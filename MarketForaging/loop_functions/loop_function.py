#!/usr/bin/env python3

# /* Import Packages */
#######################################################################
import random, math
import time, sys, os
import logging

sys.path += [os.environ['EXPERIMENTFOLDER']+'/controllers', \
             os.environ['EXPERIMENTFOLDER']+'/loop_functions', \
             os.environ['EXPERIMENTFOLDER']]

from aux import Vector2D, Logger, Timer, Accumulator, mydict
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
clocks, accums, logs = dict(), dict(), dict()

clocks['update_status'] = Timer(10)
accums['distance'] = Accumulator()
accums['distance_forage'] = Accumulator()
accums['distance_explore'] = Accumulator()
accums['collection'] = [Accumulator() for i in range(lp['generic']['num_robots'])]
clocks['forage']     = dict()
clocks['regen']      = dict()

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
            if any([is_in_circle((res.x, res.y), (x,y), res.radius+radius) for res in allresources]):
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
        allresources.append(Resource({'x':x, 'y':y, 'radius':radius, 'quantity':quantity, 'quality':quality, 'utility':lp['patches']['utility'][quality]}))

        clocks['regen'][allresources[-1]] = Timer(lp['patches']['regen_rate'][allresources[-1].quality])

        # print('Created Resource: ' + allresources[-1]._json)


def init():

    header = ['TPS', 'RAM', 'CPU']
    file   = 'status.csv'  
    logs['status'] = Logger(log_folder+file, header, ID = '0')
    logs['status'].start()

    header = ['DIST', 'RECRUIT_DIST', 'SCOUT_DIST']+list(resource_counter) + ['TOTAL', 'VALUE']
    file   = 'loop_function.csv'
    logs['loop'] = Logger(log_folder+file, header, ID = '0')
    logs['loop'].start()

    header = [str(robotID) for robotID in range(1, lp['generic']['num_robots']+1)]
    file   = 'collection.csv'
    logs['collection'] = Logger(log_folder+file, header, rate = 1, ID = '0')
    logs['collection'].start()

    for robot in allrobots:
        print(robot.variables.get_all_attributes())
        robot.id = int(robot.variables.get_attribute("id"))-1
        position_previous[robot.variables.get_attribute("id")] = Vector2D(robot.position.get_position()[0:2]) 

    for quality, count in counts.items():
        generate_resource(count, qualities = count*[quality])

            
def pre_step():
    global startFlag, startTime, resource_counter

    # Tasks to perform on the first time step
    if not startFlag:
        startTime = time.time()
    
    # Tasks to perform every time step
    foragers = {res: [] for res in allresources}

    # Tasks to perform for each robot
    for robot in allrobots:
        robot.variables.set_attribute("newResource", "")
        robot.variables.set_attribute("at", "")
        
        # Has robot stepped into resource? YES -> Update virtual sensor
        for res in allresources:

            if is_in_circle(robot.position.get_position(), (res.x, res.y), res.radius):

                # Update robot virtual sensor
                robot.variables.set_attribute("newResource", res._json)

                # Robot does not carry resource and is forager? YES -> Forage resource
                if not robot.variables.get_attribute("hasResource") \
                   and robot.variables.get_attribute("collectResource"):
                   foragers[res].append(robot.id) 
                else:
                    if robot.id in clocks['forage']: 
                        clocks['forage'].pop(robot.id)

                # Robot foraging timer is up? YES -> Collect resource
                if robot.id in clocks['forage']:
                    robot.variables.set_attribute("forageTimer", str(round(clocks['forage'][robot.id].rate,2)))
                    if clocks['forage'][robot.id].query():
                        res.quantity -= 1
                        robot.variables.set_attribute("hasResource", res.quality)
                        
        # Has robot stepped into market drop area? YES
        if is_in_circle(robot.position.get_position(), (cache.x, cache.y), cache.radius):
            robot.variables.set_attribute("at", "cache")

            # Does the robot carry resource? YES -> Sell resource
            resource_quality = robot.variables.get_attribute("hasResource")
            if resource_quality and robot.variables.get_attribute("dropResource"):      
                resource_counter[resource_quality] += 1  

                accums['collection'][robot.id].acc(lp['patches']['utility'][resource_quality])

                robot.variables.set_attribute("hasResource", "")
                robot.variables.set_attribute("resourceCount", str(int(robot.variables.get_attribute("resourceCount"))+1))


    # Tasks to perform for each resource
    for res in allresources:

        # Regenerate resource
        if clocks['regen'][res].query() and res.quantity < lp['patches']['qtty_max']:
            res.quantity += 1

        # Shuffle foragers to randomize who gets resources faster
        random.shuffle(foragers[res])

        # Base forage rate for resource type
        forageRate    = lp['patches']['forage_rate'][res.quality]
        m = (forageRate/lp['patches']['dec_returns_thresh']) * (1 - lp['patches']['dec_returns_mult'])
        b = forageRate*lp['patches']['dec_returns_mult']
        

        # Collect resources
        clocked   = [x for x in foragers[res] if x in clocks['forage']] 
        unclocked = [x for x in foragers[res] if x not in clocks['forage']] 
        already_clocking = len(clocked)

        for robotID in unclocked: 

            # Apply decreasing returns
            if lp['patches']['dec_returns_func'] == 'linear':

                if res.quantity < lp['patches']['dec_returns_thresh']:
                    forageRate = m * (res.quantity-already_clocking) + b
                    already_clocking += 1

            elif lp['patches']['dec_returns_func'] == 'log':
                pass

            clocks['forage'][robotID] = Timer(forageRate)


def post_step():
    global startFlag, clocks, accums, resource_counter
    global RAM, CPU

    if not startFlag:
        startFlag = True

    # Regenerate depleted patches
    depleted = [res for res in allresources if res.quantity <= 0]
    allresources[:] = [res for res in allresources if res not in depleted]

    generate_resource(len(depleted), [res.quality for res in depleted])

    # Record the resources to be drawn to a file
    with open(lp['files']['patches'], 'w', buffering=1) as f:
        for res in allresources:
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

    logs['collection'].log([accum.value for accum in accums['collection']])


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




