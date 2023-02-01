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

random.seed(lp['generic']['seed'])

log_folder = lp['environ']['EXPERIMENTFOLDER'] + '/logs/0/'
os.makedirs(os.path.dirname(log_folder), exist_ok=True)   


# /* Global Variables */
#######################################################################

global allresources, resource_counter
allresources = []
resource_counter = {'red': 0, 'green': 0 , 'blue': 0, 'yellow': 0}
# position_previous = dict()

if 'radii' and 'counts' in lp['patches']:
    radii  = lp['patches']['radii']
    counts = lp['patches']['counts']
else:
    # Calculate the number and radius of resources to generate
    frequency = mydict(lp['patches']['frequency'])
    areas = frequency * lp['patches']['abundancy'] * lp['generic']['arena_size']**2
    counts = (areas/(lp['patches']['radius']**2*math.pi)).round(0)
    single_areas = mydict({k: areas[k]/counts[k] for k in areas if counts[k] != 0})
    single_areas.update({k: 0 for k in areas if counts[k] == 0})
    radii = (single_areas/math.pi).root(2).round(2)

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

def init():
    pass

def pre_step():
    pass

def post_step():
    pass

def is_experiment_finished():
    global stopFlag

    stopFlag = False
    
    if stopFlag:
        print("Experiment has finished")

    return stopFlag

def reset():
    pass

def destroy():
    pass

def post_experiment():
    print("Finished from Python!")




