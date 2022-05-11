#!/usr/bin/env python3
import os, math

# All parameters
params = dict()

# General Parameters
params['environ'] = os.environ

# General Parameters
generic_params = dict()
generic_params['arena_size'] = float(os.environ["ARENADIMY"])
generic_params['num_robots'] = int(os.environ["NUMROBOTS"])
generic_params['time_limit'] = float(os.environ["TIMELIMIT"]) * 60
generic_params['seed']       = 350 # None for randomgen

generic_params['tps'] = eval(os.environ["TPS"])
generic_params['num_1'] = eval(os.environ["NUM1"])
generic_params['num_2'] = eval(os.environ["NUM2"])
generic_params['arena_dim'] = eval(os.environ["ARENADIMY"])
generic_params['rab_range'] = eval(os.environ["RABRANGE"])
generic_params['block_period'] = eval(os.environ["BLOCKPERIOD"])
generic_params['max_recruits'] = eval(os.environ["MAXRECRUITS"])

params['generic'] = generic_params

# Parameters for marketplace
market_params = dict()
market_params['radius']         = generic_params['arena_size'] * math.sqrt(0.03/math.pi)
market_params['radius_dropoff'] = generic_params['arena_size'] * math.sqrt(0.09/math.pi)

params['market'] = market_params

params['market']['height']   = eval(params['environ']['ARENADIMY'])
params['market']['width'] 	  = 0.5
params['market']['position'] = [0, 0]

params['quarry'] = dict()
params['quarry']['height']   = eval(params['environ']['ARENADIMY'])
params['quarry']['width'] 	 = 0.6
params['quarry']['position'] = [-eval(params['environ']['ARENADIMX'])/2 + params['quarry']['width']/2, 0]

params['bsite'] = dict()
params['bsite']['height']   = eval(params['environ']['ARENADIMY'])
params['bsite']['width'] 	= 0.6
params['bsite']['position'] = [eval(params['environ']['ARENADIMX'])/2 - params['bsite']['width']/2, 0]


params['stones'] = dict()
params['stones']['quantity'] = 30

params['lots'] = dict()
params['lots']['quantity'] = 4
params['lots']['height']   = 0.3
params['lots']['width']    = 0.3

# Parameters for resources
resource_params = dict()

resource_params['distribution'] = 'uniform' 
# resource_params['distribution'] = 'patchy'
# resource_params['patches']      = [{'x_mu': 0.25 * generic_params['arena_size'], 
# 									'y_mu': 0.25 * generic_params['arena_size'], 
# 									'x_sg': 0.15 * generic_params['arena_size'], 
# 									'y_sg': 0.15 * generic_params['arena_size']}]

resource_params['radius']    = 0.05
# resource_params['area_percent'] = 0.005 * (10/generic_params['num_robots'])
# resource_params['radius']    = generic_params['arena_size']  * math.sqrt(resource_params['area_percent']/math.pi) 

resource_params['quantity_min'] = 15
resource_params['quantity_max'] = 15
resource_params['distance_min'] = 1.7 * market_params['radius_dropoff']
resource_params['distance_max'] = 0.50 * generic_params['arena_size']   
resource_params['abundancy']    = 0.05

# Resource types
resource_params['qualities'] = {'red', 'green' , 'blue', 'yellow'}
resource_params['utility']   = {'red': 2, 'green':  4, 'blue': 6, 'yellow': 8}
# resource_params['frequency'] = {'red': 0.4, 'green': 0.3 , 'blue': 0.2, 'yellow': 0.1}
resource_params['frequency'] = {'red': 0.25, 'green': 0.25 , 'blue': 0.25, 'yellow': 0.25}
# resource_params['frequency'] = {'red': 0.7, 'green': 0.1 , 'blue': 0.1, 'yellow': 0.1}

# Parameters for qtuser
params['qt'] = dict()
params['qt']['show_rays'] = True

# Files that controller, loop and qtuser function use
params['files'] = dict()
params['files']['stones'] = 'loop_functions/stones.txt'
params['files']['lots']  = 'loop_functions/lots.txt'
params['files']['robots'] = 'loop_functions/robots.txt'
params['files']['rays']  = 'loop_functions/rays.txt'


## Parameters for the economy
# params['eco'] = dict()
# params['eco']['fuel_cost'] = 0.1 
