#!/usr/bin/env python3
# This is the main control loop running in each argos robot

# /* Logging Levels for Console and File */
#######################################################################
loglevel = 30
logtofile = False 

# /* Experiment Parameters */
#######################################################################
tcpPort = 40421 
erbDist = 185
erbtFreq = 10
gsFreq = 20
rwSpeed = 500
pcID = '100'

estimateRate = 1
voteRate = 45 
bufferRate = 0.25
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
sys.path.insert(1, experimentFolder+'/controllers')
sys.path.insert(1, experimentFolder)
import time
import rpyc
import copy
import logging
from aux import Logger, Peer

# Some experiment variables
global estimate, totalWhite, totalBlack
estimate = 0
totalWhite = 0
totalBlack = 0

global peered
peered = set()

global votetimer, updatetimer, consensus
updatetimer = time.time()
votetimer = time.time()
consensus = False

#### #### #### #### #### #### #### #### #### #### #### #### #### 
#### ALL CHEAP CHEAPSI SOLUTIONS; USE TCP VIA LOCALHOST?
def identifersExtract(robotID, query = 'IP'):
    namePrefix = 'ethereum_eth.'+str(robotID)
    containersFile = open('identifiers.txt', 'r')
    for line in containersFile.readlines():
        if line.__contains__(namePrefix):
            if query == 'IP':
                return line.split()[-1]
            if query == 'ENODE':
                return line.split()[1]

def enodesExtract(robotID, query = 'IP'):
    namePrefix = str(robotID)
    enodesFile = open('enodes.txt', 'r')
    for line in enodesFile.readlines():
        if line.__contains__(namePrefix):
                temp = line.split()[-1]
                return temp[1:-1]
#### #### #### #### #### #### #### #### #### #### #### #### #### 

# Move this script to console and import it like in the robots
def init_web3():
    global ticketPrice

    # Get ID from argos
    robotID = int(robot.id.get_id()[2:])+1

    # Connect to the RPYC which hosts web3.py (port 400xx where xx is robot ID)
    conn = rpyc.connect("localhost", 4000+int(robotID))
    w3 = conn.root

    # Do stuff over RPYC
    print(w3.getBalance())
    print(w3.getKey())
    print(w3.isMining())
    
    ticketPrice = 40
    return w3

#### #### #### #### #### #### #### #### #### #### #### #### #### 

def init():
    global me, w3, rw, gs, erb, tcp, mainlogger, bufferlog, estimatelog, votelog, sclog, blocklog, synclog, extralog

    robotID = str(int(robot.id.get_id()[2:])+1)

    logFile = experimentFolder+'/logs/robot'+robotID+'.log'
    logging.basicConfig(filename=logFile, filemode='w+', format='[%(levelname)s %(name)s %(relativeCreated)d] %(message)s')

    # /* Initialize Logging Files and Console Logging*/
    #######################################################################

    # Experiment data logs (recorded to file)
    header = ['ESTIMATE','W','B','S1','S2','S3']
    estimatelog = Logger('logs/estimate.csv', header, 10, ID = robotID)
    header = ['#BUFFER', '#GETH','#ALLOWED', 'BUFFERPEERS', 'GETHPEERS','ALLOWED']
    bufferlog = Logger('logs/buffer.csv', header, 2, ID = robotID)
    header = ['VOTE']
    votelog = Logger('logs/vote.csv', header, ID = robotID)
    header = ['TELAPSED','TIMESTAMP','BLOCK', 'HASH', 'PHASH', 'DIFF', 'TDIFF', 'SIZE','TXS', 'UNC', 'PENDING', 'QUEUED']
    blocklog = Logger('logs/block.csv', header, ID = robotID)
    header = ['BLOCK', 'BALANCE', 'UBI', 'PAY','#ROBOT', 'MEAN', '#VOTES','#OKVOTES', '#MYVOTES','#MYOKVOTES', 'R?','C?']
    sclog = Logger('logs/sc.csv', header, ID = robotID)
    header = ['#BLOCKS']
    synclog = Logger('logs/sync.csv', header, ID = robotID)
    header = ['CHAINDATASIZE', '%CPU']
    extralog = Logger('logs/extra.csv', header, 5, ID = robotID)
    header = ['MINED?', 'BLOCK', 'NONCE', 'VALUE', 'STATUS', 'HASH']
    txlog = Logger('logs/tx.csv', header, ID = robotID)

    # List of logmodules --> iterate .start() to start all; remove from list to ignore
    logmodules = [bufferlog, estimatelog, votelog, sclog, blocklog, synclog, extralog]

    # Console/file logs (Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL)
    mainlogger = logging.getLogger('main')

    # List of logmodules --> specify submodule loglevel if desired
    logging.getLogger('main').setLevel(loglevel)

    # /* Initialize Sub-modules */
    #######################################################################
    # /* Init web3.py */
    mainlogger.info('Initialising Python Geth Console...')
    w3 = init_web3()

    # /* Init an instance of peer for this Pi-Puck */
    me = Peer(robotID, w3.getEnode(), w3.getKey())

    # /* Init an instance of peer for the monitor PC */
    pc = Peer(pcID)

    # # /* Init an instance of the buffer for peers  */
    # mainlogger.info('Initialising peer buffer...')
    # pb = PeerBuffer(ageLimit)

    # # /* Init TCP server, __hosting process and request function */
    # mainlogger.info('Initialising TCP server...')
    # tcp = TCP_server(me.enode, me.ip, tcpPort)

    # /* Init E-RANDB __listening process and transmit function
    mainlogger.info('Initialising RandB board...')
    erb = ERANDB(erbDist, erbtFreq)

    # /* Init Ground-Sensors, __mapping process and vote function */
    mainlogger.info('Initialising ground-sensors...')
    gs = GroundSensor(gsFreq)

    # /* Init Random-Walk, __walking process */
    mainlogger.info('Initialising random-walk...')
    rw = RandomWalk(rwSpeed)

    # # /* Init LEDs */
    # rgb = RGBLEDs()

    # List of submodules --> iterate .start() to start all
    submodules = [erb, gs, rw]
    
def controlstep():
    global  votetimer, updatetimer, consensus, startFlag

    if not startFlag:
        votelog.start()
        w3.minerStart()
        w3.transact('registerRobot')
        startFlag = True

    rw.walking()
    gs.sensing()
    erb.listening()

    Estimate()
    Buffer()

    if time.time()-votetimer > 30:
        votetimer = time.time()
        try:
            vote = int(estimate*1e7)
            ticketPriceWei = w3.toWei(ticketPrice)
            w3.transact2('sendVote', vote, {"from":me.key, "value":ticketPriceWei, "gas":gasLimit, "gasPrice":gasprice})
            votelog.log([vote])
        except ValueError:
            # mainlogger.info("Vote Failed. No Balance: %s", w3.getBalance())
            pass
        except:
            mainlogger.info("Vote Failed. Unknown") 

    if time.time()-updatetimer > 15:
        updatetimer = time.time()

        try:
            consensus = w3.call('isConverged')
            newRound = w3.call('isNewRound')
            ubi = w3.call('askForUBI')
            payout = w3.call('askForPayout')

        except Exception as e:
            pass

        else:
            if newRound:
                w3.transact1('updateMean', {"gas":gasLimit})

            if ubi:
                w3.transact1('askForUBI', {"gas":gasLimit})

            if payout:
                w3.transact1('askForPayout', {"gas":gasLimit})


    newBlocks = w3.blockFilter()
    if newBlocks:
        try:
            nrobs = w3.call('robotCount')
            mean = w3.call('getMean')*1e-7
            bn = w3.blockNumber()
            bal = w3.getBalance()
            votecount = w3.call('getVoteCount') 
            voteOkcount = w3.call('getVoteOkCount') 
            nPeers = gethPeers = len(w3.getPeers())
            mainlogger.info('%s %s %s %s %s %s %s', nrobs, mean, bn, bal, votecount, voteOkcount, nPeers)

            if robotID == 1:
                print('#Rob; Mean; #Block; Balance #Votes, #OkVotes, #Peers')
                print(nrobs, mean, bn, bal, votecount, voteOkcount, nPeers)
        except:
            pass

    if consensus:
        print('CONSENSUS IS REACHED')
        robot.epuck_leds.set_all_colors("red")

def Buffer():

    peers = erb.getNew()

    if peers: 
        robot.epuck_leds.set_all_colors("red")
    else:
        robot.epuck_leds.set_all_colors("black")

    for peer in peers:
        if peer not in peered:
            enode = enodesExtract(peer, query = 'ENODE')
            w3.addPeer(enode)
            peered.add(peer)
            mainlogger.info('Added peer: %s', peer)

    temp = copy.copy(peered)
    for peer in temp:
        if peer not in peers:
            enode = enodesExtract(peer, query = 'ENODE')
            w3.removePeer(enode)
            peered.remove(peer)
            mainlogger.info('Removed peer: %s', peer)

def Estimate():
    """ Control routine to update the local estimate of the robot """
    global estimate, totalWhite, totalBlack
    # Set counters for grid colors
    newValues = gs.getNew()
    # print([newValue for newValue in newValues])

    for value in newValues:
        if value != 0:
            totalWhite += 1
        else:
            totalBlack += 1
    if isbyz:
        estimate = 0
    else:
        estimate = (0.5+totalWhite)/(totalWhite+totalBlack+1)

def reset():
    robot.logprint("reset")

def destroy():
	robot.logprint("destroy")


class GroundSensor(object):
    """ Set up a ground-sensor data acquisition loop on a background thread
    The __sensing() method will be started and it will run in the background
    until the application exits.
    """
    def __init__(self, freq = 20):
        """ Constructor
        :type freq: str
        :param freq: frequency of measurements in Hz (tip: 20Hz)
        """
        self.freq = freq
        self.groundValues = [0 for x in range(3)]
        self.groundCumsum = [0 for x in range(3)]
        self.count = 0


    def sensing(self):
        """ This method runs in the background until program is closed 
        """  

        # Initialize variables
        self.groundValues = robot.epuck_ground.get_readings()

        # Compute cumulative sum
        self.groundCumsum[0] += self.groundValues[0] 
        self.groundCumsum[1] += self.groundValues[1]
        self.groundCumsum[2] += self.groundValues[2]
        self.count += 1


    def getAvg(self):
        """ This method returns the average ground value since last call """

        # Compute average
        try:
            groundAverage =  [round(x/self.count) for x in self.groundCumsum]
        except:
            groundAverage = None

        self.count = 0
        self.groundCumsum = [0 for x in range(3)]
        return groundAverage

    def getNew(self):
        """ This method returns the instant ground value """

        return self.groundValues;


class ERANDB(object):
    """ Set up erandb transmitter on a background thread
    The __listen() method will be started and it will run in the background
    until the application exits.
    """
    def __init__(self, dist = 200, tFreq = 0):
        """ Constructor
        :type dist: int
        :param dist: E-randb communication range (0=1meter; 255=0m)
        :type freq: int
        :param freq: E-randb transmit frequency (tip: 0 = no transmission; 4 = 4 per second)
        """

         # This robot ID
        self.id = str(int(robot.id.get_id()[2:])+1)
        self.newIds = set()
        self.setData(self.id)

    def listening(self):
        """ This method runs in the background until program is closed """

        # /* Get a new peer ID */
        for reading in robot.epuck_range_and_bearing.get_readings():
            newId=reading[0]

            if newId != self.id: 
                self.newIds.add(newId)

    def setData(self, tData = None):
        if tData:
            self.tData = int(tData)
        robot.epuck_range_and_bearing.set_data([self.tData,0,0,0])

    def getNew(self):

        temp = self.newIds
        self.newIds = set()
        return temp


class RandomWalk(object):
    """ Set up a Random-Walk loop on a background thread
    The __walking() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self, MAX_SPEED):
        """ Constructor
        :type range: int
        :param enode: Random-Walk speed (tip: 500)
        """
        self.MAX_SPEED = MAX_SPEED/50                          
        self.__stop = 1
        self.__walk = True
     
        # Random walk parameters
        self.remaining_walk_time = 3
        self.my_lambda = 10 # Parameter for straight movement
        self.turn = 4
        self.possible_directions = ["straight", "cw", "ccw"]
        self.actual_direction = "straight"

        # Obstacle Avoidance parameters
        self.weights_left  = 50*[-10, -10, -5, 0, 0, 5, 10, 10]
        self.weights_right = 50*[-1 * x for x in self.weights_left]

    def walking(self):
        """ This method runs in the background until program is closed """
        # robot.epuck_leds.set_all_colors("black")
        
        # Random Walk
        if (self.remaining_walk_time == 0):
            if self.actual_direction == "straight":
                self.actual_direction = random.choice(self.possible_directions)
                self.remaining_walk_time = math.floor(random.uniform(0, 1) * self.turn)
            else:
                self.remaining_walk_time = math.ceil(random.expovariate(1/(self.my_lambda * 4)))
                self.actual_direction = "straight"
        else:
            self.remaining_walk_time -= 1

        # Find Wheel Speed for Random-Walk
        if (self.actual_direction == "straight"):
            left = right = self.MAX_SPEED/2
        elif (self.actual_direction == "cw"):
            left  = self.MAX_SPEED/2
            right = -self.MAX_SPEED/2
        elif (self.actual_direction == "ccw"):
            left  = -self.MAX_SPEED/2
            right = self.MAX_SPEED/2

        # Obstacle avoidance
        readings = robot.epuck_proximity.get_readings()
        self.ir = [reading.value for reading in readings]
                
        # Find Wheel Speed for Obstacle Avoidance
        for i, reading in enumerate(self.ir):
            if(reading > 0.2 ):
                left  = self.MAX_SPEED/2 + self.weights_left[i] * reading
                right = self.MAX_SPEED/2 + self.weights_right[i] * reading
                # robot.epuck_leds.set_all_colors("red")                

        # Saturate Speeds greater than MAX_SPEED
        if left > self.MAX_SPEED:
            left = self.MAX_SPEED
        elif left < -self.MAX_SPEED:
            left = -self.MAX_SPEED

        if right > self.MAX_SPEED:
            right = self.MAX_SPEED
        elif right < -self.MAX_SPEED:
            right = -self.MAX_SPEED

        if self.__walk:
            # Set wheel speeds
            robot.epuck_wheels.set_speed(right, left)
        else:
            # Set wheel speeds
            robot.epuck_wheels.set_speed(0, 0)
        

    def setWalk(self, state):
        """ This method is called set the random-walk to on without disabling I2C"""
        self.__walk = state

    def setLEDs(self, state):
        """ This method is called set the outer LEDs to an 8-bit state """
        if self.__LEDState != state:
            self.__isLEDset = False
            self.__LEDState = state
        
    def getIr(self):
        """ This method returns the IR readings """
        return self.ir
        

    def setWalk(self, state):
        """ This method is called set the random-walk to on without disabling I2C"""
        self.__walk = state

    def setLEDs(self, state):
        """ This method is called set the outer LEDs to an 8-bit state """
        if self.__LEDState != state:
            self.__isLEDset = False
            self.__LEDState = state
        
    def getIr(self):
        """ This method returns the IR readings """
        return self.ir




# robot.epuck_range_and_bearing.set_data([1,0,0,0])
# robot.epuck_leds.set_all_colors("red")

# def process_rab():
#     global number_robot_sensed 
#     number_robot_sensed = 0
#     for reading_i in robot.epuck_range_and_bearing.get_readings():
#         if reading_i.data[1] == 1:
#             number_robot_sensed += 1
