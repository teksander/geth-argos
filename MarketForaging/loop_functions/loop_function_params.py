#!/usr/bin/env python3
import os

# General Parameters
generic_params = dict()
generic_params['arena_size'] = float(os.environ["ARENADIM"])
generic_params['num_robots'] = int(os.environ["NUMROBOTS"])
generic_params['time_limit'] = int(os.environ["TIMELIMIT"])

# Parameters for marketplace
market_params = dict()
market_params['position'] = 'center'
market_params['size'] = 0.08 * generic_params['arena_size']  

# Parameters for new resources
resource_params = dict()
resource_params['count'] = 10 # 0.1*generic_params['num_robots']
resource_params['radius_mu'] = 0.06 * generic_params['arena_size']  
resource_params['radius_sigma'] = resource_params['radius_mu']/100
resource_params['quantity_min'] = 1
resource_params['quantity_max'] = 20
resource_params['min_distance'] = 0.25 * generic_params['arena_size']  

# Parameters for the economy
economy_params = dict()
economy_params['fuel_cost'] = 0.025 # 0.01 eth per cm travelled

# Initialize the files which store QT_draw information 
#(TO-DO: Find a better way to share draw info to qtuser_function.py)
resource_file = 'resources.txt'
robot_file = 'robots.txt'
rays_file = 'rays.txt'