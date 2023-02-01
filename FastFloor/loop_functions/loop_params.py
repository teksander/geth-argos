#!/usr/bin/env python3
# Experimental parameters used in loop and qt_user functions
# Reqs: parameter dictionary is named "params"

import math
import os

# All environment variables
params = dict()
params['environ'] = os.environ

# Generic parameters; include adaptations of environment variables
params['generic'] = dict()
params['generic']['time_limit'] = float(os.environ["TIMELIMIT"]) * 60
params['generic']['arena_size'] = float(os.environ["ARENADIM"])
params['generic']['num_robots'] = int(os.environ["NUMROBOTS"])
params['generic']['seed']       = 358 # None for randomgen
params['generic']['tps'] = eval(os.environ["TPS"])
params['generic']['num_1'] = eval(os.environ["NUM1"])
params['generic']['density'] = eval(os.environ["DENSITY"])
params['generic']['arena_dim'] = eval(os.environ["ARENADIM"])
params['generic']['rab_range'] = eval(os.environ["RABRANGE"])
params['generic']['block_period'] = eval(os.environ["BLOCKPERIOD"])
params['generic']['max_workers'] = eval(os.environ["MAXWORKERS"])
params['generic']['regen_rate'] = eval(os.environ["REGENRATE"])


# Parameters for marketplace
params['market'] = dict()
params['market']['x'] = -0.25*params['generic']['arena_size']
params['market']['y'] = -0.25*params['generic']['arena_size']
# params['market']['r'] = 0.15 *params['generic']['arena_size'] * math.sqrt(1/math.pi)
params['market']['r'] = 2.5 * 0.073/2 * math.sqrt(params['generic']['num_robots'])

# Parameters for cache
params['cache'] = dict()
params['cache']['x'] = params['market']['x']
params['cache']['y'] = params['market']['y']
params['cache']['r'] = 0.07 +params['market']['r']

params['patches'] = dict()
# params['patches']['distribution'] = 'uniform' 
# params['patches']['distribution'] = 'patchy'
# params['patches']['hotspots']      = [{'x_mu': 0.25 * params['generic']['arena_size'], 
# 									     'y_mu': 0.25 * params['generic']['arena_size'], 
# 									     'x_sg': 0.15 * params['generic']['arena_size'], 
# 									     'y_sg': 0.15 * params['generic']['arena_size']}]
params['patches']['distribution'] = 'fixed' 
params['patches']['x'] = [0.25*params['generic']['arena_size']]
params['patches']['y'] = [0.25*params['generic']['arena_size']]

params['patches']['respawn']   = False
params['patches']['known']     = True
params['patches']['radius']    = 0.30
params['patches']['qtty_min']  = 100
params['patches']['qtty_max']  = 100
params['patches']['dist_min']  = 1.5 * params['cache']['r'] 
params['patches']['dist_max']  = 5 * params['cache']['r']

params['patches']['qualities'] = {'red', 'green' , 'blue', 'yellow'}
params['patches']['counts'] = {'red': 0, 'green': 0 , 'blue': 1, 'yellow': 0}
params['patches']['radii']  = {k: params['patches']['radius'] for k in params['patches']['qualities']}

# Parameters for resource economy
params['patches']['utility']     = {'red': 1, 'green':  1, 'blue': 25, 'yellow': 1}
params['patches']['forage_rate'] = {'red': 10, 'green':  8, 'blue': 0.5, 'yellow': 4}
params['patches']['regen_rate']  = {'red': 1, 'green':  2, 'blue': 9, 'yellow': 6}

params['patches']['dec_returns'] = dict()
params['patches']['dec_returns']['func']   = 'linear'                       # constant, linear or logarithmic decreasing returns
params['patches']['dec_returns']['thresh'] = params['patches']['qtty_max']  # qqty of resource before dec returns starts
params['patches']['dec_returns']['slope']  = 0.5

params['patches']['dec_returns']['func_robot']  = 'linear'                  # seconds each resource is slower than previous
params['patches']['dec_returns']['slope_robot'] = 0

# params['patches']['dec_returns']['func_robot']  = 'exp'                  # seconds each resource is slower than previous
# params['patches']['dec_returns']['slope_robot'] = 3

# params['patches']['area_percent'] = 0.005 * (10/generic_params['num_robots'])
# params['patches']['radius']    = params['generic']['arena_size']  * math.sqrt(resource_params['area_percent']/math.pi) 

# params['patches']['radius']    = params['generic']['arena_size']  * math.sqrt(resource_params['area_percent']/math.pi) 
# params['patches']['abundancy']    = 0.03
# params['patches']['frequency'] = {'red': 0.25, 'green': 0.25 , 'blue': 0.25, 'yellow': 0.25}

# Parameters for the economy
params['economy'] = dict()
params['economy']['efficiency_distribution'] = 'linear' 
params['economy']['efficiency_best'] = 1  # amps/second of best robot
params['economy']['efficiency_step'] = 0  # amps/second increase per robot ID

# Initialize the files which store QT_draw information 
params['files'] = dict()
params['files']['patches'] = 'loop_functions/patches.txt'
params['files']['robots']  = 'loop_functions/robots.txt'
params['files']['position']  = 'loop_functions/position.txt'
params['files']['rays']    = 'loop_functions/rays.txt'
