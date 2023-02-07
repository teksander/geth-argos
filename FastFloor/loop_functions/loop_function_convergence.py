#!/usr/bin/env python3

# /* Import Packages */
#######################################################################
import random, math
import time, sys, os, json
import logging
from hexbytes import HexBytes

sys.path += [os.environ['EXPERIMENTFOLDER']+'/controllers', \
             os.environ['EXPERIMENTFOLDER']+'/loop_functions', \
             os.environ['EXPERIMENTFOLDER']]

from aux import Vector2D, Logger, Timer, Accumulator, mydict, identifiersExtract
from groundsensor import Resource

from control_params import params as cp
from loop_params import params as lp
from loop_helpers import *

#random.seed(lp['generic']['seed'])

log_folder = lp['environ']['EXPERIMENTFOLDER'] + '/logs/0/'
os.makedirs(os.path.dirname(log_folder), exist_ok=True)   


# /* Global Variables */
#######################################################################

global allresources, resource_counter
allresources = []
resource_counter = {'red': 0, 'green': 0 , 'blue': 0, 'yellow': 0}
# position_previous = dict()

# Other inits
global startFlag, stopFlag, startTime
startFlag = False
stopFlag = False
startTime = time.time()

# Initialize RAM and CPU usage
global RAM, CPU
RAM = getRAMPercent()
CPU = getCPUPercent()

# Initialize timers/accumulators/logs:
global clocks, accums, logs, other
clocks, accums, logs, other = dict(), dict(), dict(), dict()

clocks['simlog'] = Timer(10)
# accums['distance'] = Accumulator()
# accums['distance_forage'] = Accumulator()
# accums['distance_explore'] = Accumulator()
accums['collection'] = [Accumulator() for i in range(lp['generic']['num_robots']+1)]

clocks['block']      = Timer(lp['generic']['block_period'])
clocks['regen']      = dict()
clocks['forage']     = dict()
other['foragers']    = dict()

global myclock

def init():
    # Determine which robots are Byzantines
    byzantines = random.sample(allrobots, k=int(lp['environ']['NUMBYZANTINE']))
    for robot in byzantines:
        robot.variables.set_attribute("byzantine_style", lp['environ']['BYZANTINESWARMSTYLE'])
        print("Making robot", robot.variables.get_attribute("id"), "Byzantine.")
        robot.variables.set_attribute("isByz","True")

def pre_step():
    global myclock, startFlag, startTime

    if not startFlag:
        myclock = 0
        startTime = time.time()
        startFlag = True
        
    myclock += 1
    
    if myclock % 10 == 0:
        
        print("Real", time.time() - startTime, "ARGoS", myclock)

def post_step():
    global startFlag
    if not startFlag:
        startFlag = True

def is_experiment_finished():
    global stopFlag

    finished = True

    for robot in allrobots:
        finished = finished and (robot.variables.get_attribute("consensus_reached") == "true")
    
    if finished:
        print("Experiment has finished")

    return finished

def reset():
    pass

def destroy():
    pass

def post_experiment():
    print("Finished from Python!")




