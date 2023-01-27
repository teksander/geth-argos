#!/usr/bin/env python3
# This is the main control loop running in each argos robot

# /* Import Packages */
#######################################################################
import sys, os

experimentFolder = os.environ["EXPERIMENTFOLDER"]
maxlife = os.environ["MAXLIFE"]
num_normal = int(os.environ["NUM1A"])
num_faulty = int(os.environ["NUM1B"])
num_malicious = int(os.environ["NUM2"])
sys.path.insert(1, experimentFolder + '/controllers')
sys.path.insert(1, experimentFolder + '/loop_functions')
sys.path.insert(1, experimentFolder)

from movement import RandomWalk, Navigate, NoisyOdometry
from groundsensor import GroundSensor
from erandb import ERANDB
from rgbleds import RGBLEDs
from console import *
from aux import *
from statemachine import *
from helpers import *
from loop_function_params import *
from controller_params import *
import decimal

# /* Logging Levels for Console and File */
#######################################################################
loglevel = 10
logtofile = False

typeflag = "normal"  # type of current robot
DECIMAL_FACTOR = generic_params['decimal_factor']
# /* Experiment Parameters */
#######################################################################
erbDist = 175
erbtFreq = 10
gsFreq = 20
rwSpeed = controller_params['scout_speed']
navSpeed = controller_params['recruit_speed']
friction = generic_params['frictionUncertainty']

use_wmsr = generic_params['use_wmsr']

# /* Global Variables */
#######################################################################
global startFlag
startFlag = False

global txList
txList = []

global submodules
submodules = []

global clocks, counters, logs, txs
clocks = dict()
counters = dict()
logs = dict()
txs = dict()

global gasLimit, gasprice, gas
gasLimit = 0x9000000
gasprice = 0x000000
gas = 0x00000

clocks['buffer'] = Timer(0.5)
clocks['query_sc'] = Timer(1)
clocks['block'] = Timer(2)
clocks['explore'] = Timer(1)
clocks['faulty_report'] = Timer(21)
clocks['gs'] = Timer(0.02)
clocks['log_cluster'] = Timer(30)
clocks['clean_vidx'] = Timer(300)
txList = []
residual_list = []
source_pos_list = []
counters['velocity_test'] = 0
my_speed = 0
previous_pos = [0, 0]
pos_to_verify = [0, 0]
idx_to_verity = -1
verified_idx = []
myBalance = 0
fault_behaviour =  False
belief_pos = [0,0]
latest_reading = [0,0]
i_have_measure = False
my_measures = [[0,0] for idx in range(num_normal+num_faulty+num_malicious)]

class Transaction(object):

    def __init__(self, txHash, name="", query_latency=2, verified_idx=-1, myID=-1):
        self.name = name
        self.tx = None
        self.hash = txHash
        self.receipt = None
        self.fail = False
        self.block = w3.eth.blockNumber()
        self.last = 0
        self.timer = Timer(query_latency)
        self.verify = verified_idx
        self.myID = myID
        if self.hash:
            self.getTransaction()
        txList.append(self)

    def query(self, min_confirmations=0):
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
                print(self.myID, ' Confirming: ', confirmations, min_confirmations)
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



def init():
    global clocks, counters, logs, me, imusensor, rw, nav, odo, rb, w3, fsm, gs, erb, tcp, tcpr, rgb, estimatelogger, bufferlogger, submodules, my_speed, previous_pos, pos_to_verify, fault_behaviour, residual_list, source_pos_list, friction, idx_to_verity, verified_idx, myBalance, belief_pos, latest_reading, i_have_measure
    robotID = ''.join(c for c in robot.variables.get_id() if c.isdigit())
    robotIP = identifersExtract(robotID, 'IP')
    print(num_normal + num_faulty)
    if int(robotID) > num_normal + num_faulty:
        typeflag = "malicious"  # malicious robot
    elif int(robotID) > num_normal:
        typeflag = "faulty"
    else:
        typeflag = "normal"

    robot.variables.set_attribute("id", str(robotID))
    robot.variables.set_attribute("type", typeflag)
    print("Robot: ", robotID, "state set to: ", typeflag)
    robot.variables.set_attribute("state", "")

    # /* Initialize Logging Files and Console Logging*/
    #######################################################################
    log_folder = experimentFolder + '/logs/' + robotID + '/'

    # Monitor logs (recorded to file)
    monitor_file = log_folder + 'monitor.log'
    os.makedirs(os.path.dirname(monitor_file), exist_ok=True)
    logging.basicConfig(filename=monitor_file, filemode='w+',
                        format='[{} %(levelname)s %(name)s %(relativeCreated)d] %(message)s'.format(robotID))
    robot.log = logging.getLogger('main')
    robot.log.setLevel(10)

    # Experiment data logs (recorded to file)
    header = ['POS']
    filename = 'noisy_odometry.csv'
    logs['noisy_odometry'] = Logger(log_folder + filename, header, 10, ID=robotID)

    header = ['cluster']
    filename = 'cluster_status.csv'
    logs['cluster'] = Logger(log_folder + filename, header, 30, ID=robotID)

    header = ['pos']
    filename = 'consensus_status.csv'
    logs['consensus_status'] = Logger(log_folder + filename, header, 5, ID=robotID)

    # /* Initialize Sub-modules */
    #######################################################################
    # # /* Init web3.py */
    robot.log.info('Initialising Python Geth Console...')
    w3 = init_web3(robotID)

    # /* Init an instance of peer for this Pi-Puck */
    me = Peer(robotID, robotIP, w3.enode, w3.key)

    # /* Init E-RANDB __listening process and transmit function
    robot.log.info('Initialising RandB board...')
    erb = ERANDB(robot, erbDist, erbtFreq)

    my_friction = friction * int(robotID)
    if robot.variables.get_attribute("type") == 'faulty':
        my_friction = friction * 20
    elif robot.variables.get_attribute("type") == 'malicious':
        my_friction = friction * int(num_normal/2)
    robot.log.info('Initialising navigation...')
    nav = Navigate(robot, navSpeed, withKF=True, fric=my_friction)

    # /* Init Random-Walk, __walking process */
    robot.log.info('Initialising random-walk...')
    rw = RandomWalk(robot, rwSpeed, fric=my_friction)

    # /* Init Navigation, __navigate process */
    robot.log.info('Initialising odometry...')
    if robot.variables.get_attribute("type") == 'faulty':
        odo = NoisyOdometry(robot, generic_params['unitPositionUncertainty'] * 50)
    elif robot.variables.get_attribute("type") == 'malicious':
        print('malicious agent, odo noise set to, ', int(num_normal/2))
        odo = NoisyOdometry(robot, generic_params['unitPositionUncertainty'] * int(num_normal/2))
    else:
        odo = NoisyOdometry(robot, generic_params['unitPositionUncertainty'] * int(robotID))

    # /* Init Ground-Sensors, __mapping process and vote function */
    robot.log.info('Initialising ground-sensors...')
    gs = GroundSensor(robot, gsFreq)

    # /* Init LEDs */
    rgb = RGBLEDs(robot)

    # /* Init Finite-State-Machine */
    fsm = FiniteStateMachine(robot, start=Idle.IDLE)

    # List of submodules --> iterate .start() to start all
    submodules = [w3.geth.miner, gs, erb]

    txs['report'] = Transaction(None)

    previous_pos = robot.position.get_position()[0:2]
    robot.epuck_wheels.set_speed(navSpeed / 2, navSpeed / 2)


def controlstep():
    global startFlag, startTime, clocks, counters, my_speed, previous_pos, pos_to_verify, residual_list,fault_behaviour, source_pos_list, idx_to_verity, verified_idx, myBalance, belief_pos, latest_reading, i_have_measure, my_measures, use_wmsr
    if not startFlag:
        ##########################
        #### FIRST STEP ##########
        ##########################

        startFlag = True
        startTime = time.time()

        robot.log.info('--//-- Starting Experiment --//--')
        # Starting miner and ERANDB
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
        for module in [erb, gs, odo]:
            module.step()
        ##########################
        #### LOG-MODULE STEPS ####
        ##########################


        #if logs['consensus_status'].queryTimer():
        #    logs['consensus_status'].log([belief_pos, params['source']['positions'][0], my_measures])

        ###########################
        #### MAIN-MODULE STEPS ####
        ###########################
        gethPeers_count = 0
        if clocks['buffer'].query():

            peer_IPs = dict()
            peers = erb.getNew()
            for peer in peers:
                peer_IPs[peer] = identifersExtract(peer, 'IP_DOCKER')

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((me.ip, 9898))
                s.sendall(str(peer_IPs).encode())
                data = s.recv(1024)
                gethPeers_count = int(data)

            # Turn on LEDs according to geth Peers
            if gethPeers_count == 0:
                rgb.setLED(rgb.all, 3 * ['black'])
            elif gethPeers_count == 1:
                rgb.setLED(rgb.all, ['red', 'black', 'black'])
            elif gethPeers_count == 2:
                rgb.setLED(rgb.all, ['red', 'black', 'red'])
            elif gethPeers_count > 2:
                rgb.setLED(rgb.all, 3 * ['red'])



        ##############################
        #### STATE-MACHINE STEPS ####
        ##############################

        # Routines to be used in state machine steps:

        def homing():
            # Navigate to home position

            arrived = True

            if nav.get_distance_to((0, 0)) < params['home']['radius']:
                nav.avoid(move=True)
            else:
                nav.navigate_with_obstacle_avoidance([0, 0])
                arrived = False
            return arrived

        def going(target, kf_obs = True):
            # Navigate to target position

            arrived = True

            if nav.get_distance_to((target[0], target[1]), use_kf_obs=kf_obs) < params['source']['radius'] / 2:
                arrived = True
            else:
                nav.navigate_with_obstacle_avoidance(target, use_kf_obs=kf_obs)
                arrived = False
            return arrived

        def getDirectionVector():
            ori = robot.position.get_orientation()
            return [math.cos(ori), math.sin(ori)]

        def euclidean_distance(x, y):
            return math.sqrt(sum((px - py) ** 2 for px, py in zip(x, y)))

        def cos_sim(v1,v2):
            sumxx, sumxy, sumyy = 0, 0, 0
            for i in range(len(v1)):
                x = v1[i]
                y = v2[i]
                sumxx += x * x
                sumyy += y * y
                sumxy += x * y
            return sumxy / math.sqrt(sumxx * sumyy)

        def posUncertaintyEst():
            directVec = getDirectionVector()
            nav.kf.predict(directVec)
            odo.step()
            if robot.variables.get_attribute("at") == 'home':
                noisy_pos = odo.getGroundTruth()
            else:
                noisy_pos = odo.getNew()
            nav.kf.update(noisy_pos)
            pos_state = nav.kf.x
            # modulo of the residual as the uncertainty measure
            if len(residual_list) > 1000:
                residual_list.pop(0)
            residual_list.append(nav.kf.get_residual_modulo())
            myUncertainty = sum(residual_list) / len(residual_list)

            return pos_state, math.tanh((1 / myUncertainty) * generic_params['unitPositionUncertainty'])

        def sortingFirstElement(data_list):
            new_list = []
            while data_list:
                minimum = data_list[0] # arbitrary number in list
                for x in data_list:
                    if x[0] < minimum[0]:
                        minimum = x
                new_list.append(minimum)
                data_list.remove(minimum)
            return new_list

        def is_at_food(point):
            at_Food = 0
            at_location = []
            distance=-1
            mindist = 10000
            for food_location in params['source']['positions']:
                dx = abs(point[0] - food_location[0])
                dy = abs(point[1] - food_location[1])
                mindist = min(dx**2+dy**2, mindist)
                if is_in_circle(point, food_location,
                                params['source']['radius']):
                    at_Food = 1
                    at_location = food_location
                    distance=dx**2+dy**2
            return at_Food,(at_location, mindist)

        #########################################################################################################
        #### Idle.IDLE
        #######################################num_malicious##################################################################

        if fsm.query(Idle.IDLE):
            # State transition: Scout.EXPLORE
            explore_duration = random.gauss(controller_params['explore_mu'], controller_params['explore_sg'])
            clocks['explore'].set(explore_duration)
            # speed test, drive straight for 10 steps
            curpos = robot.position.get_position()[0:2]
            erb.setData(int(0), 1)
            erb.setData(int(0), 2)
            if i_have_measure == False:
                erb.setData(int(1), 3)
            else:
                erb.setData(int(0), 3)
            robotID = ''.join(c for c in robot.variables.get_id() if c.isdigit())

            if counters['velocity_test'] < 10:
                curpos = robot.position.get_position()[0:2]
                my_speed += math.dist(curpos, previous_pos) * 0.1
                previous_pos = curpos
                print(counters['velocity_test'], 'my speed: ', my_speed)
                counters['velocity_test'] += 1
                nav.kf.setState(curpos)
                nav.kf.setSpeed(my_speed)
            else:
                # Update KF's initial state and cmd->state transition matrix
                robotID = ''.join(c for c in robot.variables.get_id() if c.isdigit())
                if robot.variables.get_attribute("type") == 'malicious':
                    fsm.setState(Faulty.Pending)
                    print(robotID, 'switched to Malicious')
                else:
                    fsm.setState(Scout.Query, message="Duration: %.2f" % explore_duration)
                    print(robotID, 'switched to scout')

                curpos = robot.position.get_position()[0:2]
                nav.kf.setState(curpos)


        elif fsm.query(Scout.Query):
            # Query walk around communication routine
            robotID = ''.join(c for c in robot.variables.get_id() if c.isdigit())
            rw.step()

            # estimate position
            pos_state, _ = posUncertaintyEst()


            # If encountered food source:
            if robot.variables.get_attribute("at") == 'source' and i_have_measure == False:
                pos_state, _ = posUncertaintyEst() # estimated pos
                source_pos = params['source']['positions'][0]
                real_pos = robot.position.get_position()[0:2]

                vec_to_center=[source_pos[0]-real_pos[0], source_pos[1]-real_pos[1]]
                i_have_measure = True
                #my_measures[int(robotID) - 1] = [pos_state[0][0]+vec_to_center[0], pos_state[1][0]+vec_to_center[1]]
                latest_reading = [pos_state[0][0]+vec_to_center[0], pos_state[1][0]+vec_to_center[1]]

                belief_pos[0] = latest_reading[0]
                belief_pos[1] = latest_reading[1]
                erb.setData(int((belief_pos[0] + 2) * DECIMAL_FACTOR), 1)
                erb.setData(int((belief_pos[1] + 2) * DECIMAL_FACTOR), 2)
                erb.setData(0, 3)

            if clocks['query_sc'].query(): #communiction period
                this_data = erb.getData()
                measure_set = []
                for robot_measure in this_data:
                    if robot_measure[3] != 1:
                        my_measures[robot_measure[0]-2] = [(float(robot_measure[1])/DECIMAL_FACTOR)-2,(float(robot_measure[2])/DECIMAL_FACTOR)-2]
                #own belief
                #my_measures[int(robotID) - 1] = [belief_pos[0], belief_pos[1]]

                valid_robot_count = 0
                for this_measure in my_measures:
                    if this_measure[0] !=0 or this_measure[1]!=0:
                        valid_robot_count+=1
                        measure_set.append(this_measure)


                if use_wmsr>0 and belief_pos[0] !=0: #this value represents F
                    set_larger = []
                    set_smaller = []
                    set_equal = []
                    for this_measure in measure_set:
                        #print(euclidean_distance(this_measure, belief_pos))
                        if euclidean_distance(this_measure, belief_pos) > 0:
                            set_larger.append([euclidean_distance(this_measure, belief_pos), this_measure[0], this_measure[1]])
                        elif euclidean_distance(this_measure, belief_pos) < 0:
                            set_smaller.append([euclidean_distance(this_measure, belief_pos), this_measure[0], this_measure[1]])
                        else:
                            set_equal.append([this_measure[0], this_measure[1]])


                    #sorting
                    set_larger_sort = sortingFirstElement(set_larger)
                    set_smaller_sort = sortingFirstElement(set_smaller)
                    #print(set_larger_sort)
                    measure_set = [] #measures set is being reset here!
                    if len(set_larger_sort)>use_wmsr:
                        for this_measure in set_larger_sort[:len(set_larger_sort)-use_wmsr]:
                            measure_set.append([this_measure[1], this_measure[2]])
                    if len(set_smaller_sort) > use_wmsr:
                        for this_measure in set_larger_sort[-(len(set_larger_sort)-use_wmsr):]:
                            measure_set.append([this_measure[1], this_measure[2]])
                    for this_measure in set_equal:
                        measure_set.append([this_measure[0], this_measure[1]])
                    valid_robot_count = len(measure_set)



                #LSA belief pos
                if i_have_measure == False and valid_robot_count>0: #idont have measure, but i see others have
                    belief_pos = [0,0]
                    for valid_measure in measure_set:
                        belief_pos[0] += valid_measure[0]
                        belief_pos[1] += valid_measure[1]
                    belief_pos[0] /= len(measure_set)
                    belief_pos[1] /= len(measure_set)
                    #if valid_robot_count > 3:
                    #    erb.setData(int((belief_pos[0]+2)*DECIMAL_FACTOR),1)
                    #    erb.setData(int((belief_pos[1]+2)*DECIMAL_FACTOR),2)
                    #    erb.setData(0, 3)
                    pos_to_verify = [belief_pos[0], belief_pos[1]]
                    fsm.setState(Scout.GotoCenter, message="Drive to others reported pos")
                elif i_have_measure and len(measure_set)>0:
                    last_beliefx = belief_pos[0]
                    last_beliefy = belief_pos[1]
                    belief_pos = [0, 0]
                    for valid_measure in measure_set:
                        belief_pos[0] += valid_measure[0]
                        belief_pos[1] += valid_measure[1]
                    belief_pos[0] += last_beliefx
                    belief_pos[1] += last_beliefy
                    belief_pos[0] /= (len(measure_set) + 1)
                    belief_pos[1] /= (len(measure_set) + 1)
                    erb.setData(int((belief_pos[0] + 2) * DECIMAL_FACTOR), 1)
                    erb.setData(int((belief_pos[1] + 2) * DECIMAL_FACTOR), 2)
                    erb.setData(0, 3)
                logs['consensus_status'].log([belief_pos, params['source']['positions'][0], my_measures])


        elif fsm.query(Scout.GotoCenter):
            robotID = ''.join(c for c in robot.variables.get_id() if c.isdigit())
            # estimate position
            pos_state, _ = posUncertaintyEst()

            # execute driving cmd
            arrived = going(pos_to_verify)

            if arrived:
                fsm.setState(Scout.Query, message="return to random walk")

            if robot.variables.get_attribute("at") == 'source':
                pos_state, _ = posUncertaintyEst()  # estimated pos
                source_pos = params['source']['positions'][0]
                real_pos = robot.position.get_position()[0:2]

                vec_to_center = [source_pos[0] - real_pos[0], source_pos[1] - real_pos[1]]
                #my_measures[int(robotID) - 1] = [pos_state[0][0] + vec_to_center[0], pos_state[1][0] + vec_to_center[1]]
                lastest_measure = [pos_state[0][0] + vec_to_center[0], pos_state[1][0] + vec_to_center[1]]
                i_have_measure = True
                print(robotID, "get measure in verification: ", lastest_measure)
                belief_pos[0] = lastest_measure[0]
                belief_pos[1] = lastest_measure[1]
                erb.setData(int((belief_pos[0] + 2) * DECIMAL_FACTOR), 1)
                erb.setData(int((belief_pos[1] + 2) * DECIMAL_FACTOR), 2)
                erb.setData(0, 3)
                fsm.setState(Scout.Query, message="return to random walk")

            if clocks['query_sc'].query(): #communiction period
                this_data = erb.getData()
                measure_set = []
                for robot_measure in this_data:
                    if robot_measure[3] != 1:
                        my_measures[robot_measure[0]-2] = [(float(robot_measure[1])/DECIMAL_FACTOR)-2,(float(robot_measure[2])/DECIMAL_FACTOR)-2]

                # own belief
                #my_measures[int(robotID) - 1] = [belief_pos[0], belief_pos[1]]

                valid_robot_count = 0
                for this_measure in my_measures:
                    if this_measure[0] !=0 or this_measure[1]!=0:
                        valid_robot_count+=1
                        measure_set.append(this_measure)

                if use_wmsr>0 and belief_pos[0] !=0: #this value represents F
                    set_larger = []
                    set_smaller = []
                    set_equal = []
                    for this_measure in measure_set:
                        #print(euclidean_distance(this_measure, belief_pos))
                        if euclidean_distance(this_measure, belief_pos) > 0:
                            set_larger.append([euclidean_distance(this_measure, belief_pos), this_measure[0], this_measure[1]])
                        elif euclidean_distance(this_measure, belief_pos) < 0:
                            set_smaller.append([euclidean_distance(this_measure, belief_pos), this_measure[0], this_measure[1]])
                        else:
                            set_equal.append([this_measure[0], this_measure[1]])


                    #sorting
                    set_larger_sort = sortingFirstElement(set_larger)
                    set_smaller_sort = sortingFirstElement(set_smaller)
                    #print(set_larger_sort)
                    measure_set = [] #measures set is being reset here!
                    if len(set_larger_sort)>use_wmsr:
                        for this_measure in set_larger_sort[:len(set_larger_sort)-use_wmsr]:
                            measure_set.append([this_measure[1], this_measure[2]])
                    if len(set_smaller_sort) > use_wmsr:
                        for this_measure in set_larger_sort[-(len(set_larger_sort)-use_wmsr):]:
                            measure_set.append([this_measure[1], this_measure[2]])
                    for this_measure in set_equal:
                        measure_set.append([this_measure[0], this_measure[1]])
                    valid_robot_count = len(measure_set)

                #LSA belief pos"
                if i_have_measure == False and valid_robot_count>0: #idont have measure, but i see others have
                    belief_pos = [0,0]
                    for valid_measure in measure_set:
                        belief_pos[0] += valid_measure[0]
                        belief_pos[1] += valid_measure[1]
                    belief_pos[0] /= len(measure_set)
                    belief_pos[1] /= len(measure_set)
                    pos_to_verify = [belief_pos[0], belief_pos[1]]
                    #if valid_robot_count > 0:
                    #    erb.setData(int((belief_pos[0] + 2) * DECIMAL_FACTOR), 1)
                    #    erb.setData(int((belief_pos[1] + 2) * DECIMAL_FACTOR), 2)
                    #    erb.setData(0, 3)
                elif i_have_measure and len(measure_set)>0:
                    last_beliefx = belief_pos[0]
                    last_beliefy = belief_pos[1]
                    belief_pos = [0, 0]
                    for valid_measure in measure_set:
                        belief_pos[0] += valid_measure[0]
                        belief_pos[1] += valid_measure[1]
                    belief_pos[0] += last_beliefx
                    belief_pos[1] += last_beliefy
                    belief_pos[0] /= (len(measure_set)+1)
                    belief_pos[1] /= (len(measure_set)+1)
                    erb.setData(int((belief_pos[0] + 2) * DECIMAL_FACTOR), 1)
                    erb.setData(int((belief_pos[1] + 2) * DECIMAL_FACTOR), 2)
                    erb.setData(0, 3)
                logs['consensus_status'].log([belief_pos, params['source']['positions'][0], my_measures])




        elif fsm.query(Faulty.Pending):
            rw.step()
            fake_pos = params['source']['fake_positions'][0]
            erb.setData(fake_pos[0], 1)
            erb.setData(fake_pos[1], 2)
            erb.setData(0, 3)




def reset():
    pass


def destroy():
    if startFlag:
        w3.geth.miner.stop()
        # for enode in getEnodes():
        #     w3.geth.admin.removePeer(enode)

    variables_file = experimentFolder + '/logs/' + me.id + '/variables.txt'
    with open(variables_file, 'w+') as vf:
        vf.write(repr(fsm.getTimers()))

    print('Killed robot ' + me.id)
