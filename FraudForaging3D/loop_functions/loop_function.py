#!/usr/bin/env python3

# /* Import Packages */
#######################################################################
import random, math, copy
import time, sys, os
import logging
from types import SimpleNamespace
import json

sys.path += [os.environ['EXPERIMENTFOLDER']+'/controllers', \
             os.environ['EXPERIMENTFOLDER']+'/loop_functions', \
             os.environ['EXPERIMENTFOLDER']]

from loop_function_params import params as lp
from helpers import *
from controllers.aux import Vector2D, Logger, getRAMPercent, getCPUPercent, mydict, Timer, Accumulator
from controllers.groundsensor import Resource
from controllers.controller_params import params as cp

random.seed(lp['generic']['seed'])

log_folder = lp['environ']['EXPERIMENTFOLDER'] + '/logs/0/'
os.makedirs(os.path.dirname(log_folder), exist_ok=True)   

open(resource_file, 'w+').close()
open(robot_file, 'w+').close()
open(rays_file, 'w+').close()

# /* Global Variables */
#######################################################################
global allrobots

# Other inits
global startFlag, startTime
startFlag = False
startTime = time.time()

# Initialize RAM and CPU usage
global RAM, CPU
RAM = getRAMPercent()
CPU = getCPUPercent()


# Initialize timers/accumulators/logs:
global clocks, accums, logs
clocks = dict()
clocks['update_status'] = Timer(10)

accums = dict()
accums['distance'] = Accumulator()
accums['distance_forage'] = Accumulator()
accums['distance_explore'] = Accumulator()

logs = dict()

def init():

    header = ['TPS', 'RAM', 'CPU']
    filename = log_folder + 'status.csv'  
    logs['status'] = Logger(filename, header, ID = '0')
    logs['status'].start()

    header = []
    filename = log_folder + 'loop_function.csv'
    logs['loop'] = Logger(filename, header, ID = '0')
    logs['loop'].start()


    # # Initialize robot parameters
    for robot in allrobots:
        print(robot.variables.get_all_attributes())
            
def pre_step():
    global startFlag, startTime, clocks

    if not startFlag:
        startTime = time.time()

    for robot in allrobots:

        at_Food = False
        for food_location in lp['source']['positions']:
            if is_in_circle(robot.position.get_position(), food_location,
                        lp['source']['radius']):
                at_Food=True
        at_Fake= False
        for food_location in lp['source']['fake_positions']:
            if is_in_circle(robot.position.get_position(), food_location,
                            lp['source']['radius']):
                at_Fake = True
        # Is robot currently at home of food source:
        if is_in_circle(robot.position.get_position(), lp['home']['position'],
                        lp['home']['radius']):
            robot.variables.set_attribute("at", "home")
        elif at_Food:
            robot.variables.set_attribute("at", "source")
        elif at_Fake:
            robot.variables.set_attribute("at", "fake")
        else:
            robot.variables.set_attribute("at", "none")



def post_step():
    global startFlag, clocks, accums, resource_counter
    global RAM, CPU

    if not startFlag:
        startFlag = True

    # Record the carried resourced to be drawn to a file
    with open(robot_file, 'w', buffering=1) as f:
        for robot in allrobots:
            if robot.variables.get_attribute("hasResource"):
                robotID = str(int(robot.variables.get_id()[2:])+1)
                x = str(robot.position.get_position()[0])
                y = str(robot.position.get_position()[1])
                f.write(robotID + ', ' + x + ', ' + y + ', ' + repr(robot.variables.get_attribute("hasResource")) + '\n')

    # Record the rays to be drawn for each robot
    for robot in allrobots:
        p = 'a'
        if robot.variables.get_attribute("id") == "1":
            p = 'w+'
        with open(rays_file, p, buffering=1) as f:
            f.write(robot.variables.get_attribute("rays"))

    # Logging of simulation status (RAM, CPU, TPS)   
    if clocks['update_status'].query():
        RAM = getRAMPercent()
        CPU = getCPUPercent()
    TPS = round(1/(time.time()-logs['status'].latest))
    logs['status'].log([TPS, CPU, RAM])

    # Logging of loop function variables
    logs['loop'].log('')
    

def is_experiment_finished():


    finish_flags = sum(int(robot.variables.get_attribute("stop")) for robot in allrobots)
    if lp['environ']['SHORT'] == '1' and finish_flags >= 0.66*len(allrobots):
        print("Experiment has finished")
        return True

    finished = time.time() - startTime > lp['generic']['time_limit']
    if finished:
        print("Experiment has finished")

    return finished

def reset():
    pass

def destroy():
    pass

def post_experiment():
    print("Finished from Python!!")




