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
rwSpeed = 350
pcID = '100'

estimateRate = 1
bufferRate = 0.5 # reality is 0.25
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
from erandb import ERANDB
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

global consensus, submodules, logmodules
submodules = []
logmodules = []
consensus = False

global estTimer, buffTimer, eventTimer
estTimer = buffTimer = eventTimer = time.time()

def init():
    global me, w3, rw, gs, erb, tcp, rgb, mainlogger, bufferlog, estimatelog, votelog, sclog, blocklog, synclog, extralog, submodules, logmodules 

    robotID = str(int(robot.id.get_id()[2:])+1)

    logFile = experimentFolder+'/logs/'+robotID+'/monitor.log'
    logging.basicConfig(filename=logFile, filemode='w+', format='[%(levelname)s %(name)s %(relativeCreated)d] %(message)s')

    # /* Initialize Logging Files and Console Logging*/
    #######################################################################

    # Experiment data logs (recorded to file)
    header = ['ESTIMATE','W','B','S1','S2','S3']
    estimatelog = Logger('logs/'+robotID+'/estimate.csv', header, ID = robotID)
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
    logging.getLogger('main').setLevel(10)
    logging.getLogger('estimate').setLevel(50)
    logging.getLogger('buffer').setLevel(50)
    logging.getLogger('events').setLevel(50)
    logging.getLogger('voting').setLevel(50)

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

def controlstep():
    global startFlag, startTime, estTimer, buffTimer, eventTimer, prevTime, t1, t2

    if not startFlag:
        # START()

        t1 = None
        t2 = None
        prevTime = time.time()

        startTime = time.time()
        mainlogger.info('Starting Experiment')

        for log in logmodules:
            try:
                log.start()
            except:
                mainlogger.critical('Error Starting Log: %s', log)

        startFlag = True 
        for module in submodules:
            try:
                module.start()
            except:
                mainlogger.critical('Error Starting Module: %s', module)

    else:

        stepTimer = time.time()

        if time.time()-buffTimer > bufferRate:
            if t1 == None or t1.is_alive() == 0:
               t1 = threading.Thread(target=Buffer)
               t1.start()
            else:
                print("Buffer Thread is already running")
            buffTimer = time.time()

        # Perform step on submodules
        for module in [rw, gs, erb]:
            module.step()

        # Execute main-modules
        if time.time()-estTimer > estimateRate:
            Estimate()
            estTimer = time.time()



        # if time.time()-eventTimer > eventRate:
        #     if t2 == None or t2.is_alive() == 0:
        #        t2 = threading.Thread(target=Event)
        #        t2.start()
        #     else:
        #         print("Thread is already running")
        #     eventTimer = time.time()

        # if time.time()-eventTimer > eventRate:
        #     Event()
        #     eventTimer = time.time()

        if me.id == str(1):
            print((time.time()-prevTime))
            print(threading.active_count())
            prevTime = time.time()

def Estimate(rate = estimateRate):
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
    global peered

    def simplifiedBuffer():

        peers = erb.getNew()
        # start_new_thread(getEnodes, ())
        # gethPeers = set()
        gethPeers = getEnodes()
        nGethPeers = len(gethPeers)

        # for enode in gethPeers:
        #     mainlogger.info('Current enode: %s Total length: %s', enode, nPeers)

         # Turn on LEDs accordingly
        if nGethPeers == 0:
            rgb.setLED(rgb.all, 3* ['black'])
        elif nGethPeers == 1:
            rgb.setLED(rgb.all, ['red', 'black', 'black'])
        elif nGethPeers == 2:
            rgb.setLED(rgb.all, ['red', 'black', 'red'])
        elif nGethPeers > 2:
            rgb.setLED(rgb.all, 3*['red'])

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

                # start_new_thread(w3.removePeer, (enode,))
                w3.removePeer(enode) # Enode IP needs to be fixed
                peered.remove(peer)
                mainlogger.info('Removed peer: %s', peer)

        if not peered:
            for enode in gethPeers:
                w3.removePeer(enode)


    if globalPeers:
        pass
        # globalBuffer()
    else:
        # localBuffer()
        simplifiedBuffer()
        # forcedBuffer()

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

    def blockHandle():
        """ Tasks when a new block is added to the chain """

        # 1) Log relevant block details 
        block = w3.getBlock(blockHex)
        txPending = str(eval(w3.getTxPoolStatus()['pending']))
        txQueue = str(eval(w3.getTxPoolStatus()['queued']))

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
                    txPending, 
                    txQueue])

    
    # def scHandle():
    #     """ Interact with SC when new blocks are synchronized """
    #     global ubi, payout, newRound, balance

    #     # 2) Log relevant smart contract details
    #     blockNr = w3.blockNumber()
    #     balance = w3.getBalance()
    #     ubi = w3.call('askForUBI')
    #     payout = w3.call('askForPayout')
    #     robotCount = w3.call('robotCount')
    #     mean = w3.call('getMean')
    #     voteCount = w3.call('getVoteCount') 
    #     voteOkCount = w3.call('getVoteOkCount') 
    #     myVoteCounter = None
    #     myVoteOkCounter = None
    #     newRound = w3.call('isNewRound')
    #     consensus = w3.call('isConverged')

    #     sclog.log([blockNr, balance, ubi, payout, robotCount, mean, voteCount, voteOkCount, myVoteCounter,myVoteOkCounter, newRound, consensus])

    #     # rgb.flashWhite(0.2)

    #     if consensus == 1:
    #         rgb.setLED(rgb.all, [rgb.green]*3)
    #         rgb.freeze()
    #     #     rgb.freeze()
    #     # elif rgb.frozen:
    #     #     rgb.unfreeze()

    if not startFlag:
        mainlogger.info('Stopped Events')

    newBlocks = w3.blockFilter()
    if newBlocks:
        synclog.log([len(newBlocks)])
        for blockHex in newBlocks:
            blockHandle()

        # if not amRegistered:
        #     amRegistered = sc.functions.robot(me.key).call()[0]
        #     if amRegistered:
        #         eventlogger.debug('Registered on-chain')

        # if amRegistered:

        #     try:
        #         scHandle()
        #     except Exception as e:
        #         eventlogger.warning(e)
        #     else:
        #         if ubi != 0:
        #             ubiHash = sc.functions.askForUBI().transact({'gas':gasLimit})
        #             eventlogger.debug('Asked for UBI: %s', ubi)
        #             txList.append(ubiHash)

        #         if payout != 0:
        #             payHash = sc.functions.askForPayout().transact({'gas':gasLimit})
        #             eventlogger.debug('Asked for payout: %s', payout)
        #             txList.append(payHash)

        #         if newRound:
        #             try:
        #                 updateHash = sc.functions.updateMean().transact({'gas':gasLimit})
        #                 txList.append(updateHash)
        #                 eventlogger.debug('Updated mean')
        #             except Exception as e:
        #                 eventlogger.debug(str(e))

        #         if balance > 40.5 and voteHash == None:
        #             voteHash = vote()
        #             voteHashes.append(voteHash)

        #         if voteHash:
        #             try:
        #                 tx = w3.eth.getTransaction(voteHash)
        #                 txIndex = tx['transactionIndex']
        #                 txBlock = tx['blockNumber']
        #                 txNonce = tx['nonce']
        #             except:
        #                 votelogger.warning('Vote disappered wtf. Voting again.')
        #                 voteHash = None

        #             try:
        #                 txRecpt = w3.eth.getTransactionReceipt(voteHash)
        #                 votelogger.debug('Vote included in block!')
        #                 # print(txRecpt['blockNumber'], txRecpt['transactionIndex'], txRecpt['status'], txBlock, txIndex, txNonce)
        #                 voteHash = None
        #             except:
        #                 votelogger.debug('Vote not yet included on block')


def reset():
    pass


def destroy():
    w3.stop()
    print('Killed')
    # STOP()



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
            
    if isByz:
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
    global ticketPrice

    # Get ID from argos
    robotID = int(robot.id.get_id()[2:])+1

    # Connect to the RPYC which hosts web3.py (port 400xx where xx is robot ID)
    conn = rpyc.connect("localhost", 4000+int(robotID), config = {"allow_all_attrs" : True})
    w3 = conn.root

    # Do stuff over RPYC
    print(w3.getBalance())
    print(w3.getKey())
    print(w3.isMining())
    
    ticketPrice = 40
    return w3


# enode = enodesExtract(peer, query = 'ENODE')

def enodesExtract(robotID, query = 'ENODE'):
    namePrefix = str(robotID)
    enodesFile = open('enodes.txt', 'r')
    for line in enodesFile.readlines():
        if line.__contains__(namePrefix):
                temp = line.split()[-1]
                return temp[1:-1]

def identifersExtract(robotID, query = 'IP'):
    namePrefix = 'ethereum_eth.'+str(robotID)
    containersFile = open('identifiers.txt', 'r')
    for line in containersFile.readlines():
        if line.__contains__(namePrefix):
            if query == 'IP':
                return line.split()[-1]
            if query == 'ENODE':
                return line.split()[1]