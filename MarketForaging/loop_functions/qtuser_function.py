
import random
import configparser
import json
from types import SimpleNamespace
from enum import Enum
import math
import os
experimentFolder = os.environ["EXPERIMENTFOLDER"]
import sys
sys.path.insert(1, experimentFolder+'/controllers')
sys.path.insert(1, experimentFolder+'/loop_functions')

from loop_function_params import *

res_diam = 0.0125
res_height = 0.05

class resource_obj(object):
    def __init__(self, x, y, radius, quantity, quality):
        self.x = x
        self.y = y
        self.radius = radius
        self.quantity = quantity
        self.quality = quality
        self.timeStamp = 0

    def getJSON(self):
        return str(vars(self)).replace("\'", "\"")


def init():
	global market, item_list

	# Create the market instance
	market = resource_obj(x = 0, y = 0, radius = market_params['radius'], quantity = 1, quality = 'yellow')

	# Create a list of random circles centered around (0,0)	
	item_list = []
	for i in range(0,100):
		
		r = (resource_params['radius_mu'] - res_diam) * math.sqrt(random.random())
		theta = 2 * math.pi * random.random()

		item_list.append((r * math.cos(theta), r * math.sin(theta)))


def DrawInWorld():

	environment.qt_draw.circle([market.x, market.y, 0.001],[], market.radius, 'yellow', True)

	with open(robot_file, 'r') as f:
		for line in f:
			robotID, x, y, quality = eval(line)
			environment.qt_draw.cylinder([x, y, 0.10],[], res_diam, res_height, quality)

	with open(resource_file, 'r') as f:
		for line in f:
			res = json.loads(line, object_hook=lambda d: SimpleNamespace(**d))
			environment.qt_draw.circle([res.x, res.y, 0.001],[], res.radius, res.quality, False)
			for i in range(0, res.quantity):
				environment.qt_draw.cylinder([res.x+item_list[i][0], res.y+item_list[i][1], 0.001],[], 0.0125, 0.05, res.quality)

	with open(rays_file, 'r') as f:
		for line in f:
			robotID, pos, vec_target, vec_avoid, vec_desired = eval(line)
			environment.qt_draw.ray([pos[0], pos[1] , 0.01],[pos[0] + vec_target[0], pos[1] + vec_target[1] , 0.01], 'red', 0.15)
			environment.qt_draw.ray([pos[0], pos[1] , 0.01],[pos[0] + vec_avoid[0], pos[1] + vec_avoid[1] , 0.01], 'blue', 0.15)
			environment.qt_draw.ray([pos[0], pos[1] , 0.01],[pos[0] + vec_desired[0], pos[1] + vec_desired[1] , 0.01], 'green', 0.15)
		

		

