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
from loop_helpers import is_in_circle

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

global txList, tripList
txList   = []
tripList = []

global submodules
submodules = []

global clocks, counters, logs, txs
clocks, counters, logs, txs = dict(), dict(), dict(), dict()

clocks['buffer'] = Timer(0.5)
clocks['query_resources'] = Timer(1)
clocks['block'] = Timer(2)
clocks['search'] = Timer(10)
clocks['explore'] = Timer(1)
clocks['buy'] = Timer(cp['buy_duration'])
clocks['rs'] = Timer(0.02)
clocks['forage'] = Timer(0)

# Store the position of the market and cache
market   = Resource({"x":lp['market']['x'], "y":lp['market']['y'], "radius": lp['market']['r']})
cache    = Resource({"x":lp['cache']['x'], "y":lp['cache']['y'], "radius": lp['cache']['r']})

previous_epoch_num = -1

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
                # robot.log.info("Updated resource: %s" % self.getJSON(res))

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

    # if not self.is_in_circle(new_res.x, new_res.y):
    # def is_in_circle(self,x, y):
    #     for res in self.buffer:
    #         if is_in_circle((x,y), (res.x, res.y), res.radius): 
    #             return True
    #     return False
        
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

class Trip(object):

    def __init__(self):
        self.tStart = time.time()
        self.FC     = 0
        self.Q      = 0
        self.C      = []
        self.MC     = []
        self.TC     = 0
        self.ATC    = 0
        tripList.append(self)


    def update(self, Q):
        finished = False

        if self.FC == 0:
            self.FC = time.time() - self.tStart

        if int(Q) > self.Q:
            self.Q = int(Q)
            self.C.append(time.time() - self.tStart - self.FC)

            if len(self.C) > 1:
                new_mc = self.C[-1]-self.C[-2]
                robot.log.info("Collected // MC: %.2f" % new_mc)
                self.MC.append(new_mc)
                if new_mc > lp['patches']['utility'][rb.best.quality]:
                    finished = True

            self.TC  = time.time() - self.tStart
            self.ATC = self.TC/self.Q

        return finished

    def __str__(self):
        C  = str([round(x, 2) for x in self.C]).replace(' ','')
        MC = str([round(x, 2) for x in self.MC]).replace(' ','')
        return "%s %.2f %s %s %s %.2f %.2f" % (self.tStart, self.FC, self.Q, C, MC, self.TC, self.ATC)        

####################################################################################################################################################################################
#### INIT STEP #####################################################################################################################################################################
####################################################################################################################################################################################

def init():
    global clocks,counters, logs, submodules, me, rw, nav, odo, gps, rb, w3, fsm, rs, erb, tcp_sc, rgb
    robotID = str(int(robot.variables.get_id()[2:])+1)
    robotIP = identifersExtract(robotID, 'IP')
    robot.variables.set_attribute("id", str(robotID))
    robot.variables.set_attribute("scresources", "[]")
    robot.variables.set_attribute("foraging", "")
    robot.variables.set_attribute("dropResource", "")
    robot.variables.set_attribute("hasResource", "")
    robot.variables.set_attribute("resourceCount", "0")
    robot.variables.set_attribute("state", "")
    robot.variables.set_attribute("forageTimer", "0")
    robot.variables.set_attribute("quantity", "0")
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
    w3 = init_web3(robotID)

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
    
    #/* Init SC resource TCP query */
    robot.log.info('Initialising TCP resources...')
    tcp_sc = TCP_mp('getPatches', me.ip, 9899)

    # /* Init Random-Walk, __walking process */
    robot.log.info('Initialising random-walk...')
    rw = RandomWalk(robot, cp['scout_speed'])

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
    fsm = FiniteStateMachine(robot, start = States.IDLE)

    # List of submodules --> iterate .start() to start all
    submodules = [w3.geth.miner, erb]

    # /* Initialize logmodules*/
    #######################################################################
    # Experiment data logs (recorded to file)
    name   = 'resource.csv'
    header = ['COUNT']
    logs['resources'] = Logger(log_folder+name, header, rate = 5, ID = me.id)

    name   = 'firm.csv'
    header = ['TSTART', 'FC', 'Q', 'C', 'MC', 'TC', 'ATC', 'PROFIT']
    logs['firm'] = Logger(log_folder+name, header, ID = me.id)

    name   = 'fsm.csv'
    header = stateList
    logs['fsm'] = Logger(log_folder+name, header, rate = 10, ID = me.id)

    name   =  'odometry.csv'
    header = ['DIST']
    logs['odometry'] = Logger(log_folder+name, header, rate = 10, ID = me.id)

    txs['sell'] = Transaction(None)
    txs['buy']  = Transaction(None)
    txs['drop'] = Transaction(None)

#########################################################################################################################
#### CONTROL STEP #######################################################################################################
#########################################################################################################################
global pos
pos = [0,0]
def controlstep():
    global pos, clocks, counters, startFlag, startTime

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
        res = robot.variables.get_attribute("newResource")
        print(res)
        if res:
            resource = Resource(res)
            print(resource._calldata)
            w3.sc.functions.updatePatch(*resource._calldata).transact()

        my_eff = int(float(robot.variables.get_attribute("eff"))*100)
        w3.sc.functions.register(my_eff).transact()

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

        def homing():

            # Navigate to the market
            arrived = True

            if nav.get_distance_to(market._pr) < 0.5*market.radius:           
                nav.avoid(move = True)
                
            elif nav.get_distance_to(market._pr) < market.radius and geth_peer_count > 1:
                nav.avoid(move = True)

            else:
                nav.navigate_with_obstacle_avoidance(market._pr)
                arrived = False

            return arrived

        def dropping(resource):

            direction = (resource._pv-market._pv).rotate(-25, degrees = True).normalize()
            target = direction*(market.radius+cache.radius)/2+market._pv

            # Navigate to drop location
            arrived = True

            if nav.get_distance_to(market._p) < market.radius + 0.5* (cache.radius-market.radius):
                nav.avoid(move = True)
            else:
                nav.navigate_with_obstacle_avoidance(target)
                arrived = False

            return arrived

        def grouping(resource):

            direction = (resource._pv-market._pv).rotate(25, degrees = True).normalize()
            target = direction*(market.radius+cache.radius)/2+market._pv

            # Navigate to the group location
            arrived = True
            if nav.get_distance_to(target) < 0.2*market.radius:           
                nav.avoid(move = True) 
            else:
                nav.navigate(target)
                arrived = False

            return arrived

        def sensing(global_pos = True):

            # Sense environment for resources
            if clocks['rs'].query(): 
                res = rs.getNew()

                if res:
                    if global_pos:
                        # Use resource with GPS coordinates
                        rb.addResource(res)

                    else:
                        # Add odometry error to resource coordinates
                        error = odo.getPosition() - gps.getPosition()
                        res.x += error.x
                        res.y += error.y

                        # use resource with odo coordinates
                        rb.addResource(Resource(res._json))

                    return res

        ##########################
        ###### MODULE STEPS ######
        ##########################

        for module in [erb, rs, odo]:
            module.step()

        if logs['resources'].query():
            logs['resources'].log([len(rb)])

        if logs['fsm'].query():
            logs['fsm'].log([round(fsm.accumTime[state], 3) if state in fsm.accumTime else 0 for state in stateList ])

        if me.id == '1':
            with open(lp['files']['position'], 'w+') as f:
                f.write('%s, %s \n' % (repr(gps.getPosition()), repr(odo.getPosition())))
        else:
            with open(lp['files']['position'], 'a') as f:
                f.write('%s, %s \n' % (repr(gps.getPosition()), repr(odo.getPosition())))

        ##############################
        ##### STATE-MACHINE STEP #####
        ##############################

        #########################################################################################################
        #### Any.STATE
        #########################################################################################################

        # Perform the blockchain peering step
        peering()

        # Get perfect position if at nest
        if robot.variables.get_attribute("at") == "cache":
            odo.setPosition()

        #########################################################################################################
        #### States.IDLE
        #########################################################################################################
        if fsm.query(States.IDLE):

            fsm.setState(States.PLAN, message = "Planning")

        #########################################################################################################
        #### States.PLAN  
        ######################################################################################################### 

        elif fsm.query(States.PLAN):
            global previous_epoch_num

            block     = tcp_sc.request(data = 'block')
            token     = tcp_sc.request(data = 'token')
            resource  = tcp_sc.request(data = 'getPatch')
            resources = tcp_sc.request(data = 'getPatches')
            epochs    = tcp_sc.request(data = 'getEpochs')
            robot.sc  = tcp_sc.request(data = 'getRobot')

            availiable = tcp_sc.request(data = 'getAvailiable')   
            assigned   = bool(resource and resource['json'])
            arrived    = False
            join       = False
            leave      = False
            res        = None

            # To forage or not (market decisions)
            for res in resources:
                res = Resource(res['json'])

                # Variables that can be usefull for decisions
                if len(epochs) > 0:
                    epoch_latest = epochs[-1]

                    # Decision is performed once per epoch
                    if epoch_latest['number'] > previous_epoch_num:
                        AP = res.utility*1000 - sum(epoch_latest['ATC'])/len(epoch_latest['ATC'])
                        # BP = max([res.utility*1000-x for x in epoch_latest['ATC']])
                        # WP = min([res.utility*1000-x for x in epoch_latest['ATC']])
                        # FC = nav.get_distance_to(res._p)/cp['recruit_speed']*100
                        # my_fraction_of_TS = 100*round(robot.sc['balance']/token['supply'],3)
                        # my_deviation = 100*round(robot.sc['balance']/token['supply']-1/token['robots'],3)
                        # print(AP, BP, WP)
                        
                        # Parameters
                        K = 0
                        # K = 0.4/20000

                        # Linear
                        P = K * AP
                        
                        # Sigmoid
                        
                        robot.log.info("Join/leave P: %.2f" % P)
                        if random.random() < abs(P):
                            if P > 0:
                                join = True
                            else:
                                leave = True

                        previous_epoch_num = epoch_latest['number']

                        if join:
                            break

            # If resource is assigned, FORAGE
            if assigned:
                rb.addResource(resource['json'], update_best = True)
                arrived = grouping(rb.best)

                if leave:
                    fsm.setStorage(res)
                    fsm.setState(States.LEAVE, message = "Leaving: %s" % res._desc)

                elif arrived:
                    Trip()
                    robot.variables.set_attribute("groupSize", "0")
                    fsm.setState(States.FORAGE, message = 'Foraging: %s' % (rb.best._desc))
                        
            # If not assigned but availiable, ASSIGN
            elif availiable:
                homing()
                fsm.setState(States.ASSIGN, message = "Assigning")
            elif join:
                homing()
                fsm.setStorage(res)
                fsm.setState(States.JOIN, message = "Joining: %s" % res._desc)
            else:
                homing()

        #########################################################################################################
        #### States.ASSIGN  
        #########################################################################################################

        elif fsm.query(States.ASSIGN):

            if txs['buy'].query(3):
                txs['buy'] = Transaction(None)
                fsm.setState(States.PLAN, message = "Assign success")

            elif txs['buy'].fail == True:    
                txs['buy'] = Transaction(None)
                fsm.setState(States.PLAN, message = "Assign failed")

            elif txs['buy'].hash == None:
                res = fsm.getStorage()
                txHash = w3.sc.functions.assignPatch().transact()
                txs['buy'] = Transaction(txHash)
                robot.log.info("Assigning patch")     


        #########################################################################################################
        #### States.JOIN  
        #########################################################################################################

        elif fsm.query(States.JOIN):

            if txs['buy'].query(3):
                txs['buy'] = Transaction(None)
                fsm.setState(States.PLAN, message = "Join success")

            elif txs['buy'].fail == True:    
                txs['buy'] = Transaction(None)
                fsm.setState(States.PLAN, message = "Join failed")

            elif txs['buy'].hash == None:
                res = fsm.getStorage()
                txHash = w3.sc.functions.joinPatch(*res._calldata).transact()
                txs['buy'] = Transaction(txHash)
                robot.log.info("Joining patch") 

        #########################################################################################################
        #### States.LEAVE  
        #########################################################################################################

        elif fsm.query(States.LEAVE):

            if txs['buy'].query(3):
                txs['buy'] = Transaction(None)
                fsm.setState(States.PLAN, message = "Leave success")

            elif txs['buy'].fail == True:    
                txs['buy'] = Transaction(None)
                fsm.setState(States.PLAN, message = "Leave failed")

            elif txs['buy'].hash == None:
                res = fsm.getStorage()
                txHash = w3.sc.functions.leavePatch(*res._calldata).transact()
                txs['buy'] = Transaction(txHash)
                robot.log.info("Leaving patch") 

        #########################################################################################################
        #### States.FORAGE
        #########################################################################################################
        elif fsm.query(States.FORAGE):

            #     # Update foraging resource
            # if clocks['block'].query():
            #     fsm.setState(States.PLAN, message = None)
            # else:

            # Distance to resource
            distance = nav.get_distance_to(rb.best._pr)

            # Resource virtual sensor
            resource = sensing()
            found = resource and resource._p == rb.best._p
            finished = False

            if found:
                rb.best = resource

            if found and distance < 0.9*rb.best.radius:
                robot.variables.set_attribute("foraging", "True")
                finished = tripList[-1].update(robot.variables.get_attribute("quantity"))
                nav.avoid(move = True)

            else:
                nav.navigate_with_obstacle_avoidance(rb.best._pr)

            # Short-run decision making
            if finished:
                robot.variables.set_attribute("foraging", "")
                profit = tripList[-1].Q * lp['patches']['utility'][rb.best.quality] - tripList[-1].TC

                # Log the result of the trip
                logs['firm'].log([*str(tripList[-1]).split(), profit])

                fsm.setState(States.DROP, message = "Collected %s resources // profit: %s" % (tripList[-1].Q, round(profit,2)))


            # if robot.variables.get_attribute("hasResource") and robot.variables.get_attribute("quantity")==str(cp['maxQ']):
            #     robot.variables.set_attribute("foraging", "")
            #     fsm.setState(States.DROP, message = "Collected %s resources" % (robot.variables.get_attribute("quantity")))

        #########################################################################################################
        #### States.DROP
        #########################################################################################################
        elif fsm.query(States.DROP):

            # Navigate home
            arrived = dropping(rb.best)

            if arrived:

                # Transact to drop resource
                if not txs['drop'].hash:

                    cost = round(1000*tripList[-1].TC)
                    robot.log.info('Dropping: %s // TC: %s' % (rb.best._desc, cost))
                    dropHash = w3.sc.functions.dropResource(*rb.best._calldata, tripList[-1].Q, cost).transact()
                    txs['drop'] = Transaction(dropHash)
   
                # Transition state  
                else:
                    if txs['drop'].query(3):
                        robot.variables.set_attribute("dropResource", "True")

                        if not robot.variables.get_attribute("hasResource"):
                            txs['drop'] = Transaction(None)
                            robot.variables.set_attribute("dropResource", "")   
                            fsm.setState(States.PLAN, message = "Dropped: %s" % rb.best._desc)

                    elif txs['drop'].fail == True: 
                        robot.log.info('Drop fail: %s', rb.best._desc)     
                        txs['drop'] = Transaction(None)

                    elif txs['drop'].hash == None:
                        robot.log.info('Drop lost: %s', rb.best._desc)
                        txs['drop'] = Transaction(None)

        #########################################################################################################
        #### Scout.EXPLORE
        #########################################################################################################

        # elif fsm.query(Scout.EXPLORE):

        #     if clocks['block'].query():

        #         # Confirm I am still scout
        #         fsm.setState(States.PLAN, message = None)

        #     else:

        #         # Perform a random-walk 
        #         rw.step()

        #         # Look for resources
        #         sensing()

        #         # Transition state
        #         if clocks['explore'].query(reset = False):

        #             # Sucess exploration: Sell
        #             if rb.buffer:
        #                 fsm.setState(Scout.SELL, message = "Found %s" % len(rb))

        #             # Unsucess exploration: Buy
        #             else:
        #                 clocks['buy'].reset()
        #                 fsm.setState(States.ASSIGN, message = "Found %s" % len(rb))


        #########################################################################################################
        #### Scout.SELL
        #########################################################################################################

        # elif fsm.query(Scout.SELL):

        #     # Navigate to market
        #     if fsm.query(Recruit.HOMING, previous = True):
        #         homing(to_drop = True)
        #     else:
        #         homing()

        #     # Sell resource information  
        #     if rb.buffer:
        #         resource = rb.buffer.pop(-1)
        #         print(resource._calldata)
        #         sellHash = w3.sc.functions.updatePatch(*resource._calldata).transact()
        #         txs['sell'] = Transaction(sellHash)
        #         robot.log.info('Selling: %s', resource._desc)

        #     # Transition state  
        #     else:
        #         if txs['sell'].query(3):
        #             txs['sell'] = Transaction(None)
        #             fsm.setState(States.ASSIGN, message = "Sell success")

        #         elif txs['sell'].fail == True:    
        #             txs['sell'] = Transaction(None)
        #             fsm.setState(States.ASSIGN, message = "Sell failed")

        #         elif txs['sell'].hash == None:
        #             fsm.setState(States.ASSIGN, message = "None to sell")


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

