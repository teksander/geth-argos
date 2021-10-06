#!/usr/bin/env python3

import random
import time
import loop_function_params as lfp
import configparser
import os
import json
from types import SimpleNamespace

# General Parameters
generic_params = dict()
generic_params['arena_size'] = os.environ["ARENADIM"]
generic_params['num_robots'] = int(os.environ["NUMROBOTS"])

# Parameters for marketplace
market_params = dict()
market_params['position'] = 'left'
market_params['size'] = 0.2

# Parameters for new resources
resource_params = dict()
resource_params['count'] = 2*generic_params['num_robots']
resource_params['quality_mu'] = 0.1
resource_params['quality_sigma'] = 0.01
resource_params['quantity_min'] = 2
resource_params['quantity_max'] = 4

global resource_list
resource_list = []
resource_file = 'resources.txt'



class resource_obj(object):
    def __init__(self, x, y, quality, quantity):
        self.x = x
        self.y = y
        self.quality = quality
        self.quantity = quantity
        self.timeStamp = time.time()
        self.__json = str(vars(self)).replace("\'", "\"")

    def getJSON(self):
        return self.__json

market = resource_obj(x = 0, y = 0, quality = 0.1, quantity = 1)

def generate_resource(n = 1):

    for param, val in generic_params.items(): exec(param + '=val')
    for param, val in market_params.items(): exec(param + '=val')
    arena_size = float(generic_params['arena_size'])

    for _ in range(n):
        overlap = True
        quality = 0

        while overlap:
            # Generate parameters for a new resource
            x = round(random.uniform(-arena_size/2, arena_size/2), 2)
            y = round(random.uniform(-arena_size/2, arena_size/2), 2)

            while quality <= 0:
                quality = round(random.gauss(resource_params['quality_mu'], resource_params['quality_sigma']),2)

            quantity = random.randint(resource_params['quantity_min'], resource_params['quantity_max'])

            overlap = False
            # Check if it overlaps with arena sides or other resources
            if (max((abs(a)) for a in [x,y])  + quality > arena_size/2):
                overlap = True

            for res in resource_list:
                if is_in_circle((res.x, res.y), (x,y), res.quality+quality):
                    overlap = True

            if is_in_circle((market.x, market.y), (x,y), market.quality+quality):
                overlap = True

        resource_list.append(resource_obj(x, y, quality, quantity))
        print('Created Resource: ' + resource_list[-1].getJSON())

        with open(resource_file, 'w', buffering=1) as f:
            for res in resource_list:
               f.write(res.getJSON()+'\n')

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

    for robot in allrobots:
        robot.variables.set_attribute("hasResource", "False")

    generate_resource(resource_params['count'])

def reset():
    pass

def destroy():
    pass

def pre_step():
    pass

def post_step():

    # Has robot stepped into resource?
    for robot in allrobots:

        if robot.variables.get_attribute("hasResource") == "False":

            for res in resource_list:
                if is_in_circle(robot.position.get_position(), (res.x, res.y), res.quality):

                    robot.variables.set_attribute("hasResource", "True")
                    print('Robot got resource!')
                    res.quantity -= 1
                    robot.variables.set_attribute("knownResource", res.getJSON())
                    if res.quantity <= 0:
                        resource_list.remove(res)
                        print("Depleted resource")
                        robot.variables.set_attribute("knownResource", "")

                        generate_resource()


        if robot.variables.get_attribute("hasResource") == "True":        
            if is_in_circle(robot.position.get_position(), [0,0], 0.1):
                robot.variables.set_attribute("hasResource", "False")
                print('Robot sold resource!')

                

def is_experiment_finished():
    # Determine whether all robots have reached a consensus 
    finished = True

    for robot in allrobots:
        finished = finished and robot.variables.get_consensus()

    if finished:
        print("A consensus was reached")

    return finished

def get_floor_color():
    print("Executing Python side")

def post_experiment():
    print("Finished from Python!!")




