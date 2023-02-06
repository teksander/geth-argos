#!/usr/bin/env python3
import os, math
import random



# All parameters
params = dict()

# General Parameters
params['environ'] = os.environ
# General Parameters
generic_params = dict()
generic_params['arena_size'] = float(os.environ["ARENADIMY"])
generic_params['num_robots'] = int(os.environ["NUMROBOTS"])
generic_params['exp_type'] = int(os.environ["EXPTYPE"])
generic_params['time_limit'] = float(os.environ["TIMELIMIT"]) * 60
generic_params['seed']       = 350 # None for randomgen
generic_params['decimal_factor'] = float(os.environ["DECIMAL_FACTOR"])
generic_params['use_wmsr'] = int(os.environ["USEWMSR"])
generic_params['num_food_source'] = int(os.environ["NUMFOOD"])
generic_params['unitPositionUncertainty'] = 0.03
generic_params['frictionUncertainty'] = 0.00
num_malicious = int(os.environ["NUM2"])
def load(path):
    fs_list=[]
    ffs_list = []
    if os.path.exists(path):
        with open(path,'r') as file:
            l= list(map(float,file.read().split()))
        for idx in range(generic_params['num_food_source']):
            print(l)
            fs_list.append([l[idx*2],l[idx*2+1]])
        for idy in range(num_malicious):
            ffs_list.append([l[(generic_params['num_food_source']+idy)*2],l[(generic_params['num_food_source']+idy)*2+1]])
        print("load source pts: ", ffs_list)
        return fs_list, ffs_list
    else:
        return  [[0,0]], [[0,0]]
generic_params['tps'] = eval(os.environ["TPS"])
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
params['home']['radius'] = 0.2
params['home']['position'] = [0, 0]

params['market']['height']   = eval(params['environ']['ARENADIMY'])
params['market']['width'] 	  = 0.5
params['market']['position'] = [0, 0]

fs_list, ffs_list = load('loop_functions/source_pos.txt')

params['source']=dict()
params['source']['positions'] = fs_list
params['source']['fake_positions'] = ffs_list
params['source']['radius'] = eval(params['environ']['FOODSOURCERADIUS'])

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