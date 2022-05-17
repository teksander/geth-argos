#!/usr/bin/env python3

# /* Import Packages */
#######################################################################
import random, math
import time, sys, os
import logging

sys.path += [os.environ['EXPERIMENTFOLDER']+'/controllers', \
             os.environ['EXPERIMENTFOLDER']+'/loop_functions', \
             os.environ['EXPERIMENTFOLDER']]

from aux import Vector2D, Logger, Timer, Accumulator, getRAMPercent, getCPUPercent, mydict
from groundsensor import Resource

from control_params import params as cp
from loop_params import params as lp
from loop_helpers import *

random.seed(lp['generic']['seed'])

log_folder = lp['environ']['EXPERIMENTFOLDER'] + '/logs/0/'
os.makedirs(os.path.dirname(log_folder), exist_ok=True)   


# /* Global Variables */
#######################################################################

global resource_list, resource_counter
resource_list = []
resource_counter = {'red': 0, 'green': 0 , 'blue': 0, 'yellow': 0}
position_previous = dict()

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
global clocks, accums, logs
clocks = accums = logs = dict()

clocks['update_status'] = Timer(10)
accums['distance'] = Accumulator()
accums['distance_forage'] = Accumulator()
accums['distance_explore'] = Accumulator()

# Store the position of the market and cache
market   = Resource({"x":lp['market']['x'], "y":lp['market']['y'], "radius": lp['market']['radius']})
cache    = Resource({"x":lp['cache']['x'], "y":lp['cache']['y'], "radius": lp['cache']['radius']})

def generate_resource(n = 1, qualities = None, max_attempts = 50):
    global stopFlag
    for i in range(n):
        overlap = True
        radius = 0
        attempts = 0

        while overlap:
            attempts += 1
            if attempts == max_attempts:
                print("Max attempts reached")
                stopFlag = True
                break

            # Generate a new resource position (uniform)
            if lp['patches']['distribution'] == 'uniform':
                x = round(random.uniform(-lp['generic']['arena_size']/2, lp['generic']['arena_size']/2), 2)
                y = round(random.uniform(-lp['generic']['arena_size']/2, lp['generic']['arena_size']/2), 2)

            # Generate a new resource position (patchy)
            elif lp['patches']['distribution'] == 'patchy':
                patch = random.choices(lp['patches']['hotspots'])[0]
                x = round(random.gauss(patch['x_mu'], patch['x_sg']), 2)
                y = round(random.gauss(patch['y_mu'], patch['y_sg']), 2)

            
            # Generate a new resource radius
            # while radius <= 0:
            #     radius = round(random.gauss(lp['patches']['radius'], lp['patches']['radius_sigma']),2)

            # Generate quantity of resource and quality
            quantity = random.randint(lp['patches']['qtty_min'], lp['patches']['qtty_max'])

            if not qualities:
                quality = random.choices(list(lp['patches']['frequency']), weights=lp['patches']['frequency'].values())[0]
            else:
                quality = qualities[i]
            
            radius = radii[quality]
            
            overlap = False
            # Discard if resource overlaps with sides of arena
            if (max((abs(a)) for a in [x,y])  + radius > lp['generic']['arena_size']/2):
                overlap = True

            # Discard if resource overlaps with other resources
            if any([is_in_circle((res.x, res.y), (x,y), res.radius+radius) for res in resource_list]):
                overlap = True

            # Discard if resource overlaps with market
            if is_in_circle((market.x, market.y), (x,y), cache.radius+radius):
                overlap = True

            # Discard if resource overlaps with minimum area
            if is_in_circle((0, 0), (x,y), lp['patches']['dist_min']+radius):
                overlap = True

            # Discard if resource overlaps with maximum area
            if not is_in_circle((0, 0), (x,y), lp['patches']['dist_max']-radius):
                overlap = True

        # Append new resource to the global list of resources
        resource_list.append(Resource({'x':x, 'y':y, 'radius':radius, 'quantity':quantity, 'quality':quality, 'utility':lp['patches']['utility'][quality]}))

        # print('Created Resource: ' + resource_list[-1]._json)


def init():

    header = ['TPS', 'RAM', 'CPU']
    filename = log_folder + 'status.csv'  
    logs['status'] = Logger(filename, header, ID = '0')
    logs['status'].start()

    header = ['DIST', 'RECRUIT_DIST', 'SCOUT_DIST']+list(resource_counter) + ['TOTAL', 'VALUE']
    filename = log_folder + 'loop_function.csv'
    logs['loop'] = Logger(filename, header, ID = '0')
    logs['loop'].start()

    for robot in allrobots:
        print(robot.variables.get_all_attributes())
        position_previous[robot.variables.get_attribute("id")] = Vector2D(robot.position.get_position()[0:2]) 

    for quality, count in counts.items():
        generate_resource(count, qualities = count*[quality])

            
def pre_step():
    global startFlag, startTime, resource_counter

    if not startFlag:
        startTime = time.time()
    
    for robot in allrobots:
        robot.variables.set_attribute("newResource", "")
        
        # Has robot stepped into resource? YES -> Update virtual sensor
        for res in resource_list:
            if is_in_circle(robot.position.get_position(), (res.x, res.y), res.radius):

                # Does the robot not carry resource and is Forager? YES -> Pickup resource
                if not robot.variables.get_attribute("hasResource") and robot.variables.get_attribute("collectResource"):

                        robot.variables.set_attribute("hasResource", res.quality)
                        res.quantity -= 1

                        # Has resource expired? YES -> Generate new
                        if res.quantity <= 0:
                            resource_list.remove(res)
                            generate_resource(1, [res.quality])
                            
                # Update virtual sensor
                robot.variables.set_attribute("newResource", res._json)

        # Has robot stepped into market drop area? YES
        if is_in_circle(robot.position.get_position(), (market.x, market.y), cache.radius):

            # Does the robot carry resource? YES -> Sell resource
            resource_quality = robot.variables.get_attribute("hasResource")
            if resource_quality and robot.variables.get_attribute("dropResource"):      
                resource_counter[resource_quality] += 1  

                robot.variables.set_attribute("hasResource", "")
                robot.variables.set_attribute("resourceCount", str(int(robot.variables.get_attribute("resourceCount"))+1))


def post_step():
    global startFlag, clocks, accums, resource_counter
    global RAM, CPU


    # Record the resources to be drawn to a file
    with open(lp['files']['patches'], 'w', buffering=1) as f:
        for res in resource_list:
            f.write(res._json+'\n')

    # Record the carried resourced to be drawn to a file
    with open(lp['files']['robots'], 'w', buffering=1) as f:
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
        with open(lp['files']['rays'], p, buffering=1) as f:
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
              + [sum([resource_counter[x]*lp['patches']['utility'][x] for x in lp['patches']['utility']])])


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




