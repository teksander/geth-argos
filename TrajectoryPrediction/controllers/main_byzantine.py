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

from movement import RandomWalk
from erandb import ERANDB
from rgbleds import RGBLEDs ## maybe byebye
from console import init_web3, Transaction
from aux import *
from statemachine import * ## maybe byebye

from loop_params import params as lp
from control_params import params as cp

# /* Logging Levels for Console and File */
#######################################################################
loglevel = 10
logtofile = False 

# /* Global Variables */
#######################################################################
recorded_data = None
global startFlag
startFlag = False


global clocks, counters, logs, txs
clocks, counters, logs, txs = dict(), dict(), dict(), dict()

clocks['peering']  = Timer(0.5)
clocks['greeting'] = Timer(3)
clocks['block'] = Timer(lp['generic']['block_period'])


def compute_position(rRange, rBearing, orientation, position):
    # print(f"here is my range={rRange}, orientation={orientation}, bearing={rBearing}")
    angle = rBearing + orientation
    rdiam = 0.07 # units are in meters
    x = (rRange+rdiam)*math.cos(angle) + position[0] # xf = r*cos(alpha) + x0
    y = (rRange+rdiam)*math.sin(angle) + position[1] # yf = r*sin(alpha) + y0
    return [x, y]

####################################################################################################################################################################################
#### INIT STEP #####################################################################################################################################################################
####################################################################################################################################################################################

def init():
    global w3, me, erb, rw, rgb, fsm, recorded_data, robotID, clock, count, file_number
    robotID = str(int(robot.variables.get_id()[2:])+1)
    robotIP = identifiersExtract(robotID, 'IP')
    robot.variables.set_attribute("id", str(robotID))

    # /* Initialize submodules */
    #######################################################################
    # # /* Init web3.py */
    w3 = init_web3(robotIP)

    # /* Init an instance of peer for this Pi-Puck */
    me = Peer(robotID, robotIP, w3.enode, w3.key)

    # /* Init E-RANDB
    erb = ERANDB(robot, cp['erbDist'], cp['erbtFreq'])

    # /* Init Random-Walk
    rw = RandomWalk(robot, cp['scout_speed'])

    # /* Init LEDs */
    rgb = RGBLEDs(robot)

    # /* Init Finite-State-Machine */
    fsm = FiniteStateMachine(robot, start = States.START)


    # /* Initialize logmodules*/
    #######################################################################
    log_folder = f'{experimentFolder}/logs/{robotID}/'
    os.makedirs(os.path.dirname(log_folder), exist_ok=True) 

    # Monitor logs (recorded to file)
    name =  'monitor.log'
    logging.basicConfig(
        filename=log_folder + name,
        filemode='w+',
        format=f'[{me.id} %(levelname)s %(name)s %(relativeCreated)d] %(message)s',
    )
    robot.log = logging.getLogger('main')
    robot.log.setLevel(loglevel)

    robot.log.info("robot initialised")

    clock, count = 1, 1

    """
    maybe to update to fit this experiment.
    currently useless.
    """
    # Experiment data logs (recorded to file)'robot_sc.csv'
    name   = 'robot_sc.csv'
    header = ["Greets"]
    logs['robot_sc'] = Logger(log_folder+name, header, ID = me.id, extra=True)

    name   = 'fsm.csv'
    header = fsm.getAllStates()
    logs['fsm'] = Logger(log_folder+name, header, rate = 10, ID = me.id, extra=True)

    txs['greet'] = Transaction(w3, None)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((me.ip, 9890))
        s.send("bad".encode())

    print("bad robot id :", robotID)

#########################################################################################################################
#### CONTROL STEP #######################################################################################################
#########################################################################################################################

def controlstep():
    global clocks, counters, startFlag, robotID, clock, count, file_number

    ###########################
    ######## ROUTINES #########
    ###########################

    def peering():
        if clocks['peering'].query(): 

            peer_IPs = dict()
            for peer in erb.peers:
                peer_IPs[peer.id] = identifiersExtract(peer.id, 'IP_DOCKER')

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

    if startFlag:

        # Perform submodules step
        for module in [erb]:
            module.step()

        # Perform file logging step
        # if logs['fsm'].query():
        #     logs['fsm'].log([round(fsm.accumTime[state], 3) if state in fsm.accumTime else 0 for state in fsm.getAllStates() ])

        # Perform the blockchain peering
        peering()

    #########################################################################################################
    #### State::START
    #########################################################################################################

    if fsm.query(States.START):

        if not startFlag:
            startFlag = True 
            # startTime = time.time()

            robot.log.info('--//-- Starting Experiment --//--')

            for module in [w3.geth.miner, erb]:
                try:
                    module.start()
                except:
                    robot.log.critical('Error Starting Module: %s', module)
                    sys.exit()

            for log in logs.values():
                log.start()

            for c in clocks.values():
                c.reset()

        fsm.setState(States.WALK, message = "Walking")


    #########################################################################################################
    #### State::MOVE   
    #########################################################################################################

    rw.step()    

    clock += 1
        



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

    print('Killed robot '+ me.id)

#########################################################################################################################
#########################################################################################################################
#########################################################################################################################

def getEnodes():
    return [peer['enode'] for peer in w3.geth.admin.peers()]