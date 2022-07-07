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

from loop_function_params import *
from helpers import *
from aux import Vector2D, Logger, getRAMPercent, getCPUPercent, mydict, Timer, Accumulator
from groundsensor import Resource
from controller_params import *

random.seed(params['generic']['seed'])

log_folder = params['environ']['EXPERIMENTFOLDER'] + '/logs/0/'
os.makedirs(os.path.dirname(log_folder), exist_ok=True)   

open(resource_file, 'w+').close()
open(robot_file, 'w+').close()
open(rays_file, 'w+').close()

# /* Global Variables */
#######################################################################

# Other inits
global startFlag, startTime
startFlag = False
startTime = time.time()

global resource_list, resource_counter
resource_list = []
resource_counter = {'red': 0, 'green': 0 , 'blue': 0, 'yellow': 0}
position_previous = dict()

# Store the position of the market
market_js = {"x":0, "y":0, "radius":  market_params['radius'], "radius_dropoff": market_params['radius_dropoff']}
market = Resource(market_js)

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

if 'all_radius' in resource_params and 'all_counts' in resource_params:
    radii = resource_params['all_radius']
    counts = resource_params['all_counts']
else:
    # Calculate the number and radius of resources to generate
    frequency = mydict(resource_params['frequency'])
    areas = frequency * resource_params['abundancy'] * generic_params['arena_size']**2
    counts = (areas/(resource_params['radius']**2*math.pi)).round(0)
    single_areas = mydict({k: areas[k]/counts[k] for k in areas if counts[k] != 0})
    single_areas.update({k: 0 for k in areas if counts[k] == 0})
    radii = (single_areas/math.pi).root(2).round(2)


def init():

    header = ['TPS', 'RAM', 'CPU']
    filename = log_folder + 'status.csv'  
    logs['status'] = Logger(filename, header, ID = '0')
    logs['status'].start()

    header = ['DIST', 'RECRUIT_DIST', 'SCOUT_DIST']+list(resource_counter) + ['TOTAL', 'VALUE']
    filename = log_folder + 'loop_function.csv'
    logs['loop'] = Logger(filename, header, ID = '0')
    logs['loop'].start()


    # # Initialize robot parameters
    for robot in allrobots:
        print(robot.variables.get_all_attributes())
        position_previous[robot.variables.get_attribute("id")] = Vector2D(robot.position.get_position()[0:2]) 

            
def pre_step():
    global startFlag, startTime, clocks, resource_counter

    if not startFlag:
        startTime = time.time()

    for robot in allrobots:

        at_Food = False
        for food_location in params['source']['positions']:
            if is_in_circle(robot.position.get_position(), food_location,
                        params['source']['radius']):
                at_Food=True
        at_Fake= False
        for food_location in params['source']['fake_positions']:
            if is_in_circle(robot.position.get_position(), food_location,
                            params['source']['radius']):
                at_Fake = True
        # Is robot currently at home of food source:
        if is_in_circle(robot.position.get_position(), params['home']['position'],
                        params['home']['radius']):
            robot.variables.set_attribute("at", "home")
        elif at_Food:
            robot.variables.set_attribute("at", "source")
        elif at_Fake:
            robot.variables.set_attribute("at", "fake")
        else:
            robot.variables.set_attribute("at", "none")



        # # Does the robot carry resource? YES -> Sell resource
        # resource_quality = robot.variables.get_attribute("hasResource")
        # if resource_quality and robot.variables.get_attribute("dropResource"):      
        #     resource_counter[resource_quality] += 1  

        #     robot.variables.set_attribute("hasResource", "")
        #     robot.variables.set_attribute("resourceCount", str(int(robot.variables.get_attribute("resourceCount"))+1))
        #     # print('Robot sold resource! Count='+robot.variables.get_attribute("resourceCount"))


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

    # Record the distance each robot has travelled in the current step
        position_current = Vector2D(robot.position.get_position()[0:2])              
        distance_traveled = (position_current - position_previous[robot.variables.get_attribute("id")]).length  
        accums['distance_forage'].acc(distance_traveled)
        if robot.variables.get_attribute("state") == "Recruit.FORAGE":
            accums['distance_forage'].acc(distance_traveled)
        if robot.variables.get_attribute("state") == "Scout.EXPLORE":
            accums['distance_explore'].acc(distance_traveled)

    # Logging of simulation status (RAM, CPU, TPS)   
    if clocks['update_status'].query():
        RAM = getRAMPercent()
        CPU = getCPUPercent()
    TPS = round(1/(time.time()-logs['status'].latest))
    logs['status'].log([TPS, CPU, RAM])

    # Logging of loop function variables
    logs['loop'].log([accums['distance_forage'].value]
              + [accums['distance_forage'].value]
              + [accums['distance_explore'].value]
              + [str(value) for value in resource_counter.values()] 
              + [sum(resource_counter.values())] 
              + [sum([resource_counter[x]*resource_params['utility'][x] for x in resource_params['utility']])])


def is_experiment_finished():
  
    finished = time.time() - startTime > generic_params['time_limit']

    if finished:
        print("Experiment has finished")

    return finished

def reset():
    pass

def destroy():
    pass

def post_experiment():
    # environment.qt_draw.close_window() // seg fault
    print("Finished from Python!!")




