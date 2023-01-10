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

# Store the position of the market and cache
market   = Resource({"x":lp['market']['x'], "y":lp['market']['y'], "radius": lp['market']['r']})
cache    = Resource({"x":lp['cache']['x'], "y":lp['cache']['y'], "radius": lp['cache']['r']})

def generate_resource(n = 1, qualities = None, max_attempts = 500):
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

            # Generate a new resource position (fixed)
            if lp['patches']['distribution'] == 'fixed':
                x = lp['patches']['x'][i]
                y = lp['patches']['y'][i]

            # Generate a new resource position (uniform)
            elif lp['patches']['distribution'] == 'uniform':
                # x = round(random.uniform(-lp['generic']['arena_size']/2, lp['generic']['arena_size']/2), 2)
                # y = round(random.uniform(-lp['generic']['arena_size']/2, lp['generic']['arena_size']/2), 2)
                r1 = lp['patches']['dist_min']
                r2 = lp['patches']['dist_max'] 
                r = math.sqrt(r1**2 + (r2**2-r1**2)*random.random())
                t = 2 * math.pi * random.random()
                x = r * math.cos(t) 
                y = r * math.sin(t) 

            # Generate a new resource position (patchy)
            elif lp['patches']['distribution'] == 'patchy':
                patch = random.choices(lp['patches']['hotspots'])[0]
                # x = round(random.gauss(patch['x_mu'], patch['x_sg']), 2)
                # y = round(random.gauss(patch['y_mu'], patch['y_sg']), 2)

            
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

            # Discard if resource is inside minimum area
            if is_in_circle((0, 0), (x,y), lp['patches']['dist_min']):
                overlap = True

            # Discard if resource is outside maximum area
            if not is_in_circle((0, 0), (x,y), lp['patches']['dist_max']):
                overlap = True

            # Discard if resource is outside of arena
            if is_in_rectangle((0, 0), (x,y), lp['generic']['arena_size']/2):
                overlap = True

        # Append new resource to the global list of resources
        allresources.append(Resource({'x':x, 'y':y, 'radius':radius, 'quantity':quantity, 'quality':quality, 'utility':lp['patches']['utility'][quality]}))

        clocks['regen'][allresources[-1]] = Timer(lp['patches']['regen_rate'][allresources[-1].quality])
        other['foragers'][allresources[-1]] = set()

        # print('Created Resource: ' + allresources[-1]._json)

def forage_rate(res, carried = 0):
    cost_base    = lp['patches']['forage_rate'][res.quality]
    qtty_carried = int(carried)

    cost_patch = 0
    cost_robot = 0

    if res.quantity >= lp['patches']['dec_returns']['thresh']:
        cost_patch = cost_base

    elif lp['patches']['dec_returns']['func'] == 'linear':
        m = lp['patches']['dec_returns']['slope']
        b = cost_base + m*lp['patches']['dec_returns']['thresh']
        cost_patch = -m*res.quantity + b   

    if qtty_carried != 0:
        cost_robot = qtty_carried*lp['patches']['dec_returns']['slope_robot']

    return cost_patch + cost_robot

def init():

    # Init resources in the arena
    for quality, count in counts.items():
        generate_resource(count, qualities = count*[quality])

    # Init robot parameters
    for robot in allrobots:

        robot.id = int(robot.variables.get_attribute("id"))
        robot.ip = identifiersExtract(robot.id)
        robot.variables.set_attribute("eff", str(lp['economy']['efficiency_best']+robot.id*lp['economy']['efficiency_step']))
        
        if lp['patches']['known']:
            robot.variables.set_attribute("newResource", allresources[robot.id % len(allresources)]._json)
    
    # Init logfiles for loop function
    file   = 'simulation.csv'
    header = ['TPS', 'RAM', 'CPU']
    logs['simulation'] = Logger(log_folder+file, header, ID = '0')

    file   = 'loop.csv'
    header = list(resource_counter) + ['TOTAL', 'VALUE']
    logs['loop'] = Logger(log_folder+file, header, ID = '0')

    file   = 'patches.csv'
    header = ['JSON']
    logs['patches'] = Logger(log_folder+file, header, rate = 2, ID = '0')

    file   = 'collection.csv'
    header = ['ROBOT_ID', 'QLTY', 'QTTY','TOTAL']
    logs['collection'] = Logger(log_folder+file, header, rate = 1, ID = '0')

    for log in logs.values():
        log.start()


def pre_step():
    global startFlag, startTime, resource_counter

    # Tasks to perform on the first time step
    if not startFlag:
        startTime = time.time()
    
    # Tasks to perform for each robot
    lastBlock = None
    for robot in allrobots:
        robot.variables.set_attribute("at", "")

        # Has robot stepped into resource? YES -> Update virtual sensor
        for res in allresources:
        
            if is_in_circle(robot.position.get_position(), (res.x, res.y), res.radius):

                # Update robot virtual sensor
                robot.variables.set_attribute("newResource", res._json)
                robot.variables.set_attribute("at", res._json)
                
                # Robot is foraging? YES -> Add to foragers
                if robot.variables.get_attribute("foraging"):

                    if robot not in other['foragers'][res]:
                        other['foragers'][res].add(robot)
                        clocks['forage'][robot] = Timer(100)
                        
        # Has robot stepped into market drop area? YES
        if is_in_circle(robot.position.get_position(), (cache.x, cache.y), cache.radius):
            robot.variables.set_attribute("at", "cache")

            # Does the robot carry resource? YES -> Sell resource
            resource_quality = robot.variables.get_attribute("hasResource")
            if resource_quality and robot.variables.get_attribute("dropResource"):

                resource_counter[resource_quality] += int(robot.variables.get_attribute("quantity")) 
                accums['collection'][robot.id].acc(lp['patches']['utility'][resource_quality])

                logs['collection'].log([robot.id, resource_quality, resource_counter[resource_quality]])

                if clocks['regen'][res].rate == "on_drop":
                    res.quantity += int(robot.variables.get_attribute("quantity"))

                robot.variables.set_attribute("hasResource", "")
                robot.variables.set_attribute("quantity", "0")
                robot.variables.set_attribute("resourceCount", str(int(robot.variables.get_attribute("resourceCount"))+1))

        # if clocks['block'].query():
        #     block = eval(robot.variables.get_attribute("block"))
        #     if lastBlock == None or block['totalDifficulty']>lastBlock['totalDifficulty']:
        #         lastBlock = block
        #         print('New Block:', lastBlock['number'], lastBlock['totalDifficulty'])
        # robot.variables.set_attribute('block', repr(block))

    # Tasks to perform for each resource
    for res in allresources:

        for robot in random.sample(other['foragers'][res], len(other['foragers'][res])):
            clocks['forage'][robot].set(forage_rate(res, robot.variables.get_attribute("quantity")), reset=False)

            if clocks['forage'][robot].query():
                robot.variables.set_attribute("hasResource", res.quality)
                robot.variables.set_attribute("quantity", str(int(robot.variables.get_attribute("quantity"))+1))
                robot.variables.set_attribute("forageTimer", str(round(clocks['forage'][robot].rate, 2)))
                res.quantity -= 1

            if not robot.variables.get_attribute("foraging"):
                other['foragers'][res].remove(robot)
                clocks['forage'][robot] = None

            # Regenerate resource
            if clocks['regen'][res].query() and res.quantity < lp['patches']['qtty_max']:
                res.quantity += 1

            logs['patches'].log([res._json.replace(" ", "")])

def post_step():
    global startFlag, clocks, accums, resource_counter
    global RAM, CPU

    if not startFlag:
        startFlag = True

    # Respawn depleted patches
    if lp['patches']['respawn']:
        depleted = [res for res in allresources if res.quantity <= 0]
        allresources[:] = [res for res in allresources if res not in depleted]
        generate_resource(len(depleted), [res.quality for res in depleted])

    # Record the resources to be drawn to a file
    with open(lp['files']['patches'], 'w', buffering=1) as f:
        for res in allresources:
            f.write(res._json+'\n')

    # Record the carried resources to be drawn to a file
    with open(lp['files']['robots'], 'w', buffering=1) as f:
        for robot in allrobots:
            if robot.variables.get_attribute("hasResource"):
                robotID = str(int(robot.variables.get_id()[2:])+1)
                x = str(robot.position.get_position()[0])
                y = str(robot.position.get_position()[1])
                # f.write(robotID + ', ' + x + ', ' + y + ', ' +  + '\n')
                f.write('%s, %s, %s, %s, %s \n' % (robotID, x, y, robot.variables.get_attribute("quantity"), repr(robot.variables.get_attribute("hasResource"))))

    # Record the rays to be drawn for each robot
    for robot in allrobots:
        robot.variables.set_attribute("newResource", "")
        p = 'a'
        if robot.variables.get_attribute("id") == "1":
            p = 'w+'
        with open(lp['files']['rays'], p, buffering=1) as f:
            f.write(robot.variables.get_attribute("rays"))

    # Logging of simulation simulation (RAM, CPU, TPS)   
    if clocks['simlog'].query():
        RAM = getRAMPercent()
        CPU = getCPUPercent()
    TPS = round(1/(time.time()-logs['simulation'].latest))
    logs['simulation'].log([TPS, CPU, RAM])

    # Logging of loop function variables
    logs['loop'].log([str(value) for value in resource_counter.values()] 
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




