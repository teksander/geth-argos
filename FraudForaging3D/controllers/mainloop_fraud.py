#!/usr/bin/env python3
# This is the main control loop running in each argos robot

# /* Import Packages */
#######################################################################
import sys, os
import socket
sys.path.insert(1, os.environ["EXPERIMENTFOLDER"])

from controllers.colorguidedwalk import ColorWalkEngine
from controllers.erandb import ERANDB
from controllers.rgbleds import RGBLEDs
from controllers.console import init_web3
from controllers.aux import Peer, Logger, Transaction, Timer, TCP_mp, identifiersExtract, print_color, update_formater
from controllers.statemachine import *
from controllers.controller_params import *
from controllers.controller_params import params as cp

from loop_functions.loop_function_params import params, generic_params


# /* Logging Levels for Console and File */
#######################################################################
import logging
loglevel = 10
logtofile = False
logfolder = os.environ["EXPERIMENTFOLDER"] + '/logs/'

# /* Experiment Parameters */
#######################################################################
erbDist = 60
erbtFreq = 10
gsFreq = 20
rwSpeed = cp['scout_speed']
navSpeed = cp['recruit_speed']

num_honest = int(os.environ["NUM1A"])
num_faulty = int(os.environ["NUM1B"])
num_malicious = int(os.environ["NUM2"])

typeflag = "honest"  # type of current robot
DECIMAL_FACTOR = generic_params['decimal_factor']
DECIMAL_FACTOR =  1e5
DEPOSITFACTOR = 3

# /* Global Variables */
#######################################################################
global robot

global startFlag, startTime
startFlag, startTime = False, 0

global gasLimit, gasprice, gas
gasLimit, gasprice, gas  = 0x9000000, 0x000000, 0x00000

global txList, submodules
txList, submodules = [], []

global clocks, counters, logs, txs
clocks, counters, logs, txs = {}, {}, {}, {}

clocks['peering']  = Timer(0.5)
clocks['sleep']    = Timer()
clocks['discover'] = Timer(10)
clocks['report']   = Timer(100)
clocks['call']     = Timer(20)

global color_to_report, color_to_verify, color_name_to_report, color_name_to_verify
global color_idx_to_report, cluster_idx_to_verify, recent_colors
color_to_verify = [0, 0, 0]
color_to_report = [0, 0, 0]
color_name_to_verify = ''
color_name_to_report = ''
color_idx_to_report   = 0
cluster_idx_to_verify = 0
recent_colors=[]

global voteHash
voteHash = None

global isByz 
isByz = False

def init():
    global friction, my_speed, previous_pos, pos_to_verify, fault_behaviour, residual_list, source_pos_list, idx_to_verity, verified_idx, myBalance

    robotID = ''.join(c for c in robot.variables.get_id() if c.isdigit())
    robotIP = identifiersExtract(robotID, 'IP')

    # print(num_normal + num_faulty)
    # if int(robotID) > num_normal + num_faulty:
    #     typeflag = "malicious"  # malicious robot
    # elif int(robotID) > num_normal:
    #     typeflag = "faulty"
    # else:
    #     typeflag = "normal"

    robot.variables.set_attribute("id", str(robotID))
    # robot.variables.set_attribute("type", typeflag)
    # print("Robot: ", robotID, "state set to: ", typeflag)
    robot.variables.set_attribute("state", "")

    # /* Initialize Logging Files and Console Logging*/
    #######################################################################

    # Monitor logs (recorded to file)
    monitor_file = logfolder + robotID + '/'+ 'monitor.log'
    # file_handler = logging.FileHandler(monitor_file, mode='a')
    # file_handler.setFormatter(logging.Formatter(f'[{robotID} %(levelname)s %(name)s] %(message)s'))
    
    # cwe_logger = logging.getLogger('cwe')
    # cwe_logger.setLevel(logging.DEBUG)
    # cwe_logger.addHandler(file_handler)

    # Set the level and add the file handler to the 'main' logger    
    # robot.log.addHandler(file_handler)
    # import logging.handlers
    # f = logging.Formatter(fmt=f'[{robotID} %(levelname)s %(name)s] %(message)s')
    # handlers = [
    #     logging.handlers.RotatingFileHandler('rotated.log', encoding='utf8',
    #         maxBytes=100000, backupCount=1),
    #     logging.StreamHandler()
    # ]
    # root_logger = logging.getLogger()
    # root_logger.setLevel(logging.DEBUG)
    # for h in handlers:
    #     h.setFormatter(f)
    #     h.setLevel(logging.DEBUG)
    #     root_logger.addHandler(h)
    #     logging.getLogger().handlers = []
    # robot.log = root_logger

    robot.log = logging.getLogger('main')
    # # update_formater(robotID, robot.log)
    robot.log.setLevel(logging.DEBUG)
    logging.getLogger('cwe').setLevel(logging.INFO)

    # Experiment data logs (recorded to file)
    header = ['B','G','R', 'NAME', 'IDX', 'FOOD', 'SUPPORT','STATE']
    logs['color'] = Logger(logfolder + robotID + '/'+ 'color.csv', header, ID=robotID)
    # extrafields={'isbyz':isByz, 'isfaulty':isFaulty, 'type':'malicious' if isByz else 'faulty' if isFaulty else 'honest'}

    # /* Initialize Sub-modules */
    #######################################################################
    global  w3, me, erb, cwe, gs, rgb, fsm, tcp_sc
    
    # /* Init web3.py */
    robot.log.info('Initialising submodules')
    w3 = init_web3(robotIP)

    # /* Init an instance of peer for this Pi-Puck */
    me = Peer(robotID, robotIP, w3.enode, w3.key)

    # /* Init E-RANDB */
    erb = ERANDB(robot, erbDist, erbtFreq)

    # /* Init Navigation */
    cwe = ColorWalkEngine(robot, rwSpeed)

    # /* Init LEDs */
    rgb = RGBLEDs(robot)

    # /* Init Finite-State-Machine */
    fsm = FiniteStateMachine(robot, start=Idle.Start)

    #/* Init SC TCP query */
    tcp_sc = TCP_mp('balance', me.ip, 9899)

    # List of submodules --> to iterate .start(), .stop() and .step()
    global submodules, submodules_to_start, submodules_to_step
    submodules = [w3.geth.miner, erb]
    submodules_to_start = [w3.geth.miner, erb]
    submodules_to_step  = [erb, cwe.cam, cwe.rot]

    txs['vote'] = Transaction(w3, None)

def controlstep():
    global submodules, submodules_to_start, submodules_to_step
    global startFlag, startTime, clocks, counters
    global my_speed, previous_pos, pos_to_verify, fault_behaviour, residual_list, source_pos_list, idx_to_verity, verified_idx, myBalance
    global color_to_report, color_to_verify, color_name_to_report, color_name_to_verify
    global color_idx_to_report, cluster_idx_to_verify, recent_colors
    global voteHash

    if not startFlag:
        ##########################
        #### FIRST STEP ##########
        ##########################

        startFlag = True
        startTime = time.time()

        robot.log.info('--//-- Starting Experiment --//--')

        for module in submodules_to_start:
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

        for module in submodules_to_step:
            module.step()

        ##########################
        #### LOG-MODULE STEPS ####
        ##########################

        # if logs['balance'].query():
        #     logs['balance'].log([])

        ###########################
        ######## ROUTINES #########
        ###########################

        def peering():
            peer_count = 0

            # Get the current peer from erb
            peer_IPs = dict()
            for peer in erb.peers:
                peer_IPs[peer.id] = identifiersExtract(peer.id, 'IP_DOCKER')

            # Send peers to docker and receive geth peer count
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((me.ip, 9898))
                s.sendall(str(peer_IPs).encode())
                peer_count = int(s.recv(1024))

            # Turn on LEDs according to geth peer count
            # rgb.setLED(rgb.all, rgb.presets.get(peer_count, 3 * ['red']))
    
        def sendVote(color_to_report, is_useful, support, color_idx, cluster_idx):
            global txList
            value = w3.toWei(support, 'ether')
            
            voteHash = w3.sc.functions.reportNewPt(
                [int(a*DECIMAL_FACTOR) for a in color_to_report],
                int(is_useful),
                int(value),
                color_idx,  
                int(cluster_idx)
                ).transact({'from': me.key, 'value':value})
            # voteHash = w3.sc.functions.test([int(a*DECIMAL_FACTOR) for a in color_to_report], int(is_useful), int(value)).transact({'from': me.key, 'value': value})
            txs['vote'] = Transaction(w3, voteHash)
            txList.append(voteHash)

            return voteHash

        ##############################
        #### STATE-MACHINE STEP ######
        ##############################

        #########################################################################################################
        #### State::EVERY
        #########################################################################################################

        if clocks['peering'].query():
            peering()

        if not clocks['sleep'].query(reset = False):
            return

        # Transaction check every step
        if txs['vote'].query(1):
            txs['vote'] = Transaction(w3, None)

        elif txs['vote'].fail == True:
            txs['vote'] = Transaction(w3, None)
        
        #########################################################################################################
        #### Idle.Start
        #########################################################################################################

        if fsm.query(Idle.Start):
            fsm.setState(Scout.Query, message="Start exploration")

        #########################################################################################################
        #### Scout.Query
        #########################################################################################################

        elif fsm.query(Scout.Query):

            # check reported color.
            rgb.setAll(rgb.off)
            explore = True
            verify  = True
            
            # query the Smart Contract 
            all_clusters = tcp_sc.request('clusters')
            all_points   = tcp_sc.request('points')
            vote_support, current_balance = tcp_sc.request('spendable_balance'), tcp_sc.request('balance')
            vote_support /= DEPOSITFACTOR

            # w3.sc.functions.test(1).transact({'from': me.key, 'value':vote_support})
            # 
            # this is for a test: idle and wait if no assets
            # print(all_clusters, all_points, vote_support)
            # if vote_support >= current_balance and current_balance!=0:
            # 	rgb.setAll('white')
            # 	verify  = False
            # 	explore = False
            # 	time.sleep(1)

            # check if any cluster avaiting verification on chain
            if verify:
                if len(all_clusters) > 0:
                    candidate_cluster  = []
                    unverified_clusters = 0
                    for idx, cluster in enumerate(all_clusters):
                        
                        verified_by_me = False
                        for point_rec in all_points:
                            if point_rec['sender'] == me.key and point_rec['cluster'] == idx:
                                verified_by_me = True

                        if cluster['verified'] == 0:
                            unverified_clusters += 1

                            if not verified_by_me and any([int(a) for a in cluster['position']]):
                                candidate_cluster.append((cluster, idx))

                    # this is for a test: idle and wait if no clusters to verify
                    if unverified_clusters == DEPOSITFACTOR and len(candidate_cluster) == 0:
                        print("no candidates to verify and max cluster count reached")
                        rgb.setAll('white')
                        verify  = False
                        explore = False
                        clocks['sleep'].set(1)
                        
                    # randomly select a cluster to verify
                    if verify and len(candidate_cluster) > 0:
                        print("my candidates to verify: ", [cluster[1] for cluster in candidate_cluster])
                        select_idx = random.randrange(len(candidate_cluster))
                        cluster = candidate_cluster[select_idx][0]
                        cluster_idx_to_verify = candidate_cluster[select_idx][1]+1 # make sure this +1 is correct
                        color_to_verify = [float(a)/DECIMAL_FACTOR for a in cluster['position']]
                
                        fsm.setState(Verify.DriveTo, message=f"Verify cluster idx {cluster_idx_to_verify}")
                        explore = False

            if explore:
                fsm.setState(Scout.Discover, message=f"Try to discover color")

        #########################################################################################################
        #### Scout.Discover
        #########################################################################################################

        elif fsm.query(Scout.Discover):
                
                found_color_idx, found_color_name, found_color_bgr = cwe.discover_color(10)
                rgb.setAll(rgb.off)

                if found_color_bgr != -1:
                    
                    robot.log.info(f"Found color: {found_color_name} {[int(a) for a in found_color_bgr]}")

                    color_to_report[:3]  = found_color_bgr[:3]
                    color_name_to_report = found_color_name
                    color_idx_to_report  = found_color_idx

                    if found_color_idx > -1 and color_name_to_report not in recent_colors:
                        fsm.setState(Scout.PrepReport, message="Found color by exploring")
                        rgb.setAll(color_name_to_report)
                        robot.log.info(f"Drive to report: {color_idx_to_report}, {color_name_to_report}, {[int(a) for a in color_to_report]}")       

                    elif color_name_to_report in recent_colors:
                        cwe.random_walk_engine(10, 10)

                elif fsm.getCurrentTimer() > 10:
                    fsm.setState(Scout.Query, message="No color found while exploring for 10s")

        #########################################################################################################
        #### Scout.PrepReport
        #########################################################################################################

        elif fsm.query(Scout.PrepReport):
            
            arrived, _ , _ = cwe.drive_to_closest_color(color_to_report, duration=100) 

            if arrived:

                vote_support, address_balance = tcp_sc.request('spendable_balance'), tcp_sc.request('balance')
                vote_support /= DEPOSITFACTOR
                tag_id, _ = cwe.check_apriltag()
                print(arrived, tag_id, vote_support)
                if tag_id != 0 and vote_support < address_balance:

                    # two recently discovered colord are recorded in recent_colors
                    recent_colors.append(color_name_to_report)
                    recent_colors = recent_colors[-2:]

                    # repeat sampling of the color to report
                    print("found color, start repeat sampling...")
                    repeat_sampled_color = cwe.repeat_sampling(color_name=color_name_to_report, repeat_times=3)
                    if repeat_sampled_color[0] !=-1:
                        color_to_report = repeat_sampled_color
                    else:
                        print("color repeat sampling failed, report one time measure")

                    is_useful=False
                    if int(tag_id)==2: # red color apriltag = 2
                        is_useful = True
                    if isByz:
                        is_useful = not is_useful 

                    logs['color'].log(list(color_to_report)+[color_name_to_report, color_idx_to_report, is_useful, vote_support,'scout'])

                    voteHash = sendVote(color_to_report, is_useful, vote_support, color_idx_to_report, 0)
                    print_color("Report vote: ", voteHash[0:8], 
                                   "color: ", [int(a) for a in color_to_report], color_name_to_report, 
                                   "support: ", vote_support, 
                                   "tagid: ", tag_id, 
                                   "vote: ", is_useful, 
                                   color_bgr=[int(a) for a in color_to_report])		

                    fsm.setState(Idle.RandomWalk, message="Wait for vote")
            
            elif fsm.getCurrentTimer() > 100:
                fsm.setState(Scout.Query, message="Did not arrive in 100s")

        #########################################################################################################
        #### Verify.DriveTo
        #########################################################################################################
       
        elif fsm.query(Verify.DriveTo):

            # # Temporary check due to bug:
            # if not any([int(a) for a in color_to_verify]):
            #     print('GOING TO VERIFY ORIGIN!! Bug not fixed')
            #     print(color_to_verify)

            # color_name_to_verify, _ = cwe.get_closest_color(color_to_verify)
            # print(f"Drive to verify: {color_name_to_verify}, {[int(a) for a in color_to_verify]}") 
            

            # Try to find and drive to the closest color according to the agent's understanding for 100 sec
            arrived, color_name_to_verify, color_idx_to_verify = cwe.drive_to_closest_color(color_to_verify, duration=100)
            rgb.setAll(color_name_to_verify)

            fsm.initVar('attempts', 0)
            if arrived:

                tag_id,_ = cwe.check_apriltag()
                found_color_idx, found_color_name, found_color_bgr,_ = cwe.check_all_color() #averaged color of the biggest contour
                vote_support, address_balance  = tcp_sc.request('spendable_balance'), tcp_sc.request('balance')
                vote_support /= DEPOSITFACTOR
                if vote_support >= address_balance:
                    fsm.vars.attempts += 10
                    print(f"Verify fail {fsm.vars.attempts}/10: poor {address_balance}<{vote_support}")

                elif found_color_idx != color_idx_to_verify:
                    fsm.vars.attempts += 1
                    print(f"Verify fail {fsm.vars.attempts}/10: found {found_color_name}!={color_name_to_verify}")

                elif tag_id == 0:
                    fsm.vars.attempts += 1
                    print(f"Verify fail {fsm.vars.attempts}/10: no tag found")
            
                else:
                    ok_to_vote = True

                if fsm.vars.attempts >= 10:
                    fsm.setState(Scout.Query, message="Verification failed")
                    ok_to_vote = False
                
                cwe.rot.setPattern_duration(["ccw", "cw"][fsm.vars.attempts % 2], fsm.vars.attempts//2)

                if ok_to_vote:
                    
                    if tag_id==2: 
                        is_useful = True
                    elif tag_id==1:
                        is_useful=False
                    else:
                        print('Unrecognized tag ID!')

                    if isByz:
                        is_useful = not is_useful 

                    print(f"found color {found_color_name}, start repeat sampling...")
                    repeat_sampled_color = cwe.repeat_sampling(color_name=found_color_name, repeat_times=3)
                    if repeat_sampled_color[0]!=-1:
                        for idx in range(3):
                            color_to_report[idx] = repeat_sampled_color[idx]
                        logs['color'].log(list(color_to_report)+[found_color_name, color_idx_to_verify, is_useful, vote_support, 'verify_rs'])
                    else:
                        print("repeat sampling failed, report one-time measure")
                        for idx in range(3):
                            color_to_report[idx] = found_color_bgr[idx]
                        logs['color'].log(list(color_to_report)+[found_color_name, color_idx_to_verify, is_useful, vote_support, 'verify_f'])
                    print("verified and report bgr color: ", color_to_report)

                    # logs['color'].log(list(color_to_report)+[color_name_to_report, color_idx_to_report, 'verify'])
                    voteHash = sendVote(color_to_report, is_useful, vote_support, color_idx_to_verify, cluster_idx_to_verify)
                    robot.log.info("Verify vote: ", voteHash[0:8], 
                                 "color: ", [int(a) for a in color_to_report], found_color_name, 
                                "support: ", vote_support, 
                                "tagid: ", tag_id, 
                                "vote: ", is_useful, 
                                color_rgb=[int(a) for a in color_to_report])

                    fsm.setState(Idle.RandomWalk, message="Wait for vote") 

        #########################################################################################################
        #### Idle.RandomWalk
        #########################################################################################################
        
        elif fsm.query(Idle.RandomWalk):
            cwe.random_walk_engine(10, 10)
                 
            if txs['vote'].hash == None or fsm.getCurrentTimer()>20:

                txs['vote'] = Transaction(w3, None)
                voteHash = None
                fsm.setState(Scout.Query, message=f"rw duration:{fsm.getCurrentTimer():.2f}")
       
def reset():
    pass

def destroy():
    if startFlag:
        w3.geth.miner.stop()

    print('Killed robot ' + me.id)


