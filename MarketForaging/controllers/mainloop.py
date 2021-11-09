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
bufferRate = 0.5 # reality is 0.25
eventRate = 1
globalPeers = 0
ageLimit = 2
peerSecurityRate = 1

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
sys.path.insert(1, experimentFolder+'/controllers')
sys.path.insert(1, experimentFolder)
import time
import rpyc
import copy
import logging
import shutil
import json 
from types import SimpleNamespace

from erandb import ERANDB
from aux import *
from randomwalk import RandomWalk
from groundsensor import GroundSensor
from rgbleds import RGBLEDs
from _thread import start_new_thread
import threading

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

global estTimer, buffTimer, eventTimer, peerSecurityTimer
estTimer = buffTimer = eventTimer = peerSecurityTimer = time.time()

global mainlogger

def explore(rate = estimateRate):
    """ Control routine to update the local estimate of the robot """
    global estimate, totalWhite, totalBlack
    # Set counters for grid colors
    newValues = gs.getNew()
    # print([newValue for newValue in newValues])  

def buffer(rate = bufferRate, ageLimit = ageLimit):
    """ Control routine for robot-to-robot dynamic peering """
    global peered

    peers = erb.getNew()
    # start_new_thread(getEnodes, ())
    # gethPeers = set()

    for peer in peers:
        if peer not in peered:
            enode = tcp.request('localhost', tcpPort+int(peer)) 
            # mainlogger.info('got enode: %s', enode)
            w3.addPeer(enode)
            # start_new_thread(w3.addPeer, (enode,))
            peered.add(peer)

            mainlogger.info('Added peer: %s, enode: %s', peer, enode)

    temp = copy.copy(peered)

    for peer in temp:

        if peer not in peers:
            enode = tcp.request('localhost', tcpPort+int(peer))
            w3.removePeer(enode)
            peered.remove(peer)
            mainlogger.info('Removed peer: %s', peer)


    # The following part is a security check:
    # it determines if there are peers in geth that are
    # not supposed to be there based on the information in the variable peered

    if time.time() - peerSecurityTimer > peerSecurityRate:

        gethPeers = getEnodes()
        nGethPeers = len(gethPeers)

        if not peered:
            for enode in gethPeers:
                w3.removePeer(enode)

         # Turn on LEDs according to geth Peers
        if nGethPeers == 0: 
            rgb.setLED(rgb.all, 3* ['black'])
        elif nGethPeers == 1:
            rgb.setLED(rgb.all, ['red', 'black', 'black'])
        elif nGethPeers == 2:
            rgb.setLED(rgb.all, ['red', 'black', 'red'])
        elif nGethPeers > 2:
            rgb.setLED(rgb.all, 3*['red'])


    if bufferlog.isReady():
        # Low frequency logging of chaindata size and cpu usage
        if me.id == '1':
            ramPercent = getRAMPercent()
            cpuPercent = getCPUPercent()
            extralog.log([ramPercent,cpuPercent])
            #bufferlog.log([nGethPeers, len(peers), len(tcp.allowed)])

def event(rate = eventRate):
    """ Control routine to perform tasks triggered by an blockchain event """
    # sc.events.your_event_name.createFilter(fromBlock=block, toBlock=block, argument_filters={"arg1": "value"}, topics=[])
    
    global voteHashes, voteHash
    myVoteCounter = 0
    myOkVoteCounter = 0
    voteHashes = []
    voteHash = None

    amRegistered = False

    def blockHandle():
        """ Tasks when a new block is added to the chain """

        # 1) Log relevant block details 
        block = w3.getBlock(blockHex)
        #txPending = str(eval(w3.getTxPoolStatus()['pending']))
        #txQueue = str(eval(w3.getTxPoolStatus()['queued']))

        blocklog.log([time.time()-block['timestamp'], 
                    block['timestamp'], 
                    block['number'], 
                    block['hash'], 
                    block['parentHash'], 
                    block['difficulty'],
                    block['totalDifficulty'], 
                    block['size'], 
                    len(block['transactions']), 
                    len(block['uncles']), 
         #           txPending, 
         #           txQueue
        ])

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
            rgb.setLED(rgb.all, [rgb.green]*3)
            rgb.freeze()
            robot.variables.set_consensus(True)

        #     rgb.freeze()
        # elif rgb.frozen:
        #     rgb.unfreeze()


# /* Initialize background daemon threads for the Main-Modules*/
#######################################################################

estimateTh = threading.Thread(target=explore, args=())
# estimateTh.daemon = True   

bufferTh = threading.Thread(target=buffer, args=())
# bufferTh.daemon = True                         

eventTh = threading.Thread(target=event, args=())
# eventTh.daemon = True                        

# Ignore mainmodules by removing from list:
mainmodules = [estimateTh, bufferTh, eventTh]


def init():
    global me, rb, w3, rw, gs, erb, tcp, rgb, mainlogger, estimatelogger, bufferlogger, eventlogger, votelogger, bufferlog, estimatelog, votelog, sclog, blocklog, synclog, extralog, simlog, submodules, logmodules 
    robotID = str(int(robot.variables.get_id()[2:])+1)
    robot.variables.set_consensus(False) 

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
    
    header = ['VOTE']
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

    header = ['FPS']
    log_filename = log_folder + 'sim.csv'  
    simlog = Logger(log_filename, header, ID = robotID)

    # List of logmodules --> iterate .start() to start all; remove from list to ignore
    logmodules = [bufferlog, estimatelog, votelog, sclog, blocklog, synclog, extralog, simlog]

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

    # /* Init an instance of the buffer for resources  */
    mainlogger.info('Initialising resource buffer...')
    rb = ResourceBuffer()

    # /* Init TCP server, __hosting process and request function */
    mainlogger.info('Initialising TCP server...')
    tcp = TCP_server(me.enode, 'localhost', tcpPort+int(me.id), unlocked = True)

    # /* Init E-RANDB __listening process and transmit function
    mainlogger.info('Initialising RandB board...')
    erb = ERANDB(robot, erbDist, erbtFreq)

    # /* Init Ground-Sensors, __mapping process and vote function */
    mainlogger.info('Initialising ground-sensors...')
    gs = GroundSensor(robot, gsFreq)

    # /* Init Random-Walk, __walking process */
    mainlogger.info('Initialising random-walk...')
    rw = RandomWalk(robot, rwSpeed)

    # /* Init LEDs */
    rgb = RGBLEDs(robot)

    # List of submodules --> iterate .start() to start all
    submodules = [w3, tcp, erb, gs, rw]

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
        self.__stop = True

    def start(self):
        """ This method is called to start calculating peer ages"""
        if self.__stop:  
            self.__stop = False

            # Initialize background daemon thread
            self.thread = threading.Thread(target=self.__aging, args=())
            self.thread.daemon = True   
            # Start the execution                         
            self.thread.start()   

    def stop(self):
        """ This method is called before a clean exit """   
        self.__stop = True
        self.thread.join()
        logger.info('Peer aging stopped') 

    def __aging(self):
        """ This method runs in the background until program is closed 
        self.age is the time elapsed since the robots meeting.
        """            
        while True:

            self.step()

            if self.__stop:
                break
            else:
                time.sleep(0.05);   

    def step(self):
        """ This method performs a single sequence of operations """          

        for peer in self.buffer:
            peer.age = time.time() - peer.tStamp

            if peer.age > self.ageLimit:
                peer.kill()

            if peer.timeout != 0:
                if (peer.timeout - (time.time() - peer.timeoutStamp)) <= 0:
                    peer.timeout = 0      


    def addResource(self, newResourceJSON):
        """ This method is called to add a new resource JSON
        """   
        new_res = json.loads(newResourceJSON, object_hook=lambda d: SimpleNamespace(**d))
        new_res.timeStamp = time.time()

        # Is in the buffer? YES -> Update information
        if (new_res.x, new_res.y)  in self.getLocations():
            res = self.getResourceByLocation((new_res.x, new_res.y))
            res.quantity = new_res.quantity
            res.timeStamp = new_res.timeStamp

            if res.quantity <= 0:
                self.buffer.remove(res)

            # if me.id =="1":
            #     print("Updated known resource")
            #     print(str(vars(res)).replace("\'", "\""))

        # Is in the buffer? NO    
        elif new_res.quantity > 0:
            self.buffer.append(new_res)
            # if me.id =="1":
            #     print("Added unknown resource")
            #     print(str(vars(new_res)).replace("\'", "\""))


    def removeResource(self, oldResource):
        """ This method is called to remove a peer Id
            newPeer is the new peer object
        """   
        self.buffer.remove(oldResource)


    def getQuantities(self):
        return [res.age for res in self.buffer]
    def getQualities(self):
        return [res.quality for res in self.buffer]
    def getTimeStamps(self):
        return [res.timeStamp for res in self.buffer]       
    def getLocations(self):
        return [(res.x, res.y) for res in self.buffer]

    def getResourceByLocation(self, location):
        return self.buffer[self.getLocations().index(location)]

    def getResourceByTimestamp(self, timeStamp):
        return self.buffer[self.getLocations().index(timeStamp)]

    def getBestResource(self):
        return self.buffer[0]

def controlstep():
    global startFlag, startTime, estTimer, buffTimer, eventTimer, stepTimer, bufferTh, eventTh, resource_set, resource_objs

    # Actions to perform on the first step    
    if not startFlag:
        startFlag = True 
        stepTimer = time.time()
        startTime = time.time()
        mainlogger.info('Starting Experiment')
        
        for module in logmodules+submodules+mainmodules:
            try:
                module.start()
            except:
                mainlogger.critical('Error Starting Module: %s', module)

    # Actions to perform at every step
    else:

        # Collect visible resource data
        new_resource = robot.variables.get_attribute("newResource")

        # Visible resource is unique? YES
        if new_resource and new_resource not in resource_set:
            resource_set.add(new_resource)
            rb.addResource(new_resource)

        # Do I have food? YES -> Go to market
        if robot.variables.get_attribute("hasResource") == "True":
            rgb.setLED(rgb.all, 3*['red'])
            rw.navigate((0,0))

        # Do I have food? NO 
        if robot.variables.get_attribute("hasResource") == "False":
            rgb.setLED(rgb.all, 3*['black'])

            # Do I know location? YES -> Navigate to best resource
            if rb.buffer:
                resource = rb.getBestResource()
                rw.navigate((resource.x, resource.y))

                if rw.hasArrived():
                    rb.removeResource(resource)
                    # print("Resource no longer availiable")


            # Do I know location? NO -> Random-walk
            else:
                rw.step()


               

        # if me.id == "1":
        #     rgb.setLED(rgb.all, 3*['red'])
        #     print(rb.buffer)

            # No

                # Do I have money and my strategy is buy?
                    # Send transaction to buy best location

                # No money or greedy
                    # Go and explore

        # Perform step on submodules
        # for module in [rw, gs, erb]:
        #     module.step()

        # # Execute main-modules
        # if time.time()-estTimer > estimateRate:
        #     Estimate()
        #     estTimer = time.time()

        # if time.time()-buffTimer > bufferRate and not bufferTh.is_alive():

        #     bufferTh = threading.Thread(target=buffer)
        #     bufferTh.start()
        #     buffTimer = time.time()

        # if time.time()-eventTimer > eventRate:
        #     if not eventTh.is_alive():
        #        eventTh = threading.Thread(target=event)
        #        eventTh.start()
        #     else:
        #         pass
        #     eventTimer = time.time()

        simlog.log([round(time.time()-stepTimer, 2)])
        stepTimer = time.time()


def reset():
    pass


def destroy():
    if startFlag:
        w3.stop()
        eventTh.join()
        bufferTh.join()
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


#### #### #### #### #### #### #### #### #### #### #### #### #### 

# Move this script to console and import it like in the robots
def init_web3():
    global ticketPrice, ticketPriceWei

    # Get ID from argos
    robotID = int(robot.variables.get_id()[2:])+1

    # Connect to the RPYC which hosts web3.py (port 4xxx where xxx is robot ID)
    dockerIP = identifersExtract(robotID, 'IP')
    
    #conn = rpyc.connect("localhost", 4000+int(robotID), config = {"allow_all_attrs" : True})
    conn = rpyc.connect(dockerIP, 4000, config = {"allow_all_attrs" : True})
    w3 = conn.root

    ticketPrice = 40
    ticketPriceWei = w3.toWei(ticketPrice)
    return w3


def identifersExtract(robotID, query = 'IP'):
    namePrefix = 'ethereum_eth.' + str(robotID) + '.'
    containersFile = open('identifiers.txt', 'r')
    for line in containersFile.readlines():
        if line.__contains__(namePrefix):
            if query == 'IP':
                return line.split()[-1]
            if query == 'ENODE':
                return line.split()[1]


# enode = enodesExtract(peer, query = 'ENODE')
def enodesExtract(robotID, query = 'ENODE'):
    namePrefix = str(robotID)
    enodesFile = open('enodes.txt', 'r')
    for line in enodesFile.readlines():
        if line.__contains__(namePrefix):
                temp = line.split()[-1]
                return temp[1:-1]