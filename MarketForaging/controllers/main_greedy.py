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

from movement import RandomWalk, Navigate, Odometry
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
global startFlag, geth_peer_count
startFlag = False

global txList
txList = []

global submodules
submodules = []

global clocks, counters, logs, txs
clocks, counters, logs, txs = dict(), dict(), dict(), dict()

clocks['buffer'] = Timer(0.5)
clocks['query_resources'] = Timer(1)
clocks['block'] = Timer(2)
clocks['explore'] = Timer(1)
clocks['buy'] = Timer(cp['buy_duration'])
clocks['rs'] = Timer(0.02)

# Store the position of the market and cache
market   = Resource({"x":lp['market']['x'], "y":lp['market']['y'], "radius": lp['market']['radius']})
cache    = Resource({"x":lp['cache']['x'], "y":lp['cache']['y'], "radius": lp['cache']['radius']})

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
        return [res.utility for res in self.buffer]

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
    global clocks,counters, logs, submodules, me, rw, nav, odo, rb, w3, fsm, rs, erb, tcp, rgb
    robotID = str(int(robot.variables.get_id()[2:])+1)
    robotIP = identifersExtract(robotID, 'IP')
    robot.variables.set_attribute("id", str(robotID))
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
    name =  'monitor.log'
    os.makedirs(os.path.dirname(log_folder+name), exist_ok=True) 
    logging.basicConfig(filename=log_folder+name, filemode='w+', format='[{} %(levelname)s %(name)s %(relativeCreated)d] %(message)s'.format(robotID))
    robot.log = logging.getLogger('main')
    robot.log.setLevel(loglevel)

    # Experiment data logs (recorded to file)
    name   =  'odometry.csv'
    header = ['DIST']
    logs['odometry'] = Logger(log_folder+name, header, 10, ID = robotID)

    name   = 'resource.csv'
    header = ['COUNT']
    logs['resources'] = Logger(log_folder+name, header, 5, ID = robotID)


    # /* Initialize Sub-modules */
    #######################################################################
    # # /* Init web3.py */
    robot.log.info('Initialising Python Geth Console...')
    w3 = init_web3(robotID)

    print(robotIP)
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
    rs = ResourceVirtualSensor(robot)

    # /* Init Random-Walk, __walking process */
    robot.log.info('Initialising random-walk...')
    rw = RandomWalk(robot, cp['scout_speed'])

    # /* Init Navigation, __navigate process */
    robot.log.info('Initialising navigation...')
    nav = Navigate(robot, cp['recruit_speed'])

    # /* Init Navigation, __navigate process */
    robot.log.info('Initialising odometry...')
    odo = Odometry(robot)

    # /* Init LEDs */
    rgb = RGBLEDs(robot)

    # /* Init Finite-State-Machine */
    fsm = FiniteStateMachine(robot, start = Idle.IDLE)

    # List of submodules --> iterate .start() to start all
    submodules = [w3.geth.miner, erb]

    txs['sell'] = Transaction(None)
    txs['buy']  = Transaction(None)

#########################################################################################################################
#### CONTROL STEP #######################################################################################################
#########################################################################################################################

def controlstep():
    global clocks, counters, startFlag, startTime

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

    else:

        ###########################
        ######## ROUTINES ########
        ###########################

        def peering():
            global geth_peer_count
            geth_peer_count = 0
            if clocks['buffer'].query(): 

                peer_IPs = dict()
                peers = erb.getNew()
                for peer in peers:
                    peer_IPs[peer] = identifersExtract(peer, 'IP_DOCKER')

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

        def homing(to_drop = False):
            # Navigate to the market

            arrived = True

            if to_drop:
                if nav.get_distance_to((0,0)) < market.radius + 0.5* (cache.radius - market.radius):
                    nav.avoid(move = True)
                else:
                    nav.navigate_with_obstacle_avoidance(market._pr)
                    arrived = False
            else:
                if nav.get_distance_to(market._pr) < 0.5*market.radius:           
                    nav.avoid(move = True)
                    
                elif nav.get_distance_to(market._pr) < market.radius and geth_peer_count > 1:
                    nav.avoid(move = True)

                else:
                    nav.navigate_with_obstacle_avoidance(market._pr)
                    arrived = False

            return arrived

        def sensing():
            # Sense environment for resources
            if clocks['rs'].query(): 
                resource = rs.getNew()
                if resource:
                    rb.addResource(resource)
                    return resource

        ##########################
        ###### MODULE STEPS ######
        ##########################

        for module in [erb, rs, odo]:
            module.step()

        if logs['resources'].query():
            logs['resources'].log([len(rb)])

        if logs['odometry'].query():
            logs['odometry'].log([odo.getNew()])

        ###########################
        ####### EVERY STEP  #######
        ###########################

        peering()

        ##############################
        ##### STATE-MACHINE STEP #####
        ##############################

        #########################################################################################################
        #### Idle.IDLE
        #########################################################################################################
        if fsm.query(Idle.IDLE):

            # State transition: Scout.EXPLORE
            explore_duration = random.gauss(cp['explore_mu'], cp['explore_sg'])
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
            if fsm.query(Recruit.HOMING, previous = True):
                homing(to_drop = True)
            else:
                homing()

            # Sell resource information  
            if rb.buffer:
                resource = rb.buffer.pop(-1)
                sellHash = w3.sc.functions.updatePatch(*resource._calldata).transact()
                txs['sell'] = Transaction(sellHash)
                robot.log.info('Selling: %s', resource._desc)

            # Transition state  
            else:
                if txs['sell'].query(3):
                    txs['sell'] = Transaction(None)
                    fsm.setState(Recruit.PLAN, message = "Sell success")

                elif txs['sell'].fail == True:    
                    txs['sell'] = Transaction(None)
                    fsm.setState(Recruit.PLAN, message = "Sell failed")

                elif txs['sell'].hash == None:
                    fsm.setState(Recruit.PLAN, message = "None to sell")


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
        #### Recruit.PLAN  
        ######################################################################################################### 

        elif fsm.query(Recruit.PLAN):

            resource = w3.sc.functions.getMyResource().call()

            if resource:
                rb.addResource(resource, update_best = True)

                if fsm.getPreviousState() == Recruit.FORAGE:
                    fsm.setState(Recruit.FORAGE, message = None)
                else:
                    fsm.setState(Recruit.FORAGE, message = 'Foraging: %s' % rb.best._desc)

            else:
                fsm.setState(Recruit.BUY, message = "Buy again")

        #########################################################################################################
        #### Recruit.FORAGE
        #########################################################################################################
        elif fsm.query(Recruit.FORAGE):

            if clocks['block'].query():
                # Update foraging resource
                fsm.setState(Recruit.PLAN, message = None)

            else:

                # Resource virtual sensor
                resource = sensing()

                # Found the resource? YES -> Collect
                if resource and resource._p == rb.best._p:
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

            # Navigate home
            arrived = homing(to_drop = True)

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

