#!/usr/bin/env python3
import os, math
import random

def load(path):
    fs_list=[]
    ffs_list = []
    if os.path.exists(path):
        with open(path,'r') as file:
            l= list(map(float,file.read().split()))
        for idx in range(generic_params['num_food_source']):
            fs_list.append([l[idx*2],l[idx*2+1]])
        for idy in range(num_malicious):
            ffs_list.append([l[(generic_params['num_food_source']+idy)*2],l[(generic_params['num_food_source']+idy)*2+1]])
        print("load source pts: ", ffs_list)
        return fs_list, ffs_list
    else:
        return  [[0,0]], [[0,0]]

# All parameters
params = dict()

# General Parameters
params['environ'] = os.environ

params['generic']=dict()
params['generic']['time_limit'] = float(os.environ["TIMELIMIT"]) * 60
params['generic']['seed']       = 350 # None for randomgen

# General Parameters
generic_params = dict()
generic_params['arena_size'] = float(os.environ["ARENASIZE"])
generic_params['num_robots'] = int(os.environ["NUMROBOTS"])
generic_params['time_limit'] = float(os.environ["TIMELIMIT"]) * 60
generic_params['seed']       = 350 
generic_params['decimal_factor'] = float(os.environ["DECIMAL_FACTOR"])
generic_params['num_food_source'] = 3
generic_params['unitPositionUncertainty'] = 0.03
generic_params['frictionUncertainty'] = 0.01
num_malicious = 0

generic_params['tps'] = eval(os.environ["TPS"])
generic_params['rab_range'] = eval(os.environ["RABRANGE"])
generic_params['block_period'] = eval(os.environ["BLOCKPERIOD"])

# home position centered as a circle
params['home']=dict()
params['home']['radius'] = 0.2
params['home']['position'] = [0, 0]


# sources positions centered as a circle
fs_list, ffs_list = load('loop_functions/source_pos.txt')

params['source']=dict()
params['source']['positions'] = fs_list
params['source']['fake_positions'] = ffs_list
params['source']['radius'] = 0.1


# Initialize the files which store QT_draw information 
#(TO-DO: Find a better way to share draw info to qtuser_function.py)
resource_file = 'loop_functions/resources.txt'
robot_file = 'loop_functions/robots.txt'
rays_file = 'loop_functions/rays.txt'
scresources_file = 'loop_functions/scresources.txt'