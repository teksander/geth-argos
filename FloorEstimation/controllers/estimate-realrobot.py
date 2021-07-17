#!/usr/bin/env python3
# This is the main control loop running in each argos robot
 

 
 
 
 

# /* Logging Levels for Console and File */
#######################################################################
loglevel = 10
logtofile = False 

# /* Experiment Parameters */
#######################################################################
tcpPort = 5000 
erbDist = 175
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
from aux import *

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


def init():
    global me, w3, rw, gs, erb, tcp, mainlogger, bufferlog, estimatelog, votelog, sclog, blocklog, synclog, extralog

    robotID = str(int(robot.id.get_id()[2:])+1)

    logFile = experimentFolder+'/logs/'+robotID+'/monitor.log'
    logging.basicConfig(filename=logFile, filemode='w+', format='[%(levelname)s %(name)s %(relativeCreated)d] %(message)s')

    # /* Initialize Logging Files and Console Logging*/
    #######################################################################

    # Experiment data logs (recorded to file)
    header = ['ESTIMATE','W','B','S1','S2','S3']
    estimatelog = Logger('logs/'+robotID+'/estimate.csv', header, 10, ID = robotID)
    header = ['#BUFFER', '#GETH','#ALLOWED', 'BUFFERPEERS', 'GETHPEERS','ALLOWED']
    bufferlog = Logger('logs/'+robotID+'/buffer.csv', header, 2, ID = robotID)
    header = ['VOTE']
    votelog = Logger('logs/'+robotID+'/vote.csv', header, ID = robotID)
    header = ['TELAPSED','TIMESTAMP','BLOCK', 'HASH', 'PHASH', 'DIFF', 'TDIFF', 'SIZE','TXS', 'UNC', 'PENDING', 'QUEUED']
    blocklog = Logger('logs/'+robotID+'/block.csv', header, ID = robotID)
    header = ['BLOCK', 'BALANCE', 'UBI', 'PAY','#ROBOT', 'MEAN', '#VOTES','#OKVOTES', '#MYVOTES','#MYOKVOTES', 'R?','C?']
    sclog = Logger('logs/'+robotID+'/sc.csv', header, ID = robotID)
    header = ['#BLOCKS']
    synclog = Logger('logs/'+robotID+'/sync.csv', header, ID = robotID)
    header = ['CHAINDATASIZE', '%CPU']
    extralog = Logger('logs/'+robotID+'/extra.csv', header, 5, ID = robotID)
    header = ['MINED?', 'BLOCK', 'NONCE', 'VALUE', 'STATUS', 'HASH']
    txlog = Logger('logs/'+robotID+'/tx.csv', header, ID = robotID)

    # List of logmodules --> iterate .start() to start all; remove from list to ignore
    logmodules = [bufferlog, estimatelog, votelog, sclog, blocklog, synclog, extralog]

    # Console/file logs (Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL)
    mainlogger = logging.getLogger('main')
    estimatelogger = logging.getLogger('estimate')
    bufferlogger = logging.getLogger('buffer')
    eventlogger = logging.getLogger('events')
    votelogger = logging.getLogger('voting')

    # List of logmodules --> specify submodule loglevel if desired
    logging.getLogger('main').setLevel(loglevel)
    logging.getLogger('estimate').setLevel(loglevel)
    logging.getLogger('buffer').setLevel(loglevel)
    logging.getLogger('events').setLevel(loglevel)
    logging.getLogger('voting').setLevel(loglevel)

    # /* Initialize Sub-modules */
    #######################################################################
    # /* Init web3.py */
    mainlogger.info('Initialising Python Geth Console...')
    w3 = init_web3()

    # /* Init an instance of peer for this Pi-Puck */
    me = Peer(robotID, w3.getEnode(), w3.getKey())

    # /* Init an instance of peer for the monitor PC */
    pc = Peer(pcID)

    # /* Init an instance of the buffer for peers  */
    mainlogger.info('Initialising peer buffer...')
    pb = PeerBuffer(ageLimit)

    # # /* Init TCP server, __hosting process and request function */
    mainlogger.info('Initialising TCP server...')
    tcp = TCP_server(me.enode, 'localhost', tcpPort+int(me.id), unlocked = True)

    # /* Init E-RANDB __listening process and transmit function
    mainlogger.info('Initialising RandB board...')
    erb = ERANDB(erbDist, erbtFreq)

    # /* Init Ground-Sensors, __mapping process and vote function */
    mainlogger.info('Initialising ground-sensors...')
    gs = GroundSensor(gsFreq)

    # /* Init Random-Walk, __walking process */
    mainlogger.info('Initialising random-walk...')
    rw = RandomWalk(rwSpeed)

    # /* Init LEDs */
    rgb = RGBLEDs()

    # List of submodules --> iterate .start() to start all
    submodules = [tcp, erb, gs, rw]
    
def controlstep():
    global  votetimer, updatetimer, consensus, startFlag

    if not startFlag:
        votelog.start()
        tcp.start()
        w3.minerStart()
        w3.transact('registerRobot')
        startFlag = True

    # Perform step on submodules
    rw.step()
    gs.step()
    erb.step()

    # Execute main-modules
    Estimate()
    Buffer()
    Event()


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
    estimatelog.log([round(estimate,3),totalWhite,totalBlack,newValues[0],newValues[1],newValues[2]]) 


def Buffer(rate = bufferRate, ageLimit = ageLimit):
    """ Control routine for robot-to-robot dynamic peering """

    def simplifiedBuffer():
        peers = erb.getNew()

        if peers: 
            robot.epuck_leds.set_all_colors("red")
        else:
            robot.epuck_leds.set_all_colors("black")

        for peer in peers:
            if peer not in peered:
                # enode = tcp.request('localhost', tcpPort+int(peer)) 
                # print('got enode:', enode) # Enode IP needs to be fixed
                enode = enodesExtract(peer, query = 'ENODE')
                w3.addPeer(enode)
                peered.add(peer)
                mainlogger.info('Added peer: %s', peer)

        temp = copy.copy(peered)
        for peer in temp:
            if peer not in peers:
                # enode = tcp.request('localhost', tcpPort+int(peer))
                # w3.removePeer(enode) # Enode IP needs to be fixed
                enode = enodesExtract(peer, query = 'ENODE')
                peered.remove(peer)
                mainlogger.info('Removed peer: %s', peer)

    def globalBuffer():
        tcp.unlock()
        with open('pi-pucks.txt', 'r') as peerFile:
            for newId in peerFile:
                newId = newId.strip()
                pb.addPeer(newId)

        for peer in pb.buffer: 
            if int(me.id) > int(peer.id):
                try:
                    peer.enode = tcp.request(newPeer.ip, tcp.port)
                    w3.geth.admin.addPeer(peer.enode)
                    bufferlogger.debug('Peered to %s', peer.id)
                except:
                    bufferlogger.debug('Failed to peer to %s', peer.id)

    def localBuffer():
        pb.step()
        gethEnodes = getEnodes()
        gethIds = getIds(gethEnodes)

        # Perform buffering tasks for each peer currently in buffer
        for peer in pb.buffer:
            if peer.isDead:
                tcp.unallow(peer.id)
                bufferlogger.debug('Unallowed peer %s @ age %.2f', peer.id, peer.age)

                if peer.id in gethIds:
                    if not peer.enode:
                        peer.enode = getEnodeById(peer.id, gethEnodes)
                    w3.provider.make_request("admin_removePeer",[peer.enode])
                    gethIds.remove(peer.id)
                    bufferlogger.debug('Removed peer %s @ age %.2f', peer.id, peer.age)

                else:
                    pb.removePeer(peer.id)
                    bufferlogger.debug('Killed peer %s @ age %.2f', peer.id, peer.age)

                continue

            # elif int(me.id) > int(peer.id) and peer.timeout<=0:
            elif peer.timeout<=0:
                if not peer.enode: 
                    try:
                        peer.enode = tcp.request(peer.ip, tcp.port)
                        bufferlogger.debug('Requested peer enode %s @ age %.2f', peer.id, peer.age)          
                    except:
                        peer.trials += 1
                        if peer.trials == 5: 
                            peer.setTimeout()
                            bufferlogger.warning('Timed-out peer  %s @ age %.2f', peer.id, peer.age)
                        continue
                else:
                    if peer.id not in gethIds:
                        w3.geth.admin.addPeer(peer.enode)
                        peer.setTimeout(3)  
                        bufferlogger.debug('Added peer %s @ age %.2f', peer.id, peer.age)

        # # Turn on LEDs accordingly
        # nPeers = len(gethIds)
        # if nPeers >= 2:
        #     rw.setLEDs(0b11111111)
        # elif nPeers == 1:
        #     rw.setLEDs(0b01010101)
        # elif nPeers == 0:
        #     rw.setLEDs(0b00000000)

        # for peerId in getDiff():
        #     enode = getEnodeById(peerId, gethEnodes)
        #     w3.provider.make_request("admin_removePeer",[enode])
        #     tcp.unallow(peerId)
        #     bufferlogger.warning('Removed ilegittimate peer: %s',peerId)

        # Collect new peer IDs from E-RANDB to the buffer
        erbIds = erb.getNew()
        pb.addPeer(erbIds)
        for erbId in erbIds:
            tcp.allow(erbId)    

        # if len(pb.getIds()) > 10:
        #     bufferlogger.critical('Woooaaahh too many peers. Not Killing all for safety')
        #     # for peer in pb.buffer:
        #     #   peer.kill()
                

        if bufferlog.isReady():
            # # Low frequency logging of chaindata size and cpu usage
            # chainSize = getFolderSize('/home/pi/geth-pi-pucks/geth')
            # cpuPercent= getCPUPercent()
            # extralog.log([chainSize,cpuPercent])
            bufferlog.log([len(gethIds), len(erbIds), len(tcp.allowed), ';'.join(erbIds), ';'.join(gethIds), ';'.join(tcp.allowed)])

    if globalPeers:
        globalBuffer()
    else:
        # localBuffer()
        simplifiedBuffer()

def Event(rate = eventRate):
    """ Control routine to perform tasks triggered by an event """
    # sc.events.your_event_name.createFilter(fromBlock=block, toBlock=block, argument_filters={"arg1": "value"}, topics=[])
    
    global voteHashes, voteHash
    myVoteCounter = 0
    myOkVoteCounter = 0
    voteHashes = []
    voteHash = None
    ticketPrice = 40
    amRegistered = False

    def vote():
        nonlocal myVoteCounter, myOkVoteCounter
        myVoteCounter += 1
        try:
            vote = int(estimate*1e7)
            w3.transact2('sendVote', vote, {"from":myKey, "value":ticketPriceWei, "gas":gasLimit, "gasPrice":gasprice})
            txList.append(voteHash)

            votelog.log([vote])
            myOkVoteCounter += 1
            votelogger.debug('Voted successfully: %.2f (%i/%i)', estimate, myOkVoteCounter, myVoteCounter)
            # rgb.flashGreen()

            return voteHash

        except ValueError as e:
            votelog.log(['Value Error'])
            votelogger.debug('Failed to vote: (%i/%i). Error: %s', myOkVoteCounter, myVoteCounter, e)
            # rgb.flashRed()

        except Exception as e:
            votelogger.error('Failed to vote: (Unexpected)', e)
            # rgb.flashRed()

    # def blockHandle():
    #     """ Tasks when a new block is added to the chain """

    #     # 1) Log relevant block details 
    #     block = w3.eth.getBlock(blockHex)
    #     txPending = str(eval(w3.geth.txpool.status()['pending']))
    #     txQueue = str(eval(w3.geth.txpool.status()['queued']))

    #     blocklog.log([time.time()-block.timestamp, round(block.timestamp-blocklog.tStart, 3), block.number, block.hash.hex(), block.parentHash.hex(), block.difficulty, block.totalDifficulty, block.size, len(block.transactions), len(block.uncles), txPending, txQueue])


    def scHandle():
        """ Interact with SC when new blocks are synchronized """
        global ubi, payout, newRound, balance

        # 2) Log relevant smart contract details
        blockNr = w3.blockNumber()
        balance = w3.getBalance()
        ubi = w3.call('askForUBI')
        payout = w3.call('askForPayout')
        robotCount = w3.call('robotCount')
        mean = w3.call('getMean')
        voteCount = w3.call('getVoteCount') 
        voteOkCount = w3.call('getVoteOkCount') 
        myVoteCounter = None
        myVoteOkCounter = None
        newRound = w3.call('isNewRound')
        consensus = w3.call('isConverged')

        sclog.log([blockNr, balance, ubi, payout, robotCount, mean, voteCount, voteOkCount, myVoteCounter,myVoteOkCounter, newRound, consensus])

        # rgb.flashWhite(0.2)

        if consensus == 1:
            robot.epuck_leds.set_all_colors("red")
            # rgb.setLED(rgb.all, [rgb.green]*3)
        #     rgb.freeze()
        # elif rgb.frozen:
        #     rgb.unfreeze()

    if not startFlag:
        mainlogger.info('Stopped Events')

    newBlocks = w3.blockFilter()
    if newBlocks:
        synclog.log([len(newBlocks)])
        for blockHex in newBlocks:
            blockHandle()

        if not amRegistered:
            amRegistered = sc.functions.robot(me.key).call()[0]
            if amRegistered:
                eventlogger.debug('Registered on-chain')

        if amRegistered:

            try:
                scHandle()
            except Exception as e:
                eventlogger.warning(e)
            else:
                if ubi != 0:
                    ubiHash = sc.functions.askForUBI().transact({'gas':gasLimit})
                    eventlogger.debug('Asked for UBI: %s', ubi)
                    txList.append(ubiHash)

                if payout != 0:
                    payHash = sc.functions.askForPayout().transact({'gas':gasLimit})
                    eventlogger.debug('Asked for payout: %s', payout)
                    txList.append(payHash)

                if newRound:
                    try:
                        updateHash = sc.functions.updateMean().transact({'gas':gasLimit})
                        txList.append(updateHash)
                        eventlogger.debug('Updated mean')
                    except Exception as e:
                        eventlogger.debug(str(e))

                if balance > 40.5 and voteHash == None:
                    voteHash = vote()
                    voteHashes.append(voteHash)

                if voteHash:
                    try:
                        tx = w3.eth.getTransaction(voteHash)
                        txIndex = tx['transactionIndex']
                        txBlock = tx['blockNumber']
                        txNonce = tx['nonce']
                    except:
                        votelogger.warning('Vote disappered wtf. Voting again.')
                        voteHash = None

                    try:
                        txRecpt = w3.eth.getTransactionReceipt(voteHash)
                        votelogger.debug('Vote included in block!')
                        # print(txRecpt['blockNumber'], txRecpt['transactionIndex'], txRecpt['status'], txBlock, txIndex, txNonce)
                        voteHash = None
                    except:
                        votelogger.debug('Vote not yet included on block')


def reset():
    pass


def destroy():
    print('Killed')

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
    return [peer['enode'] for peer in w3.getPeers()]

# def getEnodeById(__id, gethEnodes = None):
#     if not gethEnodes:
#         gethEnodes = getEnodes() 
#     for enode in gethEnodes:
#         if readEnode(enode, output = 'id') == __id:
#             return enode


# def getIds(__enodes = None):
#     if __enodes:
#         return [enode.split('@',2)[1].split(':',2)[0].split('.')[-1] for enode in __enodes]
#     else:
#         return [enode.split('@',2)[1].split(':',2)[0].split('.')[-1] for enode in getEnodes()]


# /* IMPORTED SUBMODULES */
#######################################################################

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


    def step(self):
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

    def step(self):
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

    def step(self):
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


class RGBLEDs(object):
    """ Request a measurement from the Ground Sensors
    GroundSensor.getNew() returns the measurement of each sensor
    """
    def __init__(self):
        """ Constructor
        """
        self.led1 = 0x00
        self.led2 = 0x01
        self.led3 = 0x02
        self.all = [0x00,0x01,0x02]
        self.red = 0x01
        self.green = 0x02
        self.blue = 0x04
        self.off = 0x00
        self.white = 0x07
        self.frozen = False

    def setLED(self, LED, RGB):
        if not self.frozen:
            pass

    def flashRed(self, delay=1):
        if not self.frozen:
            self.setLED(self.all, 3*[self.red])
            time.sleep(delay)
            self.setLED(self.all, 3*[self.off])

    def flashGreen(self, delay=1):
        if not self.frozen:
            self.setLED(self.all, 3*[self.green])
            time.sleep(delay)
            self.setLED(self.all, 3*[self.off])

    def flashBlue(self, delay=1):
        if not self.frozen:
            self.setLED(self.all, 3*[self.blue])
            time.sleep(delay)
            self.setLED(self.all, 3*[self.off])

    def flashWhite(self, delay=1):
        if not self.frozen:
            self.setLED(self.all, 3*[self.white])
            time.sleep(delay)
            self.setLED(self.all, 3*[self.off])

    def freeze(self):
        self.frozen = True

    def unfreeze(self):
        self.frozen = False

    def stop(self):
        self.unfreeze()
        self.setLED([0x00,0x01,0x02], [0x00,0x00,0x00])


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