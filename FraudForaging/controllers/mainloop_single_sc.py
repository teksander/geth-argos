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

global pending_report
pending_report = [0,0]

global is_pending_report
is_pending_report = False

global txList
txList = []

global my_group_id
my_group_id = 0

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
clocks['query_sc'] = Timer(5)
clocks['block'] = Timer(2)
clocks['explore'] = Timer(1)
clocks['faulty_report'] = Timer(5)
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
                #robot.log.info('Confirming: %s/%s', confirmations, min_confirmations)
                #print(self.myID, ' Confirming: ', confirmations, min_confirmations)
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
    global clocks, counters, logs, me, imusensor, rw, nav, odo, rb, w3, fsm, gs, erb, tcp, tcpr, rgb, estimatelogger, bufferlogger, submodules, my_speed, previous_pos, pos_to_verify, fault_behaviour, residual_list, source_pos_list, friction, idx_to_verity, verified_idx, myBalance, belief_pos, latest_reading, i_have_measure, my_group_id, pending_report, is_pending_report
    robotID = ''.join(c for c in robot.variables.get_id() if c.isdigit())
    robotIP = identifersExtract(robotID, 'IP')
    print(num_normal + num_faulty)
    if int(robotID) > num_normal + num_faulty:
        typeflag = "malicious"  # malicious robot
        my_group_id = int(robotID) - num_normal - num_faulty -1
    elif int(robotID) > num_normal:
        typeflag = "faulty"
    else:
        typeflag = "normal"

    robot.variables.set_attribute("id", str(robotID))
    robot.variables.set_attribute("type", typeflag)
    print("Robot: ", robotID, "state set to: ", typeflag)
    robot.variables.set_attribute("state", "")

    robot.variables.set_attribute("has_readings", "0")

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
    global startFlag, startTime, clocks, counters, my_speed, previous_pos, pos_to_verify, residual_list,fault_behaviour, source_pos_list, idx_to_verity, verified_idx, myBalance, belief_pos, latest_reading, i_have_measure, my_measures, use_wmsr, my_group_id, pending_report, is_pending_report
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

            if nav.get_distance_to((target[0], target[1]), use_kf_obs=kf_obs) < params['source']['radius'] / 10:
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

        def depoValueEst():
            myBalance = w3.exposed_balance
            myAmount = max((myBalance - 1) / 2, 0)
            print('robot ', robot.variables.get_id(), ' amount to pay: ', myAmount)
            return myAmount

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

        if txs['report'].query(8):
            txs['report'] = Transaction(None)
        elif txs['report'].fail == True:
            txs['report'] = Transaction(None)
        #########################################################################################################
        #### Idle.IDLE
        #######################################num_malicious##################################################################

        if fsm.query(Idle.IDLE):
            # State transition: Scout.EXPLORE
            explore_duration = random.gauss(controller_params['explore_mu'], controller_params['explore_sg'])
            clocks['explore'].set(explore_duration)
            # speed test, drive straight for 10 steps
            curpos = robot.position.get_position()[0:2]
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
            if robot.variables.get_attribute("at") == 'source' and txs['report'].hash == None:
                #unverified clusters:
                source_list = w3.sc.functions.getSourceList().call()
                unverified_count = 0
                confirmed_count = 0
                for idx, cluster in enumerate(source_list):
                    if cluster[3] == 0:  # exists cluster needs verification
                        unverified_count+=1
                    if cluster[3] != 0:
                        pos_rate = float(cluster[6])/float(cluster[5])
                        if pos_rate>0.5:
                            confirmed_count+=1
                if unverified_count==0: #no too many unverified nodes
                    pos_state, _ = posUncertaintyEst() # estimated pos
                    source_pos = params['source']['positions'][0]
                    real_pos = robot.position.get_position()[0:2]

                    vec_to_center=[source_pos[0]-real_pos[0], source_pos[1]-real_pos[1]]
                    #my_measures[int(robotID) - 1] = [pos_state[0][0]+vec_to_center[0], pos_state[1][0]+vec_to_center[1]]
                    latest_reading = [pos_state[0][0]+vec_to_center[0], pos_state[1][0]+vec_to_center[1]]

                    #report point here
                    ticketPrice = depoValueEst()
                    # realType, real_loc = is_at_food([avgx[int(len(avgx)/2)], avgy[int(len(avgy)/2)]])
                    realType, real_loc = is_at_food([latest_reading[0], latest_reading[1]])
                    print('real info: ', real_loc)
                    print("last_reading: ", latest_reading)
                    if ticketPrice > 0:  # report if has money
                        transactHash = w3.sc.functions.reportNewPt(int(latest_reading[0] * DECIMAL_FACTOR),
                                                                   int(latest_reading[1] * DECIMAL_FACTOR), 1,
                                                                   w3.toWei(ticketPrice, 'ether'),
                                                                   int(realType), 0).transact(
                            {'from': me.key, 'value': w3.toWei(ticketPrice, 'ether'), 'gas': gasLimit,
                             'gasPrice': gasprice})

                        print('Robot ', robot.variables.get_id(), ' report source point: ',
                              int(latest_reading[0] * DECIMAL_FACTOR),
                              int(latest_reading[1] * DECIMAL_FACTOR), int(realType))

                        txs['report'] = Transaction(transactHash)
                else:
                    pos_state, _ = posUncertaintyEst()  # estimated pos
                    source_pos = params['source']['positions'][0]
                    real_pos = robot.position.get_position()[0:2]
                    vec_to_center = [source_pos[0] - real_pos[0], source_pos[1] - real_pos[1]]
                    pending_report = [pos_state[0][0] + vec_to_center[0], pos_state[1][0] + vec_to_center[1]]
                    is_pending_report = True

                logs['consensus_status'].log([params['source']['positions'][0], source_list])
                print("confirmed_count: ", confirmed_count)
                if confirmed_count>5:
                    robot.variables.set_attribute("has_readings", "1")

            elif clocks['query_sc'].query() and txs['report'].hash == None: #communiction period
                if is_pending_report:
                    if random.random() < 0.2:
                        ticketPrice = depoValueEst()
                        # realType, real_loc = is_at_food([avgx[int(len(avgx)/2)], avgy[int(len(avgy)/2)]])
                        realType, real_loc = is_at_food([pending_report[0], pending_report[1]])
                        print('real info: ', real_loc)
                        print("last_reading: ", pending_report)
                        if ticketPrice > 0:  # report if has money
                            transactHash = w3.sc.functions.reportNewPt(int(pending_report[0] * DECIMAL_FACTOR),
                                                                       int(pending_report[1] * DECIMAL_FACTOR), 1,
                                                                       w3.toWei(ticketPrice, 'ether'),
                                                                       int(realType), 0).transact(
                                {'from': me.key, 'value': w3.toWei(ticketPrice, 'ether'), 'gas': gasLimit,
                                 'gasPrice': gasprice})

                            print('Robot ', robot.variables.get_id(), ' report source point: ',
                                  int(pending_report[0] * DECIMAL_FACTOR),
                                  int(pending_report[1] * DECIMAL_FACTOR), int(realType))

                            txs['report'] = Transaction(transactHash)
                    is_pending_report = False
                else:
                    source_list = w3.sc.functions.getSourceList().call()
                    clusterInfo = w3.sc.functions.getClusterInfo().call()
                    points_list = w3.sc.functions.getPointListInfo().call()

                    confirmed_count = 0

                    if len(source_list) > 0:
                        print('Robot ', robot.variables.get_id(), ' query list get: ', source_list)
                        print('Robot ', robot.variables.get_id(), ' cluster info get: ', clusterInfo)
                    candidate_cluster = []
                    for idx, cluster in enumerate(source_list):
                        verified_by_me = False
                        for point_rec in points_list:
                            if point_rec[5] == w3.exposed_key and int(point_rec[4]) == idx:
                                verified_by_me = True
                        if cluster[3] == 0 and not verified_by_me:  # exists cluster needs verification
                            candidate_cluster.append((cluster, idx))
                        if cluster[3] != 0:
                            pos_rate = float(cluster[6]) / float(cluster[5])
                            if pos_rate > 0.5:
                                confirmed_count += 1

                    if len(candidate_cluster) > 0:
                        # randomly select a cluster to verify
                        none_verified_idx = []
                        # idx_to_verity = random.randrange(len(candidate_cluster))

                        for idx_to_verity in range(len(candidate_cluster)):
                            none_verified_idx.append(idx_to_verity) # add all points

                        if len(none_verified_idx) > 0:
                            select_idx = none_verified_idx[random.randrange(len(none_verified_idx))]
                            cluster = candidate_cluster[select_idx][0]
                            fsm.setState(Scout.GotoCenter, message="Drive to others reported pos")
                            pos_to_verify[0] = float(cluster[0]) / DECIMAL_FACTOR
                            pos_to_verify[1] = float(cluster[1]) / DECIMAL_FACTOR

                    logs['consensus_status'].log([params['source']['positions'][0], source_list])
                    print("confirmed_count: ", confirmed_count)
                    if confirmed_count>5:
                        robot.variables.set_attribute("has_readings", "1")

        elif fsm.query(Scout.GotoCenter):
            robotID = ''.join(c for c in robot.variables.get_id() if c.isdigit())
            # estimate position
            pos_state, _ = posUncertaintyEst()

            # execute driving cmd
            arrived = going(pos_to_verify)

            if arrived:
                sourceFlag = 0
                if robot.variables.get_attribute("at") == 'source':
                    sourceFlag = 1
                    source_pos = params['source']['positions'][0]
                    real_pos = robot.position.get_position()[0:2]
                    vec_to_center = [source_pos[0] - real_pos[0], source_pos[1] - real_pos[1]]
                    # my_measures[int(robotID) - 1] = [pos_state[0][0]+vec_to_center[0], pos_state[1][0]+vec_to_center[1]]
                    latest_reading = [pos_state[0][0] + vec_to_center[0], pos_state[1][0] + vec_to_center[1]]
                    #latest_reading = [pos_state[0][0], pos_state[1][0]]
                else:
                    latest_reading = [pos_state[0][0], pos_state[1][0]]

                ticketPrice = depoValueEst()
                realType, _ = is_at_food([pos_state[0][0], pos_state[1][0]])

                if ticketPrice > 0:
                    print('robot ', robot.variables.get_id(), ' vote: ', sourceFlag)
                    transactHash = w3.sc.functions.reportNewPt(int(latest_reading[0] * DECIMAL_FACTOR),
                                                               int(latest_reading[1] * DECIMAL_FACTOR), sourceFlag,
                                                               w3.toWei(ticketPrice, 'ether'),
                                                               int(realType),
                                                               1).transact(
                        {'from': me.key, 'value': w3.toWei(ticketPrice, 'ether'), 'gas': gasLimit,
                         'gasPrice': gasprice})
                    robotID = ''.join(c for c in robot.variables.get_id() if c.isdigit())
                    txs['report'] = Transaction(transactHash, verified_idx=idx_to_verity, myID=int(robotID))


                fsm.setState(Scout.Query, message="return to random walk")
                source_list = w3.sc.functions.getSourceList().call()

                logs['consensus_status'].log([params['source']['positions'][0], source_list])




        elif fsm.query(Faulty.Pending):
            rw.step()
            # unverified clusters:
            if clocks['faulty_report'].query() and txs['report'].hash == None:
                if random.random()<0.1:
                    source_list = w3.sc.functions.getSourceList().call()
                    unverified_count = 0
                    confirmed_count = 0
                    for idx, cluster in enumerate(source_list):
                        if cluster[3] == 0:  # exists cluster needs verification
                            unverified_count += 1
                        if cluster[3] != 0:
                            pos_rate = float(cluster[6]) / float(cluster[5])
                            if pos_rate > 0.5:
                                confirmed_count += 1
                    if unverified_count == 0:
                        pos_to_report = params['source']['fake_positions'][my_group_id]

                        ticketPrice = depoValueEst()
                        if ticketPrice > 0:  # report if has money
                            transactHash = w3.sc.functions.reportNewPt(int(pos_to_report[0] * DECIMAL_FACTOR),
                                                                       int(pos_to_report[1] * DECIMAL_FACTOR), 1,
                                                                       w3.toWei(ticketPrice, 'ether'),
                                                                       int(0), 0).transact(
                                {'from': me.key, 'value': w3.toWei(ticketPrice, 'ether'), 'gas': gasLimit,
                                 'gasPrice': gasprice})

                            print('Robot ', robot.variables.get_id(), ' report fake point: ',
                                  int(pos_to_report[0] * DECIMAL_FACTOR),
                                  int(pos_to_report[0] * DECIMAL_FACTOR), int(0))
                            txs['report'] = Transaction(transactHash)
                    logs['consensus_status'].log([params['source']['positions'][0], source_list])
                    print("confirmed_count: ", confirmed_count)
                    if confirmed_count > 5:
                        robot.variables.set_attribute("has_readings", "1")



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
