#!/usr/bin/env python3
import os
import math

# General Parameters
generic_params = dict()
generic_params['arena_size'] = float(os.environ["ARENADIM"])
generic_params['num_robots'] = int(os.environ["NUMROBOTS"])
generic_params['time_limit'] = int(os.environ["TIMELIMIT"]) * 60

# Parameters for marketplace
market_params = dict()
market_params['position'] = 'center'
market_params['radius']   = 0.08 * generic_params['arena_size']  

# Parameters for resources
resource_params = dict()
resource_params['radius_mu']    = 0.05 * generic_params['arena_size']  
resource_params['radius_sigma'] = 0 * resource_params['radius_mu']/100
resource_params['quantity_min'] = 1
resource_params['quantity_max'] = 5
resource_params['min_distance'] = 0.25 * generic_params['arena_size']  


resource_params['qualities'] = {'red', 'green' , 'blue', 'yellow'}
resource_params['utilities'] = {'red': 2, 'green':  4, 'blue': 6, 'yellow': 8}

resource_params['rel_frequency'] = {'red': 0.4, 'green': 0.3 , 'blue': 0.2, 'yellow': 0.1}
resource_params['count']        = 3*generic_params['num_robots']

resource_params['abs_frequency'] = {'red': 5, 'green': 4 , 'blue': 3, 'yellow': 2}
resource_params['count']         = sum(resource_params['abs_frequency'].values())

# resource_params['qualities'] = {'red'}
# resource_params['prices']    = {'red': 4}
# resource_params['frequency'] = {'red': 1}

# Parameters for the economy
economy_params = dict()
economy_params['fuel_cost'] = 0.1 # eth per second of exploration

# # Parameters for ARGoS
# argos_params = dict()
# argos_params['NUMROBOTS'] = 5
# argos_params['DENSITY'] = 1.5
# argos_params['ARENADIM'] = math.sqrt(argos_params['NUMROBOTS']/argos_params['DENSITY'])
# argos_params['ARENADIMH'] = argos_params['ARENADIM']/2
# argos_params['RAB_RANGE'] = 0.3
# argos_params['VISUALIZATION'] = None
# argos_params['FPS'] = 20
# argos_params['REPS'] = 5
# argos_params['SLEEPTIME'] = 5
# argos_params['TIMELIMIT'] = 20


# [OTHER]

# Initialize the files which store QT_draw information 
#(TO-DO: Find a better way to share draw info to qtuser_function.py)
resource_file = 'loop_functions/resources.txt'
robot_file = 'loop_functions/robots.txt'
rays_file = 'loop_functions/rays.txt'