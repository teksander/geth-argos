#!/usr/bin/env python3

# /* Import Packages */
#######################################################################
import random, math, copy
import time, sys, os
import logging, threading
from types import SimpleNamespace
import json

experimentFolder = os.environ["EXPERIMENTFOLDER"]
sys.path.insert(1, experimentFolder+'/controllers')
sys.path.insert(1, experimentFolder+'/loop_functions')
sys.path.insert(1, experimentFolder)

from aux import Vector2D, Logger, getRAMPercent, getCPUPercent, mydict
from groundsensor import Resource

from loop_function_params import *
from controller_params import *

random.seed(generic_params['seed'])

# /* Global Variables */
#######################################################################
open(resource_file, 'w+').close()
open(robot_file, 'w+').close()
open(rays_file, 'w+').close()



# Other inits
global resource_list, resource_counter, sttime, emergency_stop
emergency_stop = False
resource_list = []
resource_counter = {'red': 0, 'green': 0 , 'blue': 0, 'yellow': 0}
distance_accumul = 0
distance_accumul_forage = 0
distance_accumul_explore = 0
position_previous = dict()

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

# Store the position of the market
market_js = {"x":0, "y":0, "radius":  market_params['radius'], "radius_dropoff": market_params['radius_dropoff']}
market = Resource(market_js)

class Location(object):
    def __init__(self, x, y, radius, quantity, quality):
        self.x = x
        self.y = y
        self.radius = radius
        self.quantity = quantity
        self.quality = quality
        self.utility = resource_params['utility'][self.quality]

    def getJSON(self):
        return str(vars(self)).replace("\'", "\"")


def generate_resource(n = 1, qualities = None, max_attempts = 50):
    global emergency_stop
    for i in range(n):
        overlap = True
        radius = 0
        attempts = 0

        while overlap:
            attempts += 1
            if attempts == max_attempts:
                print("Max attempts reached")
                emergency_stop = True
                break

            # Generate a new resource position (uniform)
            if resource_params['distribution'] == 'uniform':
                x = round(random.uniform(-generic_params['arena_size']/2, generic_params['arena_size']/2), 2)
                y = round(random.uniform(-generic_params['arena_size']/2, generic_params['arena_size']/2), 2)

            # Generate a new resource position (patchy)
            elif resource_params['distribution'] == 'patchy':
                patch = random.choices(resource_params['patches'])[0]
                x = round(random.gauss(patch['x_mu'], patch['x_sg']), 2)
                y = round(random.gauss(patch['y_mu'], patch['y_sg']), 2)

            
            # Generate a new resource radius
            # while radius <= 0:
            #     radius = round(random.gauss(resource_params['radius'], resource_params['radius_sigma']),2)

            # Generate quantity of resource and quality
            quantity = random.randint(resource_params['quantity_min'], resource_params['quantity_max'])

            if not qualities:
                quality = random.choices(list(resource_params['frequency']), weights=resource_params['frequency'].values())[0]
            else:
                quality = qualities[i]
            
            radius = radii[quality]
            
            overlap = False
            # Discard if resource overlaps with sides of arena
            if (max((abs(a)) for a in [x,y])  + radius > generic_params['arena_size']/2):
                overlap = True

            # Discard if resource overlaps with other resources
            if any([is_in_circle((res.x, res.y), (x,y), res.radius+radius) for res in resource_list]):
                overlap = True

            # Discard if resource overlaps with market
            if is_in_circle((market.x, market.y), (x,y), market.radius_dropoff+radius):
                overlap = True

            # Discard if resource overlaps with minimum area
            if is_in_circle((0, 0), (x,y), resource_params['distance_min']+radius):
                overlap = True

            # Discard if resource overlaps with maximum area
            if not is_in_circle((0, 0), (x,y), resource_params['distance_max']-radius):
                overlap = True

        # Append new resource to the global list of resources
        resource_list.append(Location(x, y, radius, quantity, quality))
        # print('Created Resource: ' + resource_list[-1].getJSON())


def is_in_circle(point, circle_center, circle_radius):
    dx = abs(point[0] - circle_center[0])
    dy = abs(point[1] - circle_center[1])
    R = circle_radius

    # Alternatively check for a square inside the circle (dx + dy <= R)
    if dx**2 + dy**2 <= R**2:
        return True 
    else:
        return False

def init():
    global looplog, simlog, sttime
    sttime = time.time()

    log_folder = experimentFolder + '/logs/0/'
    os.makedirs(os.path.dirname(log_folder), exist_ok=True)    

    header = ['DIST', 'RECRUIT_DIST', 'SCOUT_DIST']+list(resource_counter) + ['TOTAL', 'VALUE']
    log_filename = log_folder + 'loop_function.csv'
    looplog = Logger(log_filename, header, ID = '0')
    looplog.start()

    header = ['TPS', 'RAM', 'CPU']
    log_filename = log_folder + 'simulation.csv'  
    simlog = Logger(log_filename, header, ID = '0')
    simlog.start()

    # # Initialize robot parameters
    for robot in allrobots:
    #     robot.variables.set_attribute("newResource", "")
    #     robot.variables.set_attribute("hasResource", "")
    #     robot.variables.set_attribute("resourceCount", "0")
    #     robot.variables.set_attribute("rays", "")

        print(robot.variables.get_all_attributes())
        position_previous[robot.variables.get_attribute("id")] = Vector2D(robot.position.get_position()[0:2]) 

    # Initialize locations in the arena

    for quality, count in counts.items():
        generate_resource(count, qualities = count*[quality])

            
def pre_step():
    global resource_counter
    
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
                robot.variables.set_attribute("newResource", res.getJSON())

        # Has robot stepped into market drop area? YES
        if is_in_circle(robot.position.get_position(), (market.x, market.y), market.radius_dropoff):

            # Does the robot carry resource? YES -> Sell resource
            resource_quality = robot.variables.get_attribute("hasResource")
            if resource_quality and robot.variables.get_attribute("dropResource"):      
                resource_counter[resource_quality] += 1  

                robot.variables.set_attribute("hasResource", "")
                robot.variables.set_attribute("resourceCount", str(int(robot.variables.get_attribute("resourceCount"))+1))
                # print('Robot sold resource! Count='+robot.variables.get_attribute("resourceCount"))

                looplog.log([distance_accumul]
                          + [distance_accumul_forage]
                          + [distance_accumul_explore]
                          + [str(value) for value in resource_counter.values()] 
                          + [sum(resource_counter.values())] 
                          + [sum([resource_counter[x]*resource_params['utility'][x] for x in resource_params['utility']])])

RAM = getRAMPercent()
CPU = getCPUPercent()
tlast = time.time()

def post_step():
    global distance_accumul, distance_accumul_forage, distance_accumul_explore, simlog, tlast, RAM, CPU
    ### The way to share information to qtuser_function should be improved ### \

    # Record the resources to be drawn to a file
    with open(resource_file, 'w', buffering=1) as f:
        for res in resource_list:
            f.write(res.getJSON()+'\n')

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
        distance_accumul += distance_traveled
        if robot.variables.get_attribute("state") == "Recruit.FORAGE":
            distance_accumul_forage += distance_traveled
        if robot.variables.get_attribute("state") == "Scout.EXPLORE":
            distance_accumul_explore += distance_traveled

    # # Record the resources each robot has in smart contract
    # for robot in allrobots:
    #     p = 'a'
    #     if robot.variables.get_attribute("id") == "1":
    #         p = 'w+'
    #     with open(scresources_file, p, buffering=1) as f:

    #         resources = eval(robot.variables.get_attribute("scresources"))
    #         for resource in resources:
    #             f.write(resource+'\n')

    # Logging of TPS, RAM and CPU usage   
    if time.time()-tlast > 10:
        RAM = getRAMPercent()
        CPU = getCPUPercent()
        tlast = time.time()
    TPS = round(1/(time.time()-simlog.latest))

    simlog.log([TPS, CPU, RAM])



def is_experiment_finished():

    time_limit = time.time() - sttime > generic_params['time_limit']
    
    finished = time_limit or emergency_stop

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




