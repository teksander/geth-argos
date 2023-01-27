#!/usr/bin/env python3
# This is the main control loop running in each argos robot

# /* Import Packages */
#######################################################################
import random, math, copy
import time, sys, os
import logging, threading
from types import SimpleNamespace
from collections import namedtuple

experimentFolder = os.environ["EXPERIMENTFOLDER"]
sys.path.insert(1, experimentFolder+'/controllers')
sys.path.insert(1, experimentFolder+'/loop_functions')
sys.path.insert(1, experimentFolder)

from movement import RandomWalk, Navigate, Odometry
from groundsensor import GroundSensor, ResourceVirtualSensor, Resource
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

# /* Experiment Parameters */
#######################################################################
tcpPort = 5000 
tcprPort = 6000 
erbDist = 175
erbtFreq = 10
gsFreq = 20
rwSpeed = controller_params['scout_speed']
navSpeed = controller_params['recruit_speed']

bufferRate = 0.5 
peerSecurityRate = 1.5
globalPeers = False
ageLimit = 2

arena_size = float(os.environ["ARENADIM"])
step_size = 1/float(os.environ["TPS"])

# /* Global Variables */
#######################################################################
global startFlag
startFlag = False

global peered, txList
peered = set()
txList = []

global submodules
submodules = []

global clocks, counters, logs, txs
clocks = dict()
counters = dict()
logs = dict()
txs = dict()

clocks['share'] = Timer(1)
clocks['buffer'] = Timer(bufferRate)
clocks['search'] = Timer(rate = 5)
clocks['collect_resources'] = Timer(1)
clocks['peer_check'] = Timer(peerSecurityRate)
clocks['balance_check'] = Timer(1.5)
clocks['query_resources'] = Timer(1)
clocks['block'] = Timer(2)
clocks['attempt'] = Timer(7)
clocks['pay_fuel'] = Timer(10)
clocks['explore'] = Timer(1)
clocks['homing'] = Timer(1)
clocks['availiable'] = Timer(7)
clocks['buy'] = Timer(controller_params['buy_duration'])
clocks['double_check_tx_exists'] = Timer(5)
clocks['wait_on_last'] = Timer(8)
clocks['rs'] = Timer(0.02)


# Store the position of the market
market_js = {"x":0, "y":0, "radius":  market_params['radius'], "radius_dropoff": market_params['radius_dropoff']}
market = Resource(market_js)

def buffer(rate = bufferRate, ageLimit = ageLimit):
    """ Control routine for robot-to-robot dynamic peering """
    global peered

    peers = erb.getNew()

    for peer in peers:
        if peer not in peered:
            enode = tcp.request('localhost', tcpPort+int(peer)) 
            # bufferlogger.info('Received enode: %s', enode)

            w3.geth.admin.addPeer(enode)
            peered.add(peer)
            # bufferlogger.info('Added peer: %s, enode: %s', peer, enode)

    temp = copy.copy(peered)

    for peer in temp:
        if peer not in peers:
            enode = tcp.request('localhost', tcpPort+int(peer))
            w3.geth.admin.removePeer(enode)
            peered.remove(peer)
            # robot.log.info('Removed peer: %s', peer)


    # Double-check stale peers
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
bufferTh = threading.Thread(target=buffer, args=())                                     


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
        self.best = None

    def getJSON(self, resource):
        return resource._json

    def getJSONs(self, idx = None):
        return {self.getJSON(res) for res in self.buffer}

    def addResource(self, new_res, update_best = False):
        """ This method is called to add a new resource
        """   
        if isinstance(new_res, str):
            new_res = Resource(new_res)

        # Is in the buffer? NO -> Add to buffer
        if (new_res.x, new_res.y) not in self.getLocations():
            res = new_res
            self.buffer.append(res)
            robot.log.info("Added: %s; Total: %s " % (res._desc, len(self)))

        # Is in the buffer? YES -> Update buffer
        else:
            res = self.getResourceByLocation((new_res.x, new_res.y))

            # if new_res.quantity < res.quantity or new_res._timeStamp > res._timeStamp:
            if new_res.quantity < res.quantity:
                res.quantity = new_res.quantity
                res._timeStamp = new_res._timeStamp
                robot.log.info("Updated resource: %s" % self.getJSON(res))

        if update_best:
            self.best = self.getResourceByLocation((new_res.x, new_res.y))

        return res

    def removeResource(self, resource):
        """ This method is called to remove a peer Id
            newPeer is the new peer object
        """   
        self.buffer.remove(resource)
        robot.log.info("Removed resource: "+self.getJSON(resource))

    def __len__(self):
        return len(self.buffer)

    def sortBy(self, by = 'value', inplace = True):

        if inplace:
            if by == 'timeStamp':
                pass
            elif by == 'value':
                self.buffer.sort(key=lambda x: x.utility, reverse=True)
        else:
            return self.buffer.sort(key=lambda x: x.utility, reverse=True)


    def getCount(self):
        return self.__len__()

    def getAttr(self, attr):
        return [getattr(res, attr) for res in self.buffer] 

    def getValues(self):
        return [res.quantity*res.utility for res in self.buffer]

    def getUtilities(self):
        return [res.utility for res in self.buffer if res.quantity > 0]

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

    def getResourceByUtility(self, utility):
        return self.buffer[self.getUtilities().index(utility)]

    # def getPCs(self):
    #     # Algorithm for best resource decision making goes here
    #     # return self.buffer[0]

    #     # dists_to_market = self.getDistances(0,0) 
    #     # return self.buffer[dists_to_market.index(min(dists_to_market))]
    #     # my_x = robot.position.get_position()[0]
    #     # my_y = robot.position.get_position()[1]

    #     # print(len(self))
    #     Qp = self.getUtilities()
    #     Qc_m = [2*distance/arena_size for distance in self.getDistances(0,0)]
    #     # Qc_r = [100*distance/arena_size * 0.3 for distance in self.getDistances(my_x,my_y)]
    #     # print(Qp, Qc_r, Qc_m) res.price - 2*
    #     Pc = [x-y for x, y in zip(Qp,Qc_m)]
    #     return Pc

    def getBestResource(self):
        utils = self.getUtilities()
        if self.buffer and utils:
            self.best = self.buffer[utils.index(max(utils))]
            return self.best 
        else: 
            return None

txList = []
class Transaction(object):

    def __init__(self, txHash, name = "", query_latency = 2):
        self.name      = name
        self.tx        = None
        self.hash      = txHash
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

####################################################################################################################################################################################
#### INIT STEP #####################################################################################################################################################################
####################################################################################################################################################################################
def init():
    global clocks, counters, logs, me, rw, nav, odo, rb, w3, fsm, rs, erb, tcp, tcpr, rgb, estimatelogger, bufferlogger, submodules
    robotID = str(int(robot.variables.get_id()[2:])+1)
    robot.variables.set_attribute("id", str(robotID))
    robot.variables.set_consensus(False) 
    robot.variables.set_attribute("newResource", "")
    robot.variables.set_attribute("scresources", "[]")
    robot.variables.set_attribute("collectResource", "")
    robot.variables.set_attribute("dropResource", "")
    robot.variables.set_attribute("hasResource", "")
    robot.variables.set_attribute("resourceCount", "0")
    robot.variables.set_attribute("state", "")

    # /* Initialize Logging Files and Console Logging*/
    #######################################################################
    log_folder = experimentFolder + '/logs/' + robotID + '/'

    # Monitor logs (recorded to file)
    monitor_file =  log_folder + 'monitor.log'
    os.makedirs(os.path.dirname(monitor_file), exist_ok=True)    
    logging.basicConfig(filename=monitor_file, filemode='w+', format='[{} %(levelname)s %(name)s %(relativeCreated)d] %(message)s'.format(robotID))
    
    # Experiment data logs (recorded to file)
    name   =  'odometry.csv'
    header = ['DIST']
    logs['odometry'] = Logger(log_folder+name, header, 10, ID = robotID)

    name   = 'resource.csv'
    header = ['COUNT']
    logs['resources'] = Logger(log_folder+name, header, 5, ID = robotID)

    name   = 'buffer.csv'
    header = ['#BUFFER', '#GETH','#ALLOWED', 'BUFFERPEERS', 'GETHPEERS','ALLOWED']
    logs['buffer'] = Logger(log_folder+name, header, 2, ID = robotID)
   
    # Console/file logs (Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL)
    robot.log = logging.getLogger('main')
    estimatelogger = logging.getLogger('estimate')
    bufferlogger = logging.getLogger('buffer')

    # List of logmodules --> specify submodule loglevel if desired
    logging.getLogger('main').setLevel(10)
    logging.getLogger('estimate').setLevel(50)
    logging.getLogger('buffer').setLevel(50)

    # /* Initialize Sub-modules */
    #######################################################################
    # # /* Init web3.py */
    robot.log.info('Initialising Python Geth Console...')
    w3 = init_web3(robotID)

    # /* Init an instance of peer for this Pi-Puck */
    me = Peer(robotID, w3.enode, w3.key)

    # /* Init an instance of the buffer for peers  */
    robot.log.info('Initialising peer buffer...')
    pb = PeerBuffer(ageLimit)

    # /* Init an instance of the buffer for resources  */
    robot.log.info('Initialising resource buffer...')
    rb = ResourceBuffer()

    # /* Init TCP server for enode requests */
    robot.log.info('Initialising TCP server...')
    tcp = TCP_server(me.enode, 'localhost', tcpPort+int(me.id), unlocked = True)

    # /* Init TCP server for resource requests */
    robot.log.info('Initialising TCP server...')
    tcpr = TCP_server("None", 'localhost', tcprPort+int(me.id), unlocked = True)

    # /* Init E-RANDB __listening process and transmit function
    robot.log.info('Initialising RandB board...')
    erb = ERANDB(robot, erbDist, erbtFreq)

    #/* Init Resource-Sensors */
    robot.log.info('Initialising resource sensor...')
    rs = ResourceVirtualSensor(robot)

    # /* Init Random-Walk, __walking process */
    robot.log.info('Initialising random-walk...')
    rw = RandomWalk(robot, rwSpeed)

    # /* Init Navigation, __navigate process */
    robot.log.info('Initialising navigation...')
    nav = Navigate(robot, navSpeed)

    # /* Init Navigation, __navigate process */
    robot.log.info('Initialising odometry...')
    odo = Odometry(robot)

    # /* Init LEDs */
    rgb = RGBLEDs(robot)

    # /* Init Finite-State-Machine */
    fsm = FiniteStateMachine(robot, start = Idle.IDLE)

    # List of submodules --> iterate .start() to start all
    submodules = [w3.geth.miner, tcp, tcpr, erb]

    txs['sell'] = Transaction(None)
    txs['buy']  = Transaction(None)


#########################################################################################################################
#### CONTROL STEP #######################################################################################################
#########################################################################################################################

def controlstep():
    global clocks, counters, startFlag, startTime, bufferTh

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

        for log in logs.values():
            log.start()

        for clock in clocks.values():
            clock.reset()

    else:

        ##########################
        #### SUB-MODULE STEPS ####
        ##########################

        for module in [erb, rs, odo]:
            module.step()

        ##########################
        #### LOG-MODULE STEPS ####
        ##########################

        # print(startTime-time.time())
        # startTime = time.time()

        if logs['resources'].isReady():
            logs['resources'].log([len(rb)])

        if logs['odometry'].isReady():
            logs['odometry'].log([odo.getNew()])

        ###########################
        #### MAIN-MODULE STEPS ####
        ###########################

        if clocks['buffer'].query(): 
            if not bufferTh.is_alive():
                bufferTh = threading.Thread(target=buffer)
                bufferTh.start()

        ##############################
        #### STATE-MACHINE STEPS ####
        ##############################

        # Routines to be used in state machine steps:

        def homing():
            # Navigate to the market

            arrived = True
            if nav.get_distance_to(market._pr) < 0.5*market.radius:           
                nav.avoid(move = True)
                
            elif nav.get_distance_to(market._pr) < market.radius and len(peered) > 1:
                nav.avoid(move = True)

            else:
                nav.navigate_with_obstacle_avoidance(market._pr)
                arrived = False

            return arrived

        def sensing():
            if clocks['rs'].query(): 
                resource = rs.getNew()
                if resource:
                    rb.addResource(resource)
                    return resource

        #########################################################################################################
        #### Idle.IDLE
        #########################################################################################################
        if fsm.query(Idle.IDLE):

            # State transition: Scout.EXPLORE
            explore_duration = random.gauss(controller_params['explore_mu'], controller_params['explore_sg'])
            clocks['explore'].set(explore_duration)
            fsm.setState(Scout.EXPLORE, message = "Duration: %.2f" % explore_duration)

        #########################################################################################################
        #### Scout.EXPLORE
        #########################################################################################################

        elif fsm.query(Scout.EXPLORE):

            # Perform a random-walk 
            rw.step()

            # Look for resources
            sensing()

            # Transition state
            if clocks['explore'].query(reset = False):

                # Sucess exploration: Sell
                if rb.buffer:
                    fsm.setState(Scout.SELL, message = "Found %s" % len(rb))

                # Unsucess exploration: Buy
                else:
                    clocks['buy'].reset()
                    fsm.setState(Recruit.BUY, message = "Found %s" % len(rb))


        #########################################################################################################
        #### Scout.SELL
        #########################################################################################################

        elif fsm.query(Scout.SELL):

            # Navigate to market
            arrived = homing()

            if arrived:
                rb.getBestResource()
                fsm.setState(Recruit.FORAGE, message = "Exploration success")

            # # Sell resource information  
            # if rb.buffer:
            #     resource = rb.buffer.pop(-1)
            #     sellHash = w3.sc.functions.addResource(*resource._calldata).transact()
            #     txs['sell'] = Transaction(sellHash)
            #     robot.log.info('Selling: %s', resource._desc)

            # # Transition state  
            # else:
            #     if txs['sell'].query(3):
            #         txs['sell'] = Transaction(None)
            #         fsm.setState(Recruit.PLAN, message = "Sell success")

            #     elif txs['sell'].fail == True:    
            #         txs['sell'] = Transaction(None)
            #         fsm.setState(Recruit.PLAN, message = "Sell failed")

            #     elif txs['sell'].hash == None:
            #         fsm.setState(Recruit.PLAN, message = "None to sell")


        #########################################################################################################
        #### Recruit.BUY  
        #########################################################################################################

        elif fsm.query(Recruit.BUY):

            # Navigate home
            homing()

            # if txs['buy'].query(3):
            #     txs['buy'] = Transaction(None)
            #     fsm.setState(Recruit.PLAN, message = "Buy success")

            # elif txs['buy'].fail == True:    
            #     txs['buy'] = Transaction(None)
            #     fsm.setState(Recruit.PLAN, message = "Buy failed")

            # elif txs['buy'].hash == None:

            #     if clocks['block'].query():

            #         resources  = w3.sc.functions.getResources().call()
            #         availiable = [res for res in resources if 0 in [eval(x) for x in res[1]]]

            #         if availiable:
            #             try:
            #                 txBuy = w3.sc.functions.buyResource().transact()
            #                 txs['buy'] = Transaction(txBuy)
            #                 robot.log.info('Bought')     

            #             except Exception as e:
            #                 fsm.setState(Recruit.PLAN, message = "Buy failed")
            #                 txs['buy'] = Transaction(None)
            #                 robot.log.warning(e.args)
                            
            if clocks['buy'].query():
                fsm.setState(Idle.IDLE, message = "Buy expired")


        #########################################################################################################
        #### Recruit.FORAGE
        #########################################################################################################
        elif fsm.query(Recruit.FORAGE):

            # Resource virtual sensor
            resource = sensing()

            # Found the resource? YES -> Collect
            if resource and resource._pos == rb.best._pos:
                robot.variables.set_attribute("collectResource", "True")
                robot.log.info('Collect: %s', resource._desc)        

            # Collected resource? NO -> Navigate to resource site
            if not robot.variables.get_attribute("hasResource"):
                nav.navigate_with_obstacle_avoidance(rb.best._pr)

                if nav.get_distance_to(rb.best._pr) < 0.1*rb.best.radius:
                    rb.best.quantity = 0
                    fsm.setState(Scout.SELL, message = 'Failed foraging trip')

            # Collected resource? YES -> Go to market
            else:
                fsm.setState(Recruit.HOMING)


        #########################################################################################################
        #### Recruit.HOMING
        #########################################################################################################
        elif fsm.query(Recruit.HOMING):

            arrived = False
            if nav.get_distance_to((0,0)) < market.radius + 0.5* (market.radius_dropoff - market.radius):
                nav.avoid(move = True)
                arrived = True

            else:
                nav.navigate_with_obstacle_avoidance(market._pr)

            if arrived:
                robot.variables.set_attribute("dropResource", "True")
                if not robot.variables.get_attribute("hasResource"):
                    robot.variables.set_attribute("dropResource", "")
                    robot.log.info('Dropped: %s', rb.best._desc)  
                    fsm.setState(Scout.SELL, message = None)

#########################################################################################################################
#### RESET-DESTROY STEPS ################################################################################################
#########################################################################################################################

def reset():
    pass

def destroy():
    if startFlag:
        w3.geth.miner.stop()
        bufferTh.join()
        for enode in getEnodes():
            w3.geth.admin.removePeer(enode)

    variables_file = experimentFolder + '/logs/' + me.id + '/variables.txt'
    with open(variables_file, 'w+') as vf:
        vf.write(repr(fsm.getTimers())) 

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


# def START(modules = submodules, logs = logmodules):
#     global startFlag, startTime
#     startTime = time.time()

#     robot.log.info('Starting Experiment')

#     for log in logs:
#         try:
#             log.start()
#         except:
#             robot.log.critical('Error Starting Log: %s', log)

#     startFlag = True 
#     for module in modules:
#         try:
#             module.start()
#         except:
#             robot.log.critical('Error Starting Module: %s', module)

# def STOP(modules = submodules, logs = logmodules):
#     robot.log.info('Stopping Experiment')
#     global startFlag

#     robot.log.info('--/-- Stopping Main-modules --/--')
#     startFlag = False

#     robot.log.info('--/-- Stopping Sub-modules --/--')
#     for submodule in modules:
#         try:
#             submodule.stop()
#         except:
#             robot.log.warning('Error stopping submodule')

#     for log in logs:
#         try:
#             log.close()
#         except:
#             robot.log.warning('Error Closing Logfile')
            
#     if isbyz:
#         pass
#         robot.log.info('This Robot was BYZANTINE')

#     txlog.start()
    
#     for txHash in txList:

#         try:
#             tx = w3.eth.getTransaction(txHash)
#         except:
#             txlog.log(['Lost'])
#         else:
#             try:
#                 txRecpt = w3.eth.getTransactionReceipt(txHash)
#                 mined = 'Yes' 
#                 txlog.log([mined, txRecpt['blockNumber'], tx['nonce'], tx['value'], txRecpt['status'], txHash.hex()])
#             except:
#                 mined = 'No' 
#                 txlog.log([mined, mined, tx['nonce'], tx['value'], 'No', txHash.hex()])

#     txlog.close()





