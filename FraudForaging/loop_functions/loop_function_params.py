#!/usr/bin/env python3
import os, math
import random

def distance(list1, list2):
    """Distance between two vectors."""
    squares = [(p-q) ** 2 for p, q in zip(list1, list2)]
    return sum(squares) ** .5

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

#home position centered as a circle
params['home']=dict()
params['home']['radius'] = 0.1
params['home']['position'] = [0, 0]

params['market']['height']   = eval(params['environ']['ARENADIMY'])
params['market']['width'] 	  = 0.5
params['market']['position'] = [0, 0]
fs_list=[]
while len(fs_list)<2:
    fs=[0,0]
    minIntSrcDist = 1.2
    interSource = False
    while distance(fs,params['home']['position'])<0.3 or distance(fs,params['home']['position'])>1.2 or not interSource:
        fs = [(random.random()-0.5)*eval(params['environ']['ARENADIMX'])*0.9,
          (random.random() - 0.5) * eval(params['environ']['ARENADIMY'])*0.9]
        interSource = True
        for pt in fs_list:
            if distance(fs,pt)<minIntSrcDist:
                interSource=False
    fs_list.append(fs)
    print(fs_list)
fs_list = [[0.3725550599792884, 0.34912730587116264], [-0.7594994838471354, -0.765297276482239]]

params['source']=dict()
params['source']['positions'] = fs_list
params['source']['radius'] = 0.1

params['quarry'] = dict()
params['quarry']['height']   = eval(params['environ']['ARENADIMY'])
params['quarry']['width'] 	 = 0.6
params['quarry']['position'] = [-eval(params['environ']['ARENADIMX'])/2 + params['quarry']['width']/2, 0]


params['csite'] = dict()
params['csite']['height']   = eval(params['environ']['ARENADIMY'])
params['csite']['width'] 	= 0.6
params['csite']['position'] = [eval(params['environ']['ARENADIMX'])/2 - params['csite']['width']/2, 0]


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

# Parameters for the economy
# economy_params = dict()
# economy_params['fuel_cost'] = 0.1 # eth per second of exploration

# Initialize the files which store QT_draw information 
#(TO-DO: Find a better way to share draw info to qtuser_function.py)
resource_file = 'loop_functions/resources.txt'
robot_file = 'loop_functions/robots.txt'
rays_file = 'loop_functions/rays.txt'
scresources_file = 'loop_functions/scresources.txt'