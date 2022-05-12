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

# Parameters for market
params['market'] = dict()
params['market']['position']  = [0, 0]
params['market']['radius']    = generic_params['arena_size'] * math.sqrt(0.03/math.pi)

# Parameters for dropzone
params['dropzone'] = dict()
params['dropzone']['position'] = [0, 0]
params['dropzone']['radius']   = generic_params['arena_size'] * math.sqrt(0.09/math.pi)

# Parameters for patches
params['patches'] = dict()
params['patches']['radius']    = 0.05
params['patches']['qtty_min']  = 10
params['patches']['qtty_max']  = 10
params['patches']['dist_min']  = 1.5  * market_params['radius_dropoff']
params['patches']['dist_max']  = 0.50 * generic_params['arena_size']   
params['patches']['qualities'] = {'red', 'green' , 'blue', 'yellow'}
params['patches']['utilities'] = {'red': 2, 'green':  4, 'blue': 6, 'yellow': 8}
params['patches']['counts']    = {'red': 1, 'green': 1 , 'blue': 1, 'yellow': 1}


# Parameters for the economy
# economy_params = dict()
# economy_params['fuel_cost'] = 0.1 # eth per second of exploration

# Initialize the files which store QT_draw information 
params['files']['resources'] = 'loop_functions/resources.txt'
params['files']['robots'] = 'loop_functions/robots.txt'
params['files']['rays'] = 'loop_functions/rays.txt'
params['files']['scresources'] = 'loop_functions/scresources.txt'