#!/usr/bin/env python3
# This is the main control loop running in each argos robot

# /* Import Packages */
#######################################################################
import random, math, copy
import time, sys, os
import os
import logging
from types import SimpleNamespace
from collections import namedtuple

experimentFolder = os.environ["EXPERIMENTFOLDER"]
sys.path.insert(1, experimentFolder+'/controllers')
sys.path.insert(1, experimentFolder+'/loop_functions')
sys.path.insert(1, experimentFolder)

from movement import RandomWalk, Navigate, NoisyOdometry
from groundsensor import GroundSensor
from erandb import ERANDB
from rgbleds import RGBLEDs
from console import *
from aux import *
from statemachine import *

from loop_function_params import *
from controller_params import *


# /* Logging Levels for Console and File */
#######################################################################
loglevel = 10
logtofile = False

DECIMAL_FACTOR = 1e5
# /* Experiment Parameters */
#######################################################################
erbDist = 175
erbtFreq = 10
gsFreq = 20
rwSpeed = controller_params['scout_speed']
navSpeed = controller_params['recruit_speed']

pos_radius = market_params['radius']
dropoff_radius = market_params['radius_dropoff']

# /* Global Variables */
#######################################################################
global startFlag
startFlag = False

global txList
txList = []

global submodules
submodules = []

global clocks, counters, logs, txs
clocks = dict()
counters = dict()
logs = dict()
txs = dict()

global gasLimit, gasprice, gas
gasLimit = 0x9000000
gasprice = 0x000000
gas = 0x00000

clocks['buffer'] = Timer(0.5)
clocks['query_sc'] = Timer(1)
clocks['block'] = Timer(2)
clocks['explore'] = Timer(1)
clocks['report'] = Timer(controller_params['buy_duration'])
clocks['gs'] = Timer(0.02)
txList = []
residual_list= []
counters['velocity_test'] = 0
my_speed = 0
previous_pos = [0,0]

class Transaction(object):

    def __init__(self, txHash, name="", query_latency=2):
        self.name = name
        self.tx = None
        self.hash = txHash
        self.receipt = None
        self.fail = False
        self.block = w3.eth.blockNumber()
        self.last = 0
        self.timer = Timer(query_latency)

        if self.hash:
            self.getTransaction()
        txList.append(self)

    def query(self, min_confirmations=0):
        confirmations = 0

        if not self.hash:
            return False

        if self.timer.query():
            self.getTransaction()
            self.getTransactionReceipt()
            self.block = w3.eth.blockNumber()

        if not self.tx:
            robot.log.warning('Failed: not found')
            self.fail = True
            return False

        elif not self.receipt:
            return False

        elif not self.receipt['status']:
            robot.log.warning('Failed: Status 0')
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

    def getTransactionReceipt(self):
        try:
            self.receipt = w3.eth.getTransactionReceipt(self.hash)
        except Exception as e:
            self.receipt = None

    def getTransaction(self):
        try:
            self.tx = w3.eth.getTransaction(self.hash)
        except Exception as e:
            self.tx = None

def init():
    global clocks, counters, logs, me, imusensor, rw, nav, odo, rb, w3, fsm, gs, erb, tcp, tcpr, rgb, estimatelogger, bufferlogger, submodules, my_speed, previous_pos
    robotID = ''.join(c for c in robot.variables.get_id() if c.isdigit())
    robotIP = identifersExtract(robotID, 'IP')

    robot.variables.set_attribute("id", str(robotID))
    robot.variables.set_attribute("state", "")

    # /* Initialize Logging Files and Console Logging*/
    #######################################################################
    log_folder = experimentFolder + '/logs/' + robotID + '/'

    # Monitor logs (recorded to file)
    monitor_file = log_folder + 'monitor.log'
    os.makedirs(os.path.dirname(monitor_file), exist_ok=True)
    logging.basicConfig(filename=monitor_file, filemode='w+',
                        format='[{} %(levelname)s %(name)s %(relativeCreated)d] %(message)s'.format(robotID))
    robot.log = logging.getLogger('main')
    robot.log.setLevel(10)

    # Experiment data logs (recorded to file)
    header = ['POS']
    filename = 'noisy_odometry.csv'
    logs['noisy_odometry'] = Logger(log_folder + filename, header, 10, ID=robotID)

    # /* Initialize Sub-modules */
    #######################################################################
    # # /* Init web3.py */
    robot.log.info('Initialising Python Geth Console...')
    w3 = init_web3(robotID)

    # /* Init an instance of peer for this Pi-Puck */
    me = Peer(robotID, robotIP, w3.enode, w3.key)

    # /* Init E-RANDB __listening process and transmit function
    robot.log.info('Initialising RandB board...')
    erb = ERANDB(robot, erbDist, erbtFreq)

    robot.log.info('Initialising navigation...')
    nav = Navigate(robot, navSpeed, withKF = True)

    # /* Init Random-Walk, __walking process */
    robot.log.info('Initialising random-walk...')
    rw = RandomWalk(robot, rwSpeed)

    # /* Init Navigation, __navigate process */
    robot.log.info('Initialising odometry...')
    odo = NoisyOdometry(robot, 0.0005*int(robotID))

    # /* Init Ground-Sensors, __mapping process and vote function */
    robot.log.info('Initialising ground-sensors...')
    gs = GroundSensor(robot, gsFreq)

    # /* Init LEDs */
    rgb = RGBLEDs(robot)

    # /* Init Finite-State-Machine */
    fsm = FiniteStateMachine(robot, start=Idle.IDLE)

    # List of submodules --> iterate .start() to start all
    submodules = [w3.geth.miner, gs, erb]

    txs['report'] = Transaction(None)

    previous_pos = robot.position.get_position()[0:2]
    robot.epuck_wheels.set_speed(navSpeed / 2, navSpeed / 2)


def controlstep():
    global startFlag, startTime, clocks, counters, my_speed, previous_pos

    if not startFlag:
        ##########################
        #### FIRST STEP ##########
        ##########################

        startFlag = True
        startTime = time.time()

        robot.log.info('--//-- Starting Experiment --//--')
        #Starting miner and ERANDB
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
    else:
        for module in [erb, gs, odo]:
            module.step()
        ##########################
        #### LOG-MODULE STEPS ####
        ##########################

        if logs['noisy_odometry'].queryTimer():
            logs['noisy_odometry'].log([odo.getNew()])

        ###########################
        #### MAIN-MODULE STEPS ####
        ###########################
        gethPeers_count = 0
        if clocks['buffer'].query():

            peer_IPs = dict()
            peers = erb.getNew()
            for peer in peers:
                peer_IPs[peer] = identifersExtract(peer, 'IP_DOCKER')

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((me.ip, 9898))
                s.sendall(str(peer_IPs).encode())
                data = s.recv(1024)
                gethPeers_count = int(data)

            # Turn on LEDs according to geth Peers
            if gethPeers_count == 0:
                rgb.setLED(rgb.all, 3 * ['black'])
            elif gethPeers_count == 1:
                rgb.setLED(rgb.all, ['red', 'black', 'black'])
            elif gethPeers_count == 2:
                rgb.setLED(rgb.all, ['red', 'black', 'red'])
            elif gethPeers_count > 2:
                rgb.setLED(rgb.all, 3 * ['red'])

        ##############################
        #### STATE-MACHINE STEPS ####
        ##############################

        # Routines to be used in state machine steps:

        def homing():
            # Navigate to home position

            arrived = True

            if nav.get_distance_to((0, 0)) < pos_radius + 0.5 * (dropoff_radius - pos_radius):
                nav.avoid(move=True)
            else:
                nav.navigate_with_obstacle_avoidance([0,0])
                arrived = False
            return arrived

        def sensing():
            if clocks['gs'].query():
                ground_color = gs.getNew()
                return ground_color
            else:
                return -1

        def getDirectionVector(left,right):
            fv=1
            ori= robot.position.get_orientation()
            return [fv* math.cos(ori), fv*math.sin(ori)]
        #########################################################################################################
        #### Idle.IDLE
        #########################################################################################################
        if fsm.query(Idle.IDLE):
            # State transition: Scout.EXPLORE
            explore_duration = random.gauss(controller_params['explore_mu'], controller_params['explore_sg'])
            clocks['explore'].set(explore_duration)
            #speed test, drive straight for 10 steps
            if counters['velocity_test']<10:
                curpos = robot.position.get_position()[0:2]
                my_speed += math.dist(curpos, previous_pos)*0.1
                previous_pos=curpos
                print(counters['velocity_test'], 'my speed: ', my_speed)
                counters['velocity_test']+=1
                nav.kf.setState(curpos)
                nav.kf.setSpeed(my_speed)
            else:
                #Update KF's initial state and cmd->state transition matrix
                fsm.setState(Scout.Query, message="Duration: %.2f" % explore_duration)
                print('mtxb: ', nav.kf.B)
                print("current balance:")
                print(w3.exposed_balance)
        elif fsm.query(Scout.Query):
            # Query smart contract
            if clocks['query_sc'].query():
                source_list = w3.sc.functions.getSourceList().call()
                for cluster in source_list:
                    if cluster[3] == 0: #exists cluster needs verification
                        fsm.setState(Verify.DriveTo, message="Go to unverified source")
            rw.step()

            #estimate position
            directVec = getDirectionVector(navSpeed / 2, navSpeed / 2)
            nav.kf.predict(directVec)
            odo.step()
            noisy_pos = odo.getNew()
            nav.kf.update(noisy_pos)
            pos_state = nav.kf.x
            #modulo of the residual as the uncertainty measure
            if len(residual_list)>10:
                residual_list.pop(0)
            residual_list.append(nav.kf.get_residual_modulo())
            myUncertainty = sum(residual_list) / len(residual_list)
            #If encountered food source:
            if txs['report'].query(3):
                txs['report'] = Transaction(None)
                fsm.setState(Verify.Homing, message="Report success")
            elif txs['report'].fail == True:
                txs['report'] = Transaction(None)
            elif robot.variables.get_attribute("at")=='source' and txs['report'].hash == None:
                ticketPrice = 1
                transactHash = w3.sc.functions.reportNewPt(int(pos_state[0][0]*DECIMAL_FACTOR), int(pos_state[1][0]*DECIMAL_FACTOR), 1, w3.toWei(ticketPrice, 'ether'), myUncertainty).transact(
                    {'from': me.key, 'value': w3.toWei(ticketPrice, 'ether'), 'gas': gasLimit, 'gasPrice': gasprice})
                txs['report'] = Transaction(transactHash)
                print("current balance:")
                print(w3.exposed_balance)
                fsm.setState(Verify.Homing, message="Homing")
        elif fsm.query(Verify.Homing):
            arrived = homing()
            if arrived:
                fsm.setState(Scout.Query, message="Homing")






def reset():
    pass

def destroy():
    if startFlag:
        w3.geth.miner.stop()
        # for enode in getEnodes():
        #     w3.geth.admin.removePeer(enode)

    variables_file = experimentFolder + '/logs/' + me.id + '/variables.txt'
    with open(variables_file, 'w+') as vf:
        vf.write(repr(fsm.getTimers()))

    print('Killed robot '+ me.id)