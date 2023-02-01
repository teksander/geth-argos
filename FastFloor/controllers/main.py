#!/usr/bin/env python3
# This is the main control loop running in each argos robot

# /* Import Packages */
#######################################################################
import random, math, copy
import time, sys, os
import logging

experimentFolder = os.environ['EXPERIMENTFOLDER']
sys.path += [os.environ['EXPERIMENTFOLDER']+'/controllers', \
             os.environ['EXPERIMENTFOLDER']+'/loop_functions', \
             os.environ['EXPERIMENTFOLDER']]

from movement import RandomWalk, Navigate, Odometry, OdoCompass, GPS
from groundsensor import GroundSensor, ResourceVirtualSensor, Resource
from erandb import ERANDB
from rgbleds import RGBLEDs
from console import *
from aux import *
from statemachine import *

from loop_params import params as lp
from control_params import params as cp

# /* Logging Levels for Console and File */
#######################################################################
loglevel = 10
logtofile = False 

# /* Global Variables */
#######################################################################
global startFlag
startFlag = False

global txList, submodules
txList,  submodules = [], []

global clocks, counters, logs, txs
clocks, counters, logs, txs = dict(), dict(), dict(), dict()

clocks['peering'] = Timer(0.5)
clocks['sensing'] = Timer(1)
clocks['block'] = Timer(lp['generic']['block_period'])


global rwSpeed
rwSpeed = 250

# Some experiment variables
global estimate, totalWhite, totalBlack
estimate = 0
totalWhite = 0
totalBlack = 0


class Transaction(object):

    def __init__(self, txHash, name = "", query_latency = 2):
        self.name      = name
        self.hash      = txHash
        self.tx        = None
        self.receipt   = None

        self.fail      = False
        self.block     = w3.eth.blockNumber()
        self.last      = 0
        self.timer     = Timer(query_latency)

        if self.hash:
            self.getTransaction()
        txList.append(self)

    def query(self, min_confirmations = 0):
        confirmations = 0

        if not self.hash:
            return False

        if self.timer.query():
            self.getTransaction()
            self.getTransactionReceipt()
            self.block = w3.eth.blockNumber()

        if not self.tx:
            robot.log.warning('Fail: Not found')
            self.fail = True
            return False

        elif not self.receipt:
            return False

        elif not self.receipt['status']:
            robot.log.warning('Fail: Status 0')
            self.fail = True
            return False

        else:
            confirmations = self.block - self.receipt['blockNumber']

            if self.last < confirmations:
                self.last = confirmations
                robot.log.info('Confirming: %s/%s', confirmations, min_confirmations)
                
            if confirmations >= min_confirmations:
                self.last = 0
                return True
            else:
                return False

    def getTransaction(self):
        try:
            self.tx = w3.eth.getTransaction(self.hash)
        except Exception as e:
            self.tx = None

    def getTransactionReceipt(self):
        try:
            self.receipt = w3.eth.getTransactionReceipt(self.hash)
        except Exception as e:
            self.receipt = None



####################################################################################################################################################################################
#### INIT STEP #####################################################################################################################################################################
####################################################################################################################################################################################

def init():
    global clocks,counters, logs, submodules, me, rw, nav, odo, gps, w3, fsm, rs, erb, tcp_calls, rgb
    robotID = str(int(robot.variables.get_id()[2:])+1)
    robotIP = identifiersExtract(robotID, 'IP')
    robot.variables.set_attribute("id", str(robotID))
    robot.variables.set_attribute("scresources", "[]")
    robot.variables.set_attribute("foraging", "")
    robot.variables.set_attribute("dropResource", "")
    robot.variables.set_attribute("hasResource", "")
    robot.variables.set_attribute("resourceCount", "0")
    robot.variables.set_attribute("state", "")
    robot.variables.set_attribute("forageTimer", "0")
    robot.variables.set_attribute("quantity", "0")
    robot.variables.set_attribute("block", "")
    robot.variables.set_attribute("groupSize", "1")

    # /* Initialize Console Logging*/
    #######################################################################
    log_folder = experimentFolder + '/logs/' + robotID + '/'

    # Monitor logs (recorded to file)
    name =  'monitor.log'
    os.makedirs(os.path.dirname(log_folder+name), exist_ok=True) 
    logging.basicConfig(filename=log_folder+name, filemode='w+', format='[{} %(levelname)s %(name)s %(relativeCreated)d] %(message)s'.format(robotID))
    robot.log = logging.getLogger('main')
    robot.log.setLevel(loglevel)

    # /* Initialize submodules */
    #######################################################################
    # # /* Init web3.py */
    robot.log.info('Initialising Python Geth Console...')
    w3 = init_web3(robotIP)

    # /* Init an instance of peer for this Pi-Puck */
    me = Peer(robotID, robotIP, w3.enode, w3.key)

    # /* Init an instance of the buffer for resources  */
    robot.log.info('Initialising resource buffer...')
    rb = ResourceBuffer()

    # /* Init E-RANDB __listening process and transmit function
    robot.log.info('Initialising RandB board...')
    erb = ERANDB(robot, cp['erbDist'] , cp['erbtFreq'])

    #/* Init Resource-Sensors */
    robot.log.info('Initialising resource sensor...')
    rs = GroundSensor(robot)
    
    #/* Init SC resource TCP query */
    robot.log.info('Initialising TCP resources...')
    tcp_calls = TCP_mp('block', me.ip, 9899)

    # /* Init Random-Walk, __walking process */
    robot.log.info('Initialising random-walk...')
    rw = RandomWalk(robot, rwSpeed)

    # /* Init Navigation, __navigate process */
    robot.log.info('Initialising navigation...')
    nav = Navigate(robot, cp['recruit_speed'])

    # /* Init odometry sensor */
    robot.log.info('Initialising odometry...')
    odo = OdoCompass(robot)

    # /* Init GPS sensor */
    robot.log.info('Initialising gps...')
    gps = GPS(robot)

    # /* Init LEDs */
    rgb = RGBLEDs(robot)

    # /* Init Finite-State-Machine */
    fsm = FiniteStateMachine(robot, start = States.VOLKER)

    # List of submodules --> iterate .start() to start all
    submodules = [w3.geth.miner, erb]

    # /* Initialize logmodules*/
    #######################################################################
    # Experiment data logs (recorded to file)
    name   = 'resource.csv'
    header = ['COUNT']
    logs['resources'] = Logger(log_folder+name, header, rate = 5, ID = me.id)

    name   = 'firm.csv'
    header = ['FC', 'Q', 'C', 'MC', 'TC', 'ATC', 'PROFIT']
    logs['firm'] = Logger(log_folder+name, header, ID = me.id)

    # name   = 'epoch.csv'
    # # header = ['NUMBER', 'BSTART', 'Q', 'TC', 'ATC', 'price']
    # header =w3.sc.functions.Epoch_key().call()
    # logs['epoch'] = Logger(log_folder+name, header, ID = me.id)

    # name   = 'robot_sc.csv'
    # # header = ["isRegistered", "efficiency", "income", "balance", "task"]
    # header = w3.sc.functions.Robot_key().call()
    # logs['robot_sc'] = Logger(log_folder+name, header, ID = me.id)

    name   = 'fsm.csv'
    header = stateList
    logs['fsm'] = Logger(log_folder+name, header, rate = 10, ID = me.id)

    name   =  'odometry.csv'
    header = ['DIST']
    logs['odometry'] = Logger(log_folder+name, header, rate = 10, ID = me.id)

    txs['sell'] = Transaction(None)
    txs['buy']  = Transaction(None)
    txs['drop'] = Transaction(None)
    txs['vote'] = Transaction(None)

#########################################################################################################################
#### CONTROL STEP #######################################################################################################
#########################################################################################################################
global pos
pos = [0,0]
def controlstep():
    global pos, clocks, counters, startFlag, startTime
    global estimate, totalWhite, totalBlack
    
    if not startFlag:
        ##########################
        #### FIRST STEP ##########
        ##########################

        startFlag = True 
        startTime = time.time()

        robot.log.info('--//-- Starting Experiment --//--')

        for module in submodules:
            try:
                module.start()
            except:
                robot.log.critical('Error Starting Module: %s', module)
                sys.exit()

        for log in logs.values():
            log.start()

        for clock in clocks.values():
            clock.reset()

        # Startup transactions

        # my_eff = 100
        w3.sc.functions.registerRobot().transact()

        totalWhite = totalBlack = 0        

    else:

        ###########################
        ######## ROUTINES ########
        ###########################

        def vote():

            if txs['vote'].query():
                txs['vote'] = Transaction(None)

            elif txs['vote'].fail:
                txs['vote'] = Transaction(None)

            elif txs['vote'].hash == None:
                txHash = w3.sc.functions.sendVote(estimate).transact()
                txs['vote'] = Transaction(txHash)
                robot.log.info("Voting") 

        def send_to_docker():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((me.ip, 9898))
                s.sendall("hi from robot %s" % me.id)
                data = s.recv(1024)
                print(data)

        def peering():
            global geth_peer_count
            geth_peer_count = 0
            if clocks['peering'].query(): 

                peer_IPs = dict()
                peer_IDs = erb.getNew()
                for peer_ID in peer_IDs:
                    peer_IPs[peer_ID] = identifiersExtract(peer_ID, 'IP_DOCKER')

                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((me.ip, 9898))
                    s.sendall(str(peer_IPs).encode())
                    data = s.recv(1024)
                    geth_peer_count = int(data)

                 # Turn on LEDs according to geth Peers
                if geth_peer_count == 0: 
                    rgb.setLED(rgb.all, 3* ['black'])
                elif geth_peer_count == 1:
                    rgb.setLED(rgb.all, ['red', 'black', 'black'])
                elif geth_peer_count == 2:
                    rgb.setLED(rgb.all, ['red', 'black', 'red'])
                elif geth_peer_count > 2:
                    rgb.setLED(rgb.all, 3*['red'])



        ##############################
        ##### STATE-MACHINE STEP #####
        ##############################

        #########################################################################################################
        #### State::EVERY
        #########################################################################################################
        
        # Perform submodules step
        for module in [erb, rs, rw]:
            module.step()

        # Sense environment for resources
        if clocks['sensing'].query(): 
            newValues = rs.getNew()

            print([newValue for newValue in newValues])
    
            for value in newValues:
                if value != 0:
                    totalWhite += 1
                else:
                    totalBlack += 1
            estimate = (0.5+totalWhite)/(totalWhite+totalBlack+1)

        
        # print(totalWhite, totalBlack, estimate)

        ticket_price = tcp_calls.request(data = 'getTicketPrice')
        ubi = tcp_calls.request(data = 'askForUBI')
        payout = tcp_calls.request(data = 'askForPayout')
        # balance = tcp_calls.request(data = 'balance')

        print(ticket_price, ubi, payout)

        # TODO!
        if balance > ticket_price:
            vote()

        # Perform the blockchain peering step
        peering()
            
        

#########################################################################################################################
#### RESET-DESTROY STEPS ################################################################################################
#########################################################################################################################

def reset():
    pass

def destroy():
    if startFlag:
        w3.geth.miner.stop()
        for enode in getEnodes():
            w3.geth.admin.removePeer(enode)

    # variables_file = experimentFolder + '/logs/' + me.id + '/variables.txt'
    # with open(variables_file, 'w+') as vf:
    #     vf.write(repr(fsm.getTimers())) 

    # epochs = tcp_sc.request(data = 'getEpochs')
    # for epoch in epochs:
    #     logs['epoch'].log([str(x).replace(" ","") for x in epoch.values()])

    # robot.sc  = tcp_sc.request(data = 'getRobot')
    # logs['robot_sc'].log(list(robot.sc.values()))

    print('Killed robot '+ me.id)

#########################################################################################################################
#########################################################################################################################
#########################################################################################################################


def getEnodes():
    return [peer['enode'] for peer in w3.geth.admin.peers()]

def getEnodeById(__id, gethEnodes = None):
    if not gethEnodes:
        gethEnodes = getEnodes() 

    for enode in gethEnodes:
        if readEnode(enode, output = 'id') == __id:
            return enode

def getIds(__enodes = None):
    if __enodes:
        return [enode.split('@',2)[1].split(':',2)[0].split('.')[-1] for enode in __enodes]
    else:
        return [enode.split('@',2)[1].split(':',2)[0].split('.')[-1] for enode in getEnodes()]
