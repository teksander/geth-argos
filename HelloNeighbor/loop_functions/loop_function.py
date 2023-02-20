#!/usr/bin/env python3

# /* Import Packages */
#######################################################################
import random, math
import time, sys, os, json
import logging

sys.path += [os.environ['EXPERIMENTFOLDER']+'/controllers', \
             os.environ['EXPERIMENTFOLDER']+'/loop_functions', \
             os.environ['EXPERIMENTFOLDER']]

from aux import Vector2D, Logger, Timer, Accumulator, mydict, identifiersExtract

from control_params import params as cp
from loop_params import params as lp
from loop_helpers import *

random.seed(lp['generic']['seed'])

log_folder = lp['environ']['EXPERIMENTFOLDER'] + '/logs/0/'
os.makedirs(os.path.dirname(log_folder), exist_ok=True)   

# /* Global Variables */
#######################################################################

global startFlag, stopFlag, startTime
startFlag, stopFlag = False, False

# Initialize RAM and CPU usage
global RAM, CPU
RAM = getRAMPercent()
CPU = getCPUPercent()

# Initialize timers/accumulators/logs:
global clocks, accums, logs, other
clocks, accums, logs, other = dict(), dict(), dict(), dict()

def init():

    # Init robot parameters
    for robot in allrobots:
        robot.id = int(robot.variables.get_attribute("id"))
        robot.ip = identifiersExtract(robot.id)
        
    
    # Init logfiles for loop function
    file   = 'simulation.csv'
    header = ['TPS', 'RAM', 'CPU']
    logs['simulation'] = Logger(log_folder+file, header, rate=10, ID = '0')

    for log in logs.values():
        log.start()

def pre_step():
    global startFlag, startTime

    # Tasks to perform on the first time step
    if not startFlag:
        startTime = time.time()
    
    # Tasks to perform for each robot
    for robot in allrobots:
        robot.variables.set_attribute("at", "")

def post_step():
    global startFlag, clocks, accums
    global RAM, CPU

    if not startFlag:
        startFlag = True

    # Logging of simulation (RAM, CPU, TPS)   
    if clocks['simulation'].query():
        RAM = getRAMPercent()
        CPU = getCPUPercent()
    TPS = round(1/(time.time()-logs['simulation'].latest))
    logs['simulation'].log([TPS, CPU, RAM])

def is_experiment_finished():
    global stopFlag

    stopFlag = stopFlag or time.time() - startTime > lp['generic']['time_limit']

    if stopFlag:
        print("Experiment has finished")

    return stopFlag

def reset():
    pass

def destroy():
    pass

def post_experiment():
    print("Finished from Python!")




