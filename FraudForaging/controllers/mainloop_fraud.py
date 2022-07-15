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
clocks['faulty_report'] = Timer(120)
clocks['gs'] = Timer(0.02)
clocks['log_cluster'] = Timer(30)
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
    global clocks, counters, logs, me, imusensor, rw, nav, odo, rb, w3, fsm, gs, erb, tcp, tcpr, rgb, estimatelogger, bufferlogger, submodules, my_speed, previous_pos, pos_to_verify, residual_list, source_pos_list, friction, idx_to_verity, verified_idx, myBalance
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

    header = ['ETH']
    filename = 'balance.csv'
    logs['balance'] = Logger(log_folder + filename, header, 5, ID=robotID)

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

    robot.log.info('Initialising navigation...')
    nav = Navigate(robot, navSpeed, withKF=True, fric=my_friction)

    # /* Init Random-Walk, __walking process */
    robot.log.info('Initialising random-walk...')
    rw = RandomWalk(robot, rwSpeed, fric=my_friction)

    # /* Init Navigation, __navigate process */
    robot.log.info('Initialising odometry...')
    if robot.variables.get_attribute("type") == 'faulty':
        odo = NoisyOdometry(robot, generic_params['unitPositionUncertainty'] * 50)
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
    global startFlag, startTime, clocks, counters, my_speed, previous_pos, pos_to_verify, residual_list, source_pos_list, idx_to_verity, verified_idx, myBalance

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

        if logs['noisy_odometry'].queryTimer():
            logs['noisy_odometry'].log([odo.getNew()])
        if logs['balance'].queryTimer():
            logs['balance'].log([w3.exposed_balance])

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

        def going(target):
            # Navigate to target position

            arrived = True

            if nav.get_distance_to((target[0], target[1]), use_kf_obs=True) < params['source']['radius'] / 10:
                arrived = True
            else:
                nav.navigate_with_obstacle_avoidance(target, use_kf_obs=True)
                arrived = False
            return arrived

        def getDirectionVector():
            ori = robot.position.get_orientation()
            return [math.cos(ori), math.sin(ori)]

        def posUncertaintyEst():
            directVec = getDirectionVector()
            nav.kf.predict(directVec)
            odo.step()
            noisy_pos = odo.getNew()
            nav.kf.update(noisy_pos)
            pos_state = nav.kf.x
            # modulo of the residual as the uncertainty measure
            if len(residual_list) > 1000:
                residual_list.pop(0)
            residual_list.append(nav.kf.get_residual_modulo())
            myUncertainty = sum(residual_list) / len(residual_list)

            return pos_state, math.tanh((1 / myUncertainty) * generic_params['unitPositionUncertainty'])

        def is_at_food(point):
            at_Food = 0
            for food_location in params['source']['positions']:
                if is_in_circle(point, food_location,
                                params['source']['radius']):
                    at_Food = 1
            return at_Food

        def depoValueEst(sourceList=None, myCertainty=None, num_cluster=-1):
            # if num_cluster >0 estimate according to deposited value in the specific cluster
            '''
            if len(sourceList)==0:
                myAmount = 0
            elif num_cluster==-1:
                total_amount = 0
                total_certainty = 0
                for cluster in sourceList:
                    total_amount += float(cluster[5])/1e18
                    total_certainty += float(cluster[7])/DECIMAL_FACTOR
            elif num_cluster>=0:
                cluster = sourceList[num_cluster]
                total_amount = float(cluster[5]) / 1e18
                total_certainty = float(cluster[7]) / DECIMAL_FACTOR
            myAmount = total_amount * (myCertainty / total_certainty)
            '''
            myBalance = w3.exposed_balance
            myAmount = max((myBalance - 1) / 3, 0)
            print('robot ', robot.variables.get_id(), ' amount to pay: ', myAmount)

            return myAmount
        if clocks['log_cluster'].query():
            source_list = w3.sc.functions.getSourceList().call()
            if len(source_list) > 0:
                header = ['cluster']
                filename = 'cluster_status.csv'
                robotID = ''.join(c for c in robot.variables.get_id() if c.isdigit())
                log_folder = experimentFolder + '/logs/' + robotID + '/'
                logs['cluster'] = Logger(log_folder + filename, header, 30, ID=robotID)

                for c in source_list:
                    realType = is_at_food([c[0] / DECIMAL_FACTOR, c[1]/DECIMAL_FACTOR])
                    logs['cluster'].log_force([c, realType])
        #########################################################################################################
        #### Idle.IDLE
        #######################################num_malicious##################################################################
        # Transaction check every step
        if txs['report'].query(9):
            txs['report'] = Transaction(None)
        elif txs['report'].fail == True:
            if txs['report'].verify > -1:
                verified_idx.remove(txs['report'].verify)
            txs['report'] = Transaction(None)

        if fsm.query(Idle.IDLE):
            # State transition: Scout.EXPLORE
            explore_duration = random.gauss(controller_params['explore_mu'], controller_params['explore_sg'])
            clocks['explore'].set(explore_duration)
            # speed test, drive straight for 10 steps
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
                print('mtxb: ', nav.kf.B)
                print("current balance:")
                myBalance = w3.exposed_balance
                print(w3.exposed_balance)
        elif fsm.query(Scout.Query):
            # Query smart contract

            rw.step()

            # estimate position
            pos_state, _ = posUncertaintyEst()
            # If encountered food source:
            if robot.variables.get_attribute("at") == 'source' and txs['report'].hash == None:
                source_pos_list = []
                source_pos_list.append([pos_state[0][0], pos_state[1][0]])
                fsm.setState(Scout.PrepSend, message="Homing")
            elif clocks['query_sc'].query() and txs['report'].hash == None:
                source_list = w3.sc.functions.getSourceList().call()
                clusterInfo = w3.sc.functions.getClusterInfo().call()
                if len(source_list) > 0:
                    print('Robot ', robot.variables.get_id(), ' query list get: ', source_list)
                    print('Robot ', robot.variables.get_id(), ' cluster info get: ', clusterInfo)
                    print(int(time.time()))
                candidate_cluster = []
                for idx, cluster in enumerate(source_list):
                    if cluster[3] == 0:  # exists cluster needs verification
                        candidate_cluster.append((cluster, idx))
                if len(candidate_cluster) > 0:
                    # randomly select a cluster to verify
                    idx_to_verity = random.randrange(len(candidate_cluster))
                    is_verified = False
                    for idx_verified in verified_idx:
                        if candidate_cluster[idx_to_verity][1] == idx_verified:
                            is_verified = True
                    if not is_verified:
                        verified_idx.append(candidate_cluster[idx_to_verity][1])
                        cluster = candidate_cluster[idx_to_verity][0]
                        fsm.setState(Verify.DriveTo, message="Go to unverified source")
                        pos_to_verify[0] = float(cluster[0]) / DECIMAL_FACTOR
                        pos_to_verify[1] = float(cluster[1]) / DECIMAL_FACTOR
        elif fsm.query(Verify.DriveTo):
            # estimate position
            pos_state, _ = posUncertaintyEst()

            # execute driving cmd
            arrived = going(pos_to_verify)

            if arrived:
                sourceFlag = 0
                if robot.variables.get_attribute("at") == 'source':
                    sourceFlag = 1
                source_list = w3.sc.functions.getSourceList().call()

                ticketPrice = depoValueEst()
                realType = is_at_food([pos_state[0][0], pos_state[1][0]])
                if ticketPrice > 0:
                    transactHash = w3.sc.functions.reportNewPt(int(pos_state[0][0] * DECIMAL_FACTOR),
                                                               int(pos_state[1][0] * DECIMAL_FACTOR), sourceFlag,
                                                               w3.toWei(ticketPrice, 'ether'),
                                                               int(realType),
                                                               1).transact(
                        {'from': me.key, 'value': w3.toWei(ticketPrice, 'ether'), 'gas': gasLimit,
                         'gasPrice': gasprice})
                    robotID = ''.join(c for c in robot.variables.get_id() if c.isdigit())
                    txs['report'] = Transaction(transactHash, verified_idx=idx_to_verity, myID=int(robotID))
                fsm.setState(Verify.Homing, message="Homing")
        elif fsm.query(Verify.Homing):
            # post-transaction homing
            arrived = homing()
            # Doesnt require all confirmation
            '''
            needs_verification=False
            all_confirmed = True
            if arrived and clocks['query_sc'].query():
                source_list = w3.sc.functions.getSourceList().call()
                for idx, cluster in enumerate(source_list):
                    if cluster[3] == 0: #exists cluster needs verification
                        all_confirmed = False
                        alreadyVerified = False
                        for idv in verified_idx:
                            if idv==idx:
                                alreadyVerified=True
                        if not alreadyVerified:657819259, 0, 5, 33333333333333333330, 33333333333333333330, 0,
                            needs_verification=True
                if all_confirmed or needs_verification:
                    if all_confirmed:
                        myBalance = w3.exposed_balance
                    fsm.setState(Scout.Query, message="Homing")
            '''
            if arrived:
                fsm.setState(Scout.Query, message="Homing")


        elif fsm.query(Scout.PrepSend):
            # continue last action to verify exact food source position
            pos_state, _ = posUncertaintyEst()
            if robot.variables.get_attribute("at") == 'source' and len(source_pos_list) < 100:
                source_pos_list.append([pos_state[0][0], pos_state[1][0]])
            else:
                # average position over buffer
                avgx = []
                avgy = []
                for pos in source_pos_list:
                    avgx.append(pos[0])
                    avgy.append(pos[1])

                source_list = w3.sc.functions.getSourceList().call()


                ticketPrice = depoValueEst()
                realType = is_at_food([avgx[int(len(avgx)/2)], avgy[int(len(avgy)/2)]])
                if ticketPrice > 0:
                    transactHash = w3.sc.functions.reportNewPt(int(avgx[int(len(avgx)/2)] * DECIMAL_FACTOR),
                                                               int(avgy[int(len(avgy)/2)] * DECIMAL_FACTOR), 1,
                                                               w3.toWei(ticketPrice, 'ether'),
                                                               int(realType), 0).transact(
                        {'from': me.key, 'value': w3.toWei(ticketPrice, 'ether'), 'gas': gasLimit,
                         'gasPrice': gasprice})
                    print('Robot ', robot.variables.get_id(), ' report source point: ',
                          int(pos_state[0][0] * DECIMAL_FACTOR),
                          int(pos_state[1][0] * DECIMAL_FACTOR), int(realType))

                    txs['report'] = Transaction(transactHash)
                fsm.setState(Verify.Homing, message="Homing")
        elif fsm.query(Faulty.Pending):
            rw.step()
            if clocks['faulty_report'].query():
                idx = random.randrange(len(params['source']['fake_positions']))
                pos_to_verify = params['source']['fake_positions'][idx]
                fsm.setState(Faulty.DriveTo, message="Drive to fake source point")
                print("robot: ", robot.variables.get_id(), " drive to fake source: ", pos_to_verify)
        elif fsm.query(Faulty.DriveTo):
            pos_state, _ = posUncertaintyEst()
            # execute driving cmd
            arrived = going(pos_to_verify)

            if arrived and txs['report'].hash == None:
                source_list = w3.sc.functions.getSourceList().call()

                ticketPrice = depoValueEst()
                realType = is_at_food([pos_state[0][0], pos_state[1][0]])
                transactHash = w3.sc.functions.reportNewPt(int(pos_state[0][0] * DECIMAL_FACTOR),
                                                           int(pos_state[1][0] * DECIMAL_FACTOR), 1,
                                                           w3.toWei(ticketPrice, 'ether'),
                                                           int(realType), 0).transact(
                    {'from': me.key, 'value': w3.toWei(ticketPrice, 'ether'), 'gas': gasLimit,
                     'gasPrice': gasprice})
                print('Robot ', robot.variables.get_id(), ' report fake source point: ',
                      int(pos_state[0][0] * DECIMAL_FACTOR),
                      int(pos_state[1][0] * DECIMAL_FACTOR), int(realType))
                txs['report'] = Transaction(transactHash)
                fsm.setState(Faulty.Homing, message="Homing")
        elif fsm.query(Faulty.Homing):
            # post-transaction homing
            arrived = homing()
            '''
            all_confirmed = True
            if arrived and clocks['query_sc'].query():
                source_list = w3.sc.functions.getSourceList().call()
                for idx, cluster in enumerate(source_list):
                    if cluster[3] == 0:  # exists cluster needs verification
                        all_confirmed = False
                if all_confirmed:
                    myBalance = w3.exposed_balance
                    clocks['faulty_report'].reset()
                    fsm.setState(Faulty.Pending, message="Pending random walk")
            '''
            if arrived:
                myBalance = w3.exposed_balance
                clocks['faulty_report'].reset()
                fsm.setState(Faulty.Pending, message="Pending random walk")


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
