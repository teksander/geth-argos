#!/usr/bin/env python3
import random
import time
import configparser
import os
import json
from types import SimpleNamespace
import math
import os
experimentFolder = os.environ["EXPERIMENTFOLDER"]
import sys
sys.path.insert(1, experimentFolder+'/controllers')
sys.path.insert(1, experimentFolder+'/loop_functions')
from aux import Vector2D, Logger, getRAMPercent, getCPUPercent
from enum import Enum
import psutil

from loop_function_params import *

open(resource_file, 'w+').close()
open(robot_file, 'w+').close()
open(rays_file, 'w+').close()


# Other inits
global resource_list, resource_counter, sttime, market

resource_utilities = resource_params['utilities']
# resource_frequency = resource_params['rel_frequency']
resource_frequency = resource_params['abs_frequency']
resource_counter = {'red': 0, 'green': 0 , 'blue': 0, 'yellow': 0}

resource_list = []

class Location(object):
    def __init__(self, x, y, radius, quantity, quality):
        self.x = x
        self.y = y
        self.radius = radius
        self.quantity = quantity
        self.quality = quality

    def getJSON(self):
        return str(vars(self)).replace("\'", "\"")


def generate_resource(n = 1, qualities = None):

    for i in range(n):
        overlap = True
        radius = 0

        while overlap:

            # Generate a new resource position
            x = round(random.uniform(-generic_params['arena_size']/2, generic_params['arena_size']/2), 2)
            y = round(random.uniform(-generic_params['arena_size']/2, generic_params['arena_size']/2), 2)

            # Generate a new resource radius
            while radius <= 0:
                radius = round(random.gauss(resource_params['radius_mu'], resource_params['radius_sigma']),2)

            # Generate quantity of resource and quality
            quantity = random.randint(resource_params['quantity_min'], resource_params['quantity_max'])

            if not qualities:
                quality = random.choices(list(resource_frequency), weights=resource_frequency.values())[0]
            else:
                quality = qualities[i]
                
            
            overlap = False
            # Discard if resource overlaps with sides of arena
            if (max((abs(a)) for a in [x,y])  + radius > generic_params['arena_size']/2):
                overlap = True

            # Discard if resource overlaps with other resources
            for res in resource_list:
                if is_in_circle((res.x, res.y), (x,y), res.radius+radius):
                    overlap = True

            # Discard if resource overlaps with market
            if is_in_circle((market.x, market.y), (x,y), market.radius+radius):
                overlap = True

            # Discard if resource overlaps with minimum area
            if is_in_circle((market.x, market.y), (x,y), resource_params['min_distance']+radius):
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
    global market, looplog, simlog, sttime
    sttime = time.time()

    log_folder = experimentFolder + '/logs/0/'
    os.makedirs(os.path.dirname(log_folder), exist_ok=True)    

    header = list(resource_utilities) + ['TOTAL', 'VALUE']
    log_filename = log_folder + 'loop_function.csv'
    looplog = Logger(log_filename, header, ID = '0')
    looplog.start()

    header = ['FPS', 'RAM', 'CPU']
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

    # Initialize locations in the arena
    market = Location(x = 0, y = 0, radius = market_params['radius'], quantity = 1, quality = 'yellow')

    # generate_resource(resource_params['count'])

    lst = []
    for k,v in resource_params['abs_frequency'].items():
        lst.extend(v*[k])
    print(lst)
    generate_resource(resource_params['count'], qualities = lst)

            
def pre_step():
    global resource_counter
    
    for robot in allrobots:
        robot.variables.set_attribute("newResource", "")
        
        # Has robot stepped into resource? YES -> Update virtual sensor
        for res in resource_list:
            if is_in_circle(robot.position.get_position(), (res.x, res.y), res.radius):
                robot.variables.set_attribute("newResource", res.getJSON())

                # Does the robot not carry resource and chooses to pick up? YES -> Pickup resource
                if not robot.variables.get_attribute("hasResource") and robot.variables.get_attribute("collectResource"):

                        robot.variables.set_attribute("hasResource", res.quality)
                        res.quantity -= 1
                        # robot.variables.set_attribute("newResource", "")
                        # print('Robot got resource!')

                        # Has resource expired? YES -> Generate new
                        if res.quantity <= 0:
                            resource_list.remove(res)
                            generate_resource(1, [res.quality])

        # Has robot stepped into market? YES
        if is_in_circle(robot.position.get_position(), (market.x, market.y), market.radius):

            # Does the robot carry resource? YES -> Sell resource
            resource_quality = robot.variables.get_attribute("hasResource")
            if resource_quality:      
                resource_counter[resource_quality] += 1  

                robot.variables.set_attribute("hasResource", "")
                robot.variables.set_attribute("resourceCount", str(int(robot.variables.get_attribute("resourceCount"))+1))
                # print('Robot sold resource! Count='+robot.variables.get_attribute("resourceCount"))

                looplog.log([str(value) for value in resource_counter.values()] 
                          + [sum(resource_counter.values())] 
                          + [sum([resource_counter[x]*resource_utilities[x] for x in resource_utilities])])

RAM = getRAMPercent()
CPU = getCPUPercent()
tlast = time.time()

def post_step():
    global simlog, tlast, RAM, CPU
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

    # Logging of FPS, RAM and CPU usage   
    if time.time()-tlast > 10:
        RAM = getRAMPercent()
        CPU = getCPUPercent()
        tlast = time.time()
    FPS = round(1/(time.time()-simlog.latest))

    simlog.log([FPS, CPU, RAM])



def is_experiment_finished():

    finished = time.time() - sttime > generic_params['time_limit']

    if finished:
        print("Experiment has finished")

    return finished

def reset():
    pass

def destroy():
    pass

def post_experiment():
    print("Finished from Python!!")




