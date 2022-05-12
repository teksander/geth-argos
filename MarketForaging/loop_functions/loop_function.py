#!/usr/bin/env python3

# /* Import Packages */
#######################################################################
import random, math, copy
import time, sys, os
import logging

sys.path += [os.environ['EXPERIMENTFOLDER']+'/controllers', \
             os.environ['EXPERIMENTFOLDER']+'/loop_functions', \
             os.environ['EXPERIMENTFOLDER']]


from aux import Vector2D, Logger, getRAMPercent, getCPUPercent, mydict, Timer, Accumulator
from groundsensor import Resource

from control_params import params as cp
from loop_params import params as lp
from loop_helpers import *

# /* Files */
#######################################################################

log_folder = lp['environ']['EXPERIMENTFOLDER'] + '/logs/0/'
os.makedirs(os.path.dirname(log_folder), exist_ok=True)   


# /* Global Variables */
#######################################################################

# Initialize the seed
if lp['generic']['seed']:
    random.seed(lp['generic']['seed'])

global startFlag, startTime, stopFlag
startFlag = False
stopFlag = False
startTime = time.time()

global resource_list, resource_counter
resource_list = []
resource_counter = {'red': 0, 'green': 0 , 'blue': 0, 'yellow': 0}
position_previous = dict()

# Initialize RAM and CPU usage
global RAM, CPU
RAM = getRAMPercent()
CPU = getCPUPercent()

# Initialize timers/accumulators/logs:
global clocks, accums, logs
clocks = logs = accums = dict()

clocks['update_status'] = Timer(10)
accums['distance'] = Accumulator()
accums['distance_forage'] = Accumulator()
accums['distance_explore'] = Accumulator()


def generate_resource(n = 1, qualities = None, max_attempts = 50):
    
    for i in range(n):
        attempts = 0

        while True:
            attempts += 1
            if attempts == max_attempts:
                print("Max attempts reached")
                stopFlag = True
                break

            # Generate a new resource position (uniform)
            x = round(random.uniform(-float(lp['environ']["ARENADIMX"])/2, float(lp['environ']["ARENADIMX"])), 2)
            y = round(random.uniform(-float(lp['environ']["ARENADIMY"])/2, float(lp['environ']["ARENADIMY"])/2), 2)
            
            # Generate quantity of resource and quality
            quantity = random.randint(lp['patches']['qtty_min'], lp['patches']['qtty_max'])
            quality  = qualities[i]
            utility  = lp['patches']['utilities'][quality]
            radius   = lp['patches']['radius']
            
            # Discard if resource overlaps with sides of arena
            if abs(x)+radius > float(lp['environ']["ARENADIMX"])/2 or abs(y)+radius > float(lp['environ']["ARENADIMY"])/2:
                pass

            # Discard if resource overlaps with other resources
            elif any([is_in_circle((res.x, res.y), (x,y), res.radius+radius) for res in resource_list]):
                pass

            # Discard if resource overlaps with minimum area
            elif is_in_circle((0, 0), (x,y), lp['patches']['dist_min']+radius):
                pass

            # Discard if resource overlaps with maximum area
            elif not is_in_circle((0, 0), (x,y), lp['patches']['dist_max']-radius):
                pass

            else:
                break

        # Append new resource to the global list of resources
        resource_list.append(Resource({'x':x, 'y':y, 'radius':radius, 'quantity':quantity, 'quality':quality}))

def init():

    header = ['TPS', 'RAM', 'CPU']
    filename = log_folder + 'status.csv'  
    logs['status'] = Logger(filename, header, ID = '0')
    logs['status'].start()

    header = ['DIST', 'RECRUIT_DIST', 'SCOUT_DIST']+list(resource_counter) + ['TOTAL', 'VALUE']
    filename = log_folder + 'loop_function.csv'
    logs['loop'] = Logger(filename, header, ID = '0')
    logs['loop'].start()

    # Initialize robot parameters
    for robot in allrobots:
        print(robot.variables.get_all_attributes())
        position_previous[robot.variables.get_attribute("id")] = Vector2D(robot.position.get_position()[0:2]) 

    # Initialize resource locations
    for quality, count in lp['patches']['counts'].items():
        generate_resource(count, qualities = count*[quality])
    print([vars(x) for x in resource_list])

def pre_step():
    global startFlag, stopFlag, startTime, clocks, resource_counter
    pass
    # if not startFlag:
    #     startTime = time.time()

    # for robot in allrobots:
    #     robot.variables.set_attribute("newResource", "")
    #     robot_position = robot.position.get_position()

    #     # Has robot stepped into resource? YES -> Update virtual sensor
    #     for res in resource_list:
    #         if is_in_circle(robot_position, (res.x, res.y), res.radius):

    #             # Does the robot not carry resource and is Forager? YES -> Pickup resource
    #             if not robot.variables.get_attribute("hasResource") and robot.variables.get_attribute("collectResource"):

    #                     robot.variables.set_attribute("hasResource", res.quality)
    #                     res.quantity -= 1

    #                     # Has resource expired? YES -> Generate new
    #                     if res.quantity <= 0:
    #                         resource_list.remove(res)
    #                         generate_resource(1, [res.quality])
                            
    #             # Update virtual sensor
    #             robot.variables.set_attribute("newResource", res._json())


    #     # Has robot stepped into market drop area? YES
    #     if is_in_circle(robot_position, \
    #                         lp['dropzone']['position'], \
    #                         lp['dropzone']['radius']):
        
    #         # Does the robot carry resource? YES -> Sell resource
    #         resource_quality = robot.variables.get_attribute("hasResource")
    #         if resource_quality and robot.variables.get_attribute("dropResource"):      
    #             resource_counter[resource_quality] += 1  

    #             robot.variables.set_attribute("hasResource", "")
    #             robot.variables.set_attribute("resourceCount", str(int(robot.variables.get_attribute("resourceCount"))+1))
                # print('Robot sold resource! Count='+robot.variables.get_attribute("resourceCount"))
        

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

    # Record the resources to be drawn to a file
    with open(lp['files']['resources'], 'w', buffering=1) as f:
        for res in resource_list:
            f.write(res._json+'\n')

    # # Record the carried resourced to be drawn to a file
    # with open(lp['files']['robots'], 'w', buffering=1) as f:
    #     for robot in allrobots:
    #         if robot.variables.get_attribute("hasResource"):
    #             robotID = str(int(robot.variables.get_id()[2:])+1)
    #             x = str(robot.position.get_position()[0])
    #             y = str(robot.position.get_position()[1])
    #             f.write(robotID + ', ' + x + ', ' + y + ', ' + repr(robot.variables.get_attribute("hasResource")) + '\n')

    # # Record the rays to be drawn for each robot
    # with open(lp['files']['rays'], 'w', buffering=1) as f:
    #     for robot in allrobots:
    #         f.write(robot.variables.get_attribute("rays"))

    # # Record the distance each robot has travelled in the current step
    #     position_current = Vector2D(robot.position.get_position()[0:2])              
    #     distance_traveled = (position_current - position_previous[robot.variables.get_attribute("id")]).length  
    #     accums['distance_forage'].acc(distance_traveled)
    #     if robot.variables.get_attribute("state") == "Recruit.FORAGE":
    #         accums['distance_forage'].acc(distance_traveled)
    #     if robot.variables.get_attribute("state") == "Scout.EXPLORE":
    #         accums['distance_explore'].acc(distance_traveled)

    # Logging of simulation status (RAM, CPU, TPS)   
    if clocks['update_status'].query():
        RAM = getRAMPercent()
        CPU = getCPUPercent()
    TPS = round(1/(time.time()-logs['status'].latest))
    logs['status'].log([TPS, CPU, RAM])

    # # Logging of loop function variables
    # logs['loop'].log([accums['distance_forage'].value]
    #           + [accums['distance_forage'].value]
    #           + [accums['distance_explore'].value]
    #           + [str(value) for value in resource_counter.values()] 
    #           + [sum(resource_counter.values())] 
    #           + [sum([resource_counter[x]*lp['patches']['utilities'][x] for x in lp['patches']['utilities']])])


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
    # environment.qt_draw.close_window() // seg fault
    print("Finished from Python!!")




