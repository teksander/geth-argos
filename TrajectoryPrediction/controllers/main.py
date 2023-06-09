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
from data_structure import Trajectory, RecordedData
from statemachine import * ## maybe byebye

from loop_params import params as lp
from control_params import params as cp

"""
To reduce the number of waypoints stored in memory,
consider two robot positions distinct if they are
at least MIN_DISTANCE away from each other
This constant is expressed in meters
"""
MIN_DISTANCE = 0.05
"Convenience constant to avoid calculating the square root in PostStep()"
MIN_DISTANCE_SQUARED = MIN_DISTANCE ** 2
"Length of the sequences (in number of time steps)"
SEQ_LENGTH = 100
fileswap = 50 # in seconds

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
    rdiam = 0.075 # units are in meters
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


    # data recording files. the files where the robots store the data of the trajectory recording of each robot.
    header = ['robotID', 'neighborID', 'time', 'x', 'y']
    file_number = 1
    file_name = f'traj{file_number}.csv'
    logs['traj'] = Logger(log_folder+file_name, header, ID = me.id)
    # /* Init Data Recording Structure */
    recorded_data = RecordedData(erb, logs['traj'])

    # creating the epired data file.
    # file_name = 'expired.csv'
    # logs['expired'] = Logger(log_folder+file_name, header, ID = me.id)


    # each robots training history, contains the epoch, loss, val loss, and time to train.
    # header = ['epoch','loss','val_loss','time']
    # file_name = 'train_history.csv'
    # logs['train'] = Logger(log_folder+file_name, header, ID = me.id)

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
        s.send("good".encode())



#########################################################################################################################
#### CONTROL STEP #######################################################################################################
#########################################################################################################################

def controlstep():
    global clocks, counters, startFlag, robotID, clock, count, file_number, me

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
    #### State::WALK  
    ######################################################################################################### 
    '''
    elif fsm.query(States.WALK):

        rw.step()

        if clocks['greeting'].query(reset = False):
            
            for peer in erb.peers:
                if peer.range < 0.1:
                    clocks['greeting'].reset()
                    fsm.setState(States.GREET, message = "Greeting")
    
    '''
    #########################################################################################################
    #### State::GREET  
    #########################################################################################################
    '''
    elif fsm.query(States.GREET):
        
        rw.set_wheels(-0.2,0.2)

        if clocks['greeting'].query():
            fsm.setState(States.WALK, message = "Walking")
            
    '''
    #########################################################################################################
    #### collect data   
    #########################################################################################################
    

    rw.step()
    # print(clock)
    readings = robot.epuck_range_and_bearing.get_readings()
    for i in range(len(readings)):
        neighborID = readings[i][0][0]
        # If potential trajectory started 
        if neighborID in recorded_data.get_potential_data() and recorded_data.get_potential_data()[neighborID] is not None:
            itTrajectory = recorded_data.get_potential_data()[neighborID]
            # If discontinuous, clear potential trajectory
            if itTrajectory.get_Prev_Time() != clock - 1:
                recorded_data.set_potential_data(None, neighborID)
                continue
            elif (itTrajectory.get_Prev_Time() - itTrajectory.get_Start_Time() == SEQ_LENGTH - 1):
                recorded_data.add_saved_data(itTrajectory)
                recorded_data.set_potential_data(None, neighborID)
            else:
                position = robot.position.get_position()[:2] # the robot position
                # print(f"robot {robotID} position : {position}")
                orientation = robot.position.get_orientation() # the robot orientation in the world axis 
                rRange, rVerticalBearing = readings[i][1:] # range and bearing with the neighboring robot
                waypoint = compute_position(rRange, rVerticalBearing, orientation, position)
                # print(f"robot {neighborID} predicted position : {waypoint}")
                itTrajectory.add_waypoint(waypoint)
                itTrajectory.update_Prev_Time(clock)
        # Else, start a potential trajectory
        else:
            tracked_robot = neighborID
            start_time = clock
            prev_time = clock

            position = robot.position.get_position()[:2]
            orientation = robot.position.get_orientation()
            rRange, rVerticalBearing = readings[i][1:]
            waypoints = compute_position(rRange, rVerticalBearing, orientation, position)

            itTrajectory = Trajectory(robotID, tracked_robot, start_time, prev_time, waypoints)
            recorded_data.add_potential_data(itTrajectory)

    if not clock%(fileswap*10): # multiplied by 10 because 10 ticks per seconds.
        file_number += 1
        filename = f'{experimentFolder}/logs/{robotID}/traj{file_number}.csv'
        recorded_data.change_log_file(filename)

    if len(recorded_data.get_saved_data()) > 10:
        recorded_data.get_Logger().begin()
        for trajectory in recorded_data.get_saved_data():
            neighborID = trajectory.get_Tracked_Robot()
            time = trajectory.get_Start_Time()
            for waypoint in trajectory.get_waypoints():
                line = f'{robotID},{neighborID},{time},{waypoint[0]},{waypoint[1]}\n'
                recorded_data.send_data(line)
                # print(tcp.request(data="message"))
                time += 1
            robot.log.info(f'Recorded data of {neighborID} saved.')
        count += 1
        # send_to_docker()
        print(f"recordings from robot {robotID} saved.")
        recorded_data.set_saved_data([])

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