#!/usr/bin/env python3
# This is the main control loop running in each argos robot

# /* Import Packages */
#######################################################################
import random, math, copy
import time, sys, os
import logging

sys.path += [os.environ['EXPERIMENTFOLDER']+'/controllers', \
             os.environ['EXPERIMENTFOLDER']+'/loop_functions', \
             os.environ['EXPERIMENTFOLDER']]

from movement import RandomWalk
from erandb import ERANDB
from rgbleds import RGBLEDs
from console import init_web3, Transaction
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
global startFlag
startFlag = False

global clocks, counters, logs, txs
clocks, counters, logs, txs = dict(), dict(), dict(), dict()

clocks['peering']  = Timer(0.5)
clocks['greeting'] = Timer(3)
clocks['block'] = Timer(lp['generic']['block_period'])

####################################################################################################################################################################################
#### INIT STEP #####################################################################################################################################################################
####################################################################################################################################################################################

def init():
    global w3, me, erb, rw, rgb, fsm
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
    erb = ERANDB(robot, cp['erbDist'] , cp['erbtFreq'])

    # /* Init Random-Walk
    rw = RandomWalk(robot, cp['speed'])

    # /* Init LEDs */
    rgb = RGBLEDs(robot)

    # /* Init Finite-State-Machine */
    fsm = FiniteStateMachine(robot, start = States.START)

    # /* Initialize logmodules*/
    #######################################################################
    log_folder = os.environ['EXPERIMENTFOLDER'] + '/logs/' + me.id + '/'
    os.makedirs(os.path.dirname(log_folder), exist_ok=True) 

    # Monitor logs (recorded to file)
    name =  'monitor.log'
    logging.basicConfig(filename=log_folder+name, filemode='w+', format='[{} %(levelname)s %(name)s %(relativeCreated)d] %(message)s'.format(me.id))
    robot.log = logging.getLogger('main')
    robot.log.setLevel(loglevel)

    # Experiment data logs (recorded to file)'robot_sc.csv'
    name   = 'robot_sc.csv'
    header = ["Greets"]
    logs['robot_sc'] = Logger(log_folder+name, header, ID = me.id)

    name   = 'fsm.csv'
    header = fsm.getAllStates()
    logs['fsm'] = Logger(log_folder+name, header, rate = 10, ID = me.id)

    txs['greet'] = Transaction(w3, None)

#########################################################################################################################
#### CONTROL STEP #######################################################################################################
#########################################################################################################################

def controlstep():
    global clocks, counters, startFlag

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
        if logs['fsm'].query():
            logs['fsm'].log([round(fsm.accumTime[state], 3) if state in fsm.accumTime else 0 for state in fsm.getAllStates() ])

        # Perform the blockchain peering
        peering()

    #########################################################################################################
    #### State::START
    #########################################################################################################

    if fsm.query(States.START):
        
        if not startFlag:
            startFlag = True 
            startTime = time.time()

            robot.log.info('--//-- Starting Experiment --//--')

            for module in [w3.geth.miner, erb]:
                try:
                    module.start()
                except:
                    robot.log.critical('Error Starting Module: %s', module)
                    sys.exit()

            for log in logs.values():
                log.start()

            for clock in clocks.values():
                clock.reset()

        fsm.setState(States.WALK, message = "Walking")

    #########################################################################################################
    #### State::WALK  
    ######################################################################################################### 

    elif fsm.query(States.WALK):

        rw.step()

        if clocks['greeting'].query(reset = False):
            
            for peer in erb.peers:
                if peer.range < 0.1:
                    clocks['greeting'].reset()
                    fsm.setState(States.GREET, message = "Greeting")
    

    #########################################################################################################
    #### State::GREET  
    #########################################################################################################

    elif fsm.query(States.GREET):
        
        rw.set_wheels(-0.2,0.2)

        if clocks['greeting'].query():
            fsm.setState(States.WALK, message = "Walking")
            

        # if txs['greet'].query(3):
        #     txs['buy'].reset(None)
        #     fsm.setState(States.WALK, message = "Greet success")

        # elif txs['greet'].failed():    
        #     fsm.setState(States.WALK, message = "Greet failed")

        # elif txs['greet'].hash == None:
        #     txHash = w3.sc.functions.greet().transact()
        #     txs['buy'].reset(txHash)
        #     robot.log.info("Greeting Peer")     


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