#!/usr/bin/env python3
# This is the main control loop running in each argos robot
 

# /* Logging Levels for Console and File */
#######################################################################
loglevel = 10
logtofile = False 

# /* Experiment Parameters */
#######################################################################
tcpPort = 5000 
tcprPort = 6000 
tcpkPort = 7000 
erbDist = 175
erbtFreq = 10
gsFreq = 20
rwSpeed = 350
pcID = '100'

estimateRate = 1
bufferRate = 0.5 # reality is 0.25
peerSecurityRate = 1.5
eventRate = 1
globalPeers = 0
ageLimit = 2


# /* Global Variables */
#######################################################################
global startFlag, isbyz
startFlag = False
isbyz = False

global gasLimit, gasprice, gas
gasLimit = 0x9000000
gasprice = 0x900000
gas = 0x90000

global txList
txList = []

# /* Import Packages */
#######################################################################
import random, math
import sys
import os
experimentFolder = os.environ["EXPERIMENTFOLDER"]
arena_size = float(os.environ["ARENADIM"])
step_size = 1/float(os.environ["FPS"])
sys.path.insert(1, experimentFolder+'/controllers')
sys.path.insert(1, experimentFolder+'/loop_functions')
sys.path.insert(1, experimentFolder)
from loop_function_params import *
import time
import copy
import logging
import shutil
import json 
from types import SimpleNamespace
from collections import namedtuple
from aenum import Enum, auto

from erandb import ERANDB
from aux import *
from console import *
from randomwalk import RandomWalk, Navigate
from groundsensor import GroundSensor, ResourceVirtualSensor
from rgbleds import RGBLEDs
from _thread import start_new_thread as thread
import threading


from loop_function_params import *

# Some experiment variables
global estimate, totalWhite, totalBlack
estimate = 0
totalWhite = 0
totalBlack = 0

global peered
peered = set()

global resource_set
resource_set  = set()
resource_objs = list()

global consensus, submodules, logmodules
submodules = []
logmodules = []
consensus = False


global clocks, estTimer, eventTimer
clocks = dict()

clocks['share'] = Timer(1)
clocks['buffer'] = Timer(bufferRate)

clocks['collect_resources'] = Timer(1)
clocks['peer_check'] = Timer(peerSecurityRate)
clocks['balance_check'] = Timer(1.5)
clocks['query_resources'] = Timer(1)
clocks['block'] = Timer(15)
clocks['pay_fuel'] = Timer(10)
clocks['explore'] = Timer(150)

estTimer =  eventTimer  = time.time()

global resource_price
resource_price = resource_params['prices']

r = market_params['radius'] * math.sqrt(random.random())
theta = 2 * math.pi * random.random()

market_xn = r * math.cos(theta)     
market_yn = r * math.sin(theta)   

# global mainlogger

def buffer(rate = bufferRate, ageLimit = ageLimit):
    """ Control routine for robot-to-robot dynamic peering """
    global peered

    peers = erb.getNew()

    for peer in peers:
        if peer not in peered:
            enode = tcp.request('localhost', tcpPort+int(peer)) 
            # mainlogger.info('got enode: %s', enode)

            w3.geth.admin.addPeer(enode)
            peered.add(peer)

            # mainlogger.info('Added peer: %s, enode: %s', peer, enode)

    temp = copy.copy(peered)

    for peer in temp:
        if peer not in peers:
            enode = tcp.request('localhost', tcpPort+int(peer))

            w3.geth.admin.removePeer(enode)

            peered.remove(peer)
            # mainlogger.info('Removed peer: %s', peer)


    # The following part is a security check:
    # it determines if there are peers in geth that are
    # not supposed to be there based on the information in the variable peered

    if clocks['peer_check'].query():
        gethPeers_enodes = getEnodes()
        gethPeers_ids = getIds(gethPeers_enodes)
        gethPeers_count = len(gethPeers_enodes)

        if not peered:
            for enode in gethPeers_enodes:
                w3.geth.admin.removePeer(enode)

        # else:
        #     for ID in peered:
        #         if ID not in gethPeers_ids:
        #             enode = getEnodeById(ID, gethPeers_enodes)
        #             print(ID)
        #             # w3.geth.admin.addPeer(enode)


         # Turn on LEDs according to geth Peers
        if gethPeers_count == 0: 
            rgb.setLED(rgb.all, 3* ['black'])
        elif gethPeers_count == 1:
            rgb.setLED(rgb.all, ['red', 'black', 'black'])
        elif gethPeers_count == 2:
            rgb.setLED(rgb.all, ['red', 'black', 'red'])
        elif gethPeers_count > 2:
            rgb.setLED(rgb.all, 3*['red'])


# /* Initialize background daemon threads for the Main-Modules*/
#######################################################################

# estimateTh = threading.Thread(target=explore, args=())
# # estimateTh.daemon = True   

bufferTh = threading.Thread(target=buffer, args=())
# # bufferTh.daemon = True                         

# eventTh = threading.Thread(target=event, args=())
# # eventTh.daemon = True                        

# Ignore mainmodules by removing from list:
mainmodules = []


global time_exploring
time_exploring = 0
exploration_period = 1
tau = 100
EXPLORE = True


class Resource(object):
    """ Establish the resource class 
    """
    def __init__(self, resource_js):

        # Default resource attrs: x, y, radius, quality, quantity
        resource_dict = json.loads(resource_js)
        for attr in resource_dict:
            setattr(self, attr, resource_dict[attr])

        # Calculate the total value of the resource
        self.value = self.quantity * resource_price[self.quality]
        self.price = 0.5 * self.value

        # Introduce the measurement error
        r = self.radius * math.sqrt(random.random())
        theta = 2 * math.pi * random.random()
        self._xr = self.x + r * math.cos(theta)
        self._yr = self.y + r * math.sin(theta)

        # Introduce the timestamp
        self._timeStamp = time.time()
        self._isSold = False

    def _json(self):
        public_vars = { k:v for k,v in vars(self).items() if not k.startswith('_')}
        return str(public_vars).replace("\'", "\"")


class ResourceBuffer(object):
    """ Establish the resource buffer class 
    """
    def __init__(self, ageLimit = 2):
        """ Constructor
        :type id__: str
        :param id__: id of the peer
        """
        # Add the known peer details
        self.buffer = []
        self.ageLimit = ageLimit

    def getJSON(self, resource):
        return resource._json()

    def getJSONs(self, idx = None):
        return {self.getJSON(res) for res in self.buffer}

    def addResource(self, new_res):
        """ This method is called to add a new resource
        """   
        if isinstance(new_res, str):
            resource = Resource(resource_js)

        # Is in the buffer? NO -> Add to buffer
        if (new_res.x, new_res.y) not in self.getLocations():
            res = new_res
            self.buffer.append(res)
            mainlogger.info("Added resource: "+self.getJSON(res))

        # Is in the buffer? YES -> Update buffer
        else:
            res = self.getResourceByLocation((new_res.x, new_res.y))

            if new_res.quantity < res.quantity or new_res._timeStamp > res._timeStamp:
                res = new_res
                # res.quantity = new_res.quantity
                # res.value = new_res.value
                # res._timeStamp = new_res._timeStamp

                # mainlogger.info("Updated resource: "+self.getJSON(res))

        if res.quantity <= 0:
                self.removeResource(res)

        return res

    def removeResource(self, resource):
        """ This method is called to remove a peer Id
            newPeer is the new peer object
        """   
        self.buffer.remove(resource)

        # mainlogger.info("Removed resource: "+str(vars(oldResource)).replace("\'", "\""))

    def __len__(self):
        return len(self.buffer)

    def sortBy(self, by = 'value', inplace = True):

        if inplace:
            if by == 'timeStamp':
                pass
            elif by == 'value':
                self.buffer.sort(key=lambda x: x.value, reverse=True)
        else:
            return self.buffer.sort(key=lambda x: x.value, reverse=True)


    def getCount(self):
        return self.__len__()

    def getAttr(self, attr):
        return [getattr(res, attr) for res in self.buffer] 

    def getValues(self):
        return [res.quantity*resource_price[res.quality] for res in self.buffer]

    def getQuantities(self):
        return [res.age for res in self.buffer]

    def getQualities(self):
        return [res.quality for res in self.buffer]

    def getTimeStamps(self):
        return [res.timeStamp for res in self.buffer]    

    def getAges(self):
        return [time.time()-res.timeStamp for res in self.buffer]    

    def getLocations(self):
        return [(res.x, res.y) for res in self.buffer]

    def getDistances(self, x, y):
        return [math.sqrt((x-res.x)**2 + (y-res.y)**2) for res in self.buffer]

    def getResourceByLocation(self, location):
        return self.buffer[self.getLocations().index(location)]

    def getResourceByTimestamp(self, timeStamp):
        return self.buffer[self.getTimeStamps().index(timeStamp)]

    def getResourceByQuality(self, quality):
        return self.buffer[self.getQualities().index(quality)]

    def getResourceByValue(self, value):
        return self.buffer[self.getValues().index(value)]

    def getBestResource(self):
        # Algorithm for best resource decision making goes here
        # return self.buffer[0]

        # dists_to_market = self.getDistances(0,0) 
        # return self.buffer[dists_to_market.index(min(dists_to_market))]
        my_x = robot.position.get_position()[0]
        my_y = robot.position.get_position()[1]

        # print(len(self))
        Qp = [resource_price[quality] for quality in self.getQualities()]
        Qc_m = [100*distance/arena_size * 0.3 for distance in self.getDistances(0,0)]
        Qc_r = [100*distance/arena_size * 0.3 for distance in self.getDistances(my_x,my_y)]
        # print(Qp, Qc_r, Qc_m)
        Pc = [x-y-z for x, y, z in zip(Qp,Qc_m,Qc_r)]
        return self.buffer[Pc.index(max(Pc))]

class Transaction(object):

    def __init__(self, txHash, tx = None, txReceipt = None):
        self.txHash = txHash
        self.tx = tx
        self.txReceipt = txReceipt

class TransactionBuffer(object):
    """ Establish the transaction buffer class 
    """

    def __init__(self):
        self.buffer = []

    def addTransaction(self, txHash):

        if txHash not in self.getHashes():

            tx = w3.eth.getTransaction(txHash)
            txReceipt = w3.eth.getTransactionReceipt(txHash)

            self.buffer.append(Transaction(txHash, tx, txReceipt))
        else:
            print("tx already in buffer")

    def getHashes(self):
        return [tx.hash for tx in self.buffer]

    def update(self):
        for tx in self.buffer:
            if not tx.txReceipt:
                tx.txReceipt = w3.eth.getTransactionReceipt(txHash)


class Idle(Enum):
    IDLE = 1
    HOMING = 2

class Scout(Enum):
    EXPLORE = 3

class Recruit(Enum):
    BUY = 4
    FORAGE = 5

class FiniteStateMachine(object):

    def __init__(self):
        self._currState = Idle.IDLE
    
    def getState(self):
        return self._currState

    def setState(self, state, message = None):
        mainlogger.info("%s -> %s", self._currState, state)
        if message:
            mainlogger.info("Note: %s", message)
        self._currState = state
    
    def query(self, state):
        return self._currState == state

def init():
    global me, nav, rb, w3, gs, rs, erb, tcp, tcpr, rgb, mainlogger, estimatelogger, bufferlogger, eventlogger, votelogger, bufferlog, estimatelog, votelog, sclog, blocklog, synclog, extralog, submodules, logmodules 
    robotID = str(int(robot.variables.get_id()[2:])+1)
    robot.variables.set_attribute("id", str(robotID))
    robot.variables.set_consensus(False) 
    robot.variables.set_attribute("newResource", "")
    robot.variables.set_attribute("collectResource", "")
    robot.variables.set_attribute("hasResource", "")
    robot.variables.set_attribute("resourceCount", "0")
    robot.variables.set_attribute("wallet", "50")

    # /* Initialize Logging Files and Console Logging*/
    #######################################################################
    log_folder = experimentFolder + '/logs/' + robotID + '/'

    # Monitor logs (recorded to file)
    monitor_file =  log_folder + 'monitor.log'
    os.makedirs(os.path.dirname(monitor_file), exist_ok=True)    
    logging.basicConfig(filename=monitor_file, filemode='w+', format='[%(levelname)s %(name)s %(relativeCreated)d] %(message)s')

    # Experiment data logs (recorded to file)

    header = ['ESTIMATE','W','B','S1','S2','S3']
    log_filename = log_folder + 'estimate.csv'
    estimatelog = Logger(log_filename, header, ID = robotID)
    
    header = ['#BUFFER', '#GETH','#ALLOWED', 'BUFFERPEERS', 'GETHPEERS','ALLOWED']
    log_filename = log_folder + 'buffer.csv'
    bufferlog = Logger(log_filename, header, 2, ID = robotID)
    
    header = ['#RESOURCES']
    log_filename = log_folder + 'vote.csv'
    votelog = Logger(log_filename, header, ID = robotID)
    
    header = ['TELAPSED','TIMESTAMP','BLOCK', 'HASH', 'PHASH', 'DIFF', 'TDIFF', 'SIZE','TXS', 'UNC', 'PENDING', 'QUEUED']
    log_filename = log_folder + 'block.csv'
    blocklog = Logger(log_filename, header, ID = robotID)
    
    header = ['BLOCK', 'BALANCE', 'UBI', 'PAY','#ROBOT', 'MEAN', '#VOTES','#OKVOTES', '#MYVOTES','#MYOKVOTES', 'R?','C?']
    log_filename = log_folder + 'sc.csv'     
    sclog = Logger(log_filename, header, ID = robotID)
    
    header = ['#BLOCKS']
    log_filename = log_folder + 'sync.csv' 
    synclog = Logger(log_filename, header, ID = robotID)
    
    header = ['%RAM', '%CPU']
    log_filename = log_folder + 'extra.csv'
    extralog = Logger(log_filename, header, 5, ID = robotID)
    
    header = ['MINED?', 'BLOCK', 'NONCE', 'VALUE', 'STATUS', 'HASH']
    log_filename = log_folder + 'tx.csv'     
    txlog = Logger(log_filename, header, ID = robotID)

    # List of logmodules --> iterate .start() to start all; remove from list to ignore
    logmodules = [bufferlog, estimatelog, votelog, sclog, blocklog, synclog, extralog]

    # Console/file logs (Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL)
    mainlogger = logging.getLogger('main')
    estimatelogger = logging.getLogger('estimate')
    bufferlogger = logging.getLogger('buffer')
    eventlogger = logging.getLogger('events')
    votelogger = logging.getLogger('voting')

    # List of logmodules --> specify submodule loglevel if desired
    logging.getLogger('main').setLevel(10)
    logging.getLogger('estimate').setLevel(50)
    logging.getLogger('buffer').setLevel(50)
    logging.getLogger('events').setLevel(10)
    logging.getLogger('voting').setLevel(10)

    # /* Initialize Sub-modules */
    #######################################################################
    # # /* Init web3.py */
    mainlogger.info('Initialising Python Geth Console...')
    w3 = init_web3(robotID)
    # w3.sc.functions.getAllowance().transact()

    # /* Init an instance of peer for this Pi-Puck */
    me = Peer(robotID, w3.enode, w3.key)

    # /* Init an instance of peer for the monitor PC */
    pc = Peer(pcID)

    # /* Init an instance of the buffer for peers  */
    mainlogger.info('Initialising peer buffer...')
    pb = PeerBuffer(ageLimit)

    # /* Init an instance of the buffer for resources  */
    mainlogger.info('Initialising resource buffer...')
    rb = ResourceBuffer()

    # /* Init TCP server for enode requests */
    mainlogger.info('Initialising TCP server...')
    tcp = TCP_server(me.enode, 'localhost', tcpPort+int(me.id), unlocked = True)

    # /* Init TCP server for key requests */
    mainlogger.info('Initialising TCP server...')
    tcpk = TCP_server(me.key, 'localhost', tcpkPort+int(me.id), unlocked = True)

    # /* Init TCP server for resource requests */
    mainlogger.info('Initialising TCP server...')
    tcpr = TCP_server("None", 'localhost', tcprPort+int(me.id), unlocked = True)

    # /* Init E-RANDB __listening process and transmit function
    mainlogger.info('Initialising RandB board...')
    erb = ERANDB(robot, erbDist, erbtFreq)

    # /* Init Ground-Sensors, __mapping process and vote function */
    mainlogger.info('Initialising ground-sensors...')
    gs = GroundSensor(robot, gsFreq)

    #/* Init Resource-Sensors */
    rs = ResourceVirtualSensor(robot)

    # /* Init Random-Walk, __walking process */
    mainlogger.info('Initialising random-walk...')
    robot.rw = RandomWalk(robot, rwSpeed)

    # /* Init Navigation, __navigate process */
    mainlogger.info('Initialising navigation...')
    nav = Navigate(robot, 350)

    # /* Init LEDs */
    rgb = RGBLEDs(robot)

    # /* Init Finite-State-Machine */
    robot.fsm = FiniteStateMachine()

    # List of submodules --> iterate .start() to start all
    submodules = [w3.geth.miner, tcp, tcpr, erb, gs]


bc_balance = 21
balance = 0
offer_decrease_rate = 0.02
offer_increase_rate = 0.05
offer_multiplier = 0.1
explore_duration = 0
explore_threshold = 15
txReceipt = None
txHash = None
fuel_cost = economy_params['fuel_cost']
txReceipt_fuel = None
txHash_fuel = None
current_resource = None

def controlstep():
    global current_resource, explore_duration, txReceipt_fuel,txHash_fuel, txReceipt, txHash, bc_balance, balance, state, startFlag, startTime, estTimer, eventTimer, shareTimer, stepTimer, bufferTh, eventTh, resource_set, resource_objs, time_exploring, EXPLORE, clocks

    # Actions to perform on the first step    
    if not startFlag:

        startFlag = True 
        stepTimer = startTime = time.time()

        mainlogger.info('--//-- Starting Experiment --//--')
        for module in logmodules+submodules+mainmodules:
            try:
                module.start()
            except:
                mainlogger.critical('Error Starting Module: %s', module)


    # Actions to perform at every step
    else:

        ##########################
        #### SUB-MODULE STEPS ####
        ##########################
        for module in [erb, rs]:
            module.step()

        ###########################
        #### MAIN-MODULE STEPS ####
        ###########################
        if clocks['buffer'].query:
            if not bufferTh.is_alive():
                bufferTh = threading.Thread(target=buffer)
                bufferTh.start()
            else:
                pass   

        ##############################
        #### STATE-SPECIFIC STEPS ####
        ##############################
        if robot.fsm.query(Idle.IDLE):
            robot.epuck_wheels.set_speed(0,0)


            if clocks['balance_check'].query():
                balance = float(w3.getBalance())
                explore_duration = (balance - explore_threshold)/fuel_cost

                if explore_duration > explore_threshold:

                    if not txHash_fuel:

                        tx = {'from': me.key, 
                             'value': w3.toWei(explore_duration * fuel_cost, 'ether')}

                        txHash_fuel = w3.sc.functions.buyFuel().transact(tx)

                    else:
                        clocks['explore'].set(explore_duration)
                        robot.fsm.setState(Scout.EXPLORE, message = 'Explore duration %s' % explore_duration)

                else:
                    robot.fsm.setState(Recruit.BUY, message = 'Too poor to explore')

        #########################################################################################################
        if robot.fsm.query(Scout.EXPLORE):
            
            # Exploration strategy. Non-homogeneous robots could have a better strategy
            robot.rw.random()

            # Collection of new resources
            resource_js = rs.getNew()
            
            if resource_js:
                resource = Resource(resource_js)
                rb.addResource(resource)

                if not resource._isSold:
                    try: 
                        w3.sc.functions.addResource(resource.json, 
                                                    int(resource.x * 100), 
                                                    int(resource.y * 100),
                                                    int(resource.radius * 100),
                                                    resource.quantity,
                                                    resource.quality,
                                                    resource.value,
                                                    resource.price,
                                                    10).transact()

                        mainlogger.info('Sold resource')
                        resource._isSold = True
                    except Exception as e:
                        pass


            if clocks['explore'].query(reset = False):
                mainlogger.info('Explore time finished')
                robot.fsm.setState(Idle.HOMING)

        #########################################################################################################
        if robot.fsm.query(Idle.HOMING):

            nav.navigate_with_obstacle_avoidance((0, 0))

            if nav.get_distance_to_target() < 0.6*market_params['radius']:
                robot.fsm.setState(Idle.IDLE, message = "Arrived at Market")

            elif nav.get_distance_to_target() < 1.2*market_params['radius'] and len(peered) > 1:
                robot.fsm.setState(Idle.IDLE, message = "Arrived at Market")

        #########################################################################################################
        if robot.fsm.query(Recruit.BUY):
            

            if clocks['query_resources'].query():

                balance = math.floor(float(w3.getBalance()))
                resources = w3.sc.functions.getResources().call()

                current_resource_js = None
                for resource in resources:
                    if resource[1] == me.key:
                        current_resource_js = resource[3]

                if resources and not current_resource_js:
                    min_price = min([x[5] for x in resources])

                    if balance >= min_price:

                        if not txHash:
                            try:
                                txHash = w3.sc.functions.buyResource().transact({'value': w3.toWei(balance-3, 'ether')})
                                mainlogger.info('Bought resource')
                            except:
                                pass
                        else:
                            try:
                                txReceipt = w3.eth.getTransactionReceipt(txHash)
                            except Exception as e:
                                mainlogger.info('TX not mined yet')
                    else:
                        mainlogger.info('Not enough funds to buy any resource:', balance)

                elif current_resource_js:
                    txReceipt = txHash = None
                    current_resource = Resource(current_resource_js)
                    robot.fsm.setState(Recruit.FORAGE, 'Became Recruit')

                
        #########################################################################################################
        if robot.fsm.query(Recruit.FORAGE):

            # Do I have item? NO -> Go to forage
            if not robot.variables.get_attribute("hasResource"):
                nav.navigate_with_obstacle_avoidance((current_resource._xr, current_resource._yr))

                if nav.get_distance_to_target() < current_resource.radius:
                    robot.variables.set_attribute("collectResource", "True")
                else:
                    robot.variables.set_attribute("collectResource", "")

                if nav.get_distance_to_target() < 0.4 * current_resource.radius:
                    
                    current_resource = None
                    # w3.sc.functions.removeResource().transact()
                    robot.fsm.setState(Idle.HOMING, 'Resource Depleted or Not Found')


            # Do I have item? YES -> Go to market
            else:
                nav.navigate_with_obstacle_avoidance((market_xn,market_yn))

                if nav.get_distance_to_target() < 0.9 * market_params['radius']:
                    w3.sc.functions.sellItem(current_resource.value).transact()


def reset():
    pass


def destroy():
    if startFlag:
        w3.geth.miner.stop()
        bufferTh.join()
        for enode in getEnodes():
            w3.geth.admin.removePeer(enode)

    print('Killed')
    # STOP()


def START(modules = submodules, logs = logmodules):
    global startFlag, startTime
    startTime = time.time()

    mainlogger.info('Starting Experiment')

    for log in logs:
        try:
            log.start()
        except:
            mainlogger.critical('Error Starting Log: %s', log)

    startFlag = True 
    for module in modules:
        try:
            module.start()
        except:
            mainlogger.critical('Error Starting Module: %s', module)

def STOP(modules = submodules, logs = logmodules):
    mainlogger.info('Stopping Experiment')
    global startFlag

    mainlogger.info('--/-- Stopping Main-modules --/--')
    startFlag = False
    time.sleep(1.5)

    mainlogger.info('--/-- Stopping Sub-modules --/--')
    for submodule in modules:
        try:
            submodule.stop()
        except:
            mainlogger.warning('Error stopping submodule')

    for log in logs:
        try:
            log.close()
        except:
            mainlogger.warning('Error Closing Logfile')
            
    if isbyz:
        pass
        mainlogger.info('This Robot was BYZANTINE')

    txlog.start()
    
    for txHash in txList:

        try:
            tx = w3.eth.getTransaction(txHash)
        except:
            txlog.log(['Lost'])
        else:
            try:
                txRecpt = w3.eth.getTransactionReceipt(txHash)
                mined = 'Yes' 
                txlog.log([mined, txRecpt['blockNumber'], tx['nonce'], tx['value'], txRecpt['status'], txHash.hex()])
            except:
                mined = 'No' 
                txlog.log([mined, mined, tx['nonce'], tx['value'], 'No', txHash.hex()])

    txlog.close()


# /* Some useful functions */
#######################################################################

# def getBalance():
#     return round(w3.fromWei(w3.eth.getBalance(me.key), 'ether'), 2)

# def getDiffEnodes(gethEnodes = None):
#     if gethEnodes:
#         return set(gethEnodes)-set(pb.getEnodes())-{me.enode}
#     else:
#         return set(getEnodes())-set(pb.getEnodes())-{me.enode}

# def getDiff(gethIds = None):
#     if gethIds:
#         return set(gethIds)-set(pb.getIds())-{me.id}
#     else:
#         return set(getIds())-set(pb.getIds())-{me.enode}

def getEnodes():
    return [peer['enode'] for peer in w3.geth.admin.peers()]
    # return [peer['enode'] for peer in w3.getPeers()]

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


#### #### #### #### #### #### #### #### #### #### #### #### #### 

# enode = enodesExtract(peer, query = 'ENODE')
def enodesExtract(robotID, query = 'ENODE'):
    namePrefix = str(robotID)
    enodesFile = open('enodes.txt', 'r')
    for line in enodesFile.readlines():
        if line.__contains__(namePrefix):
                temp = line.split()[-1]
                return temp[1:-1]

############## BACKUPS

 ##### COLLECTION OF RESOURCE INFORMATION #####
        

        # # Collect resource data from the virtual sensor
        # if clocks['collect_resources'].query():
        #     resource_js = rs.getNew()
        #     if resource_js:
        #         # mainlogger.debug('Got resources from sensor:'+resource_js) 
        #         rb.addResource(resource_js)
        
        # if clocks['share'].query():
        #     mainlogger.critical(rb.getJSONs())

        #     # Collect resource data from peers
        #     if rb.getCount() < 1:
        #         for peer_id, count, _, _ in erb.getData():
        #             resource_js = tcpr.request('localhost', tcprPort+int(peer_id))

        #             if resource_js and resource_js != 'None':
        #                 # mainlogger.debug("Got resource from peer:"+resource_js)
        #                 rb.addResource(resource_js)

        #     # Share resource data to peers

        #     if rb.getCount() > 0:
        #         if rb.buffer[0].quantity > 3:
        #             resource_js = rb.getJSON(rb.buffer[0])
        #             if tcpr.getData() != resource_js:
        #                 mainlogger.debug("Sharing Resource "+resource_js)
        #                 tcpr.setData(resource_js)


        # ###### NAVIGATION DECISION MAKING ######

        # # Do I have food? YES -> Go to market
        # if robot.variables.get_attribute("hasResource"):
        #     nav.navigate_with_obstacle_avoidance((market_xn,market_yn))


        # # Do I have food? NO 
        # else:

        #     # Should I explore more?

        #     # Do I know location? NO -> Random-walk
        #     if not rb.buffer:
        #         EXPLORE = True

        #     # Do I know location? YES -> Foraging Strategy
        #     if rb.buffer and EXPLORE:
        #         EXPLORE = False
        #         # if time_exploring > exploration_period:

        #         #     best_res = rb.getBestResource()

        #         #     Pc = resource_price[best_res.quality]*0.5 - 100*math.sqrt((-best_res.x)**2 + (-best_res.y)**2)/arena_size * 0.2 + 100*(1-math.exp(-time_exploring/tau))
        #         #     # EXPLORE = random.choices([True, False], [100-Pc, Pc])[0]
        #         #     EXPLORE = False
        #         #     # print(Pc)
        #         #     time_exploring = 0

        #     if EXPLORE:
        #         time_exploring += 0.1
        #         robot.rw.random()

        #     else:
        #         # best_res = rb.getBestResource()
        #         best_res = rb.buffer[-1]
        #         nav.navigate_with_obstacle_avoidance((best_res.xn, best_res.yn))

        #         if nav.distance_to_target() < best_res.radius:
        #             robot.variables.set_attribute("collectResource", "True")
        #         else:
        #             robot.variables.set_attribute("collectResource", "")

        #         if nav.distance_to_target() < 0.5 * best_res.radius:
        #             rb.removeResource(best_res)
        #             EXPLORE = True
