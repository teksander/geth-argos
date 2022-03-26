#!/usr/bin/env python3

# /* Import Packages */
#######################################################################
import random, math
import time, sys, os
import logging, threading
from types import SimpleNamespace
import json

blockchainFolder = os.environ["DOCKERFOLDER"]
experimentFolder = os.environ["EXPERIMENTFOLDER"]
sys.path.insert(1, experimentFolder+'/controllers')
sys.path.insert(1, experimentFolder+'/loop_functions')
sys.path.insert(1, experimentFolder)

from loop_function_params import *
from controller_params import *
generic_params['show_rays'] = False

# /* Global Variables */
#######################################################################
res_diam = 0.0125
res_height = 0.05


def init():
	global item_list

	# Create a list of random circles centered around (0,0)	
	item_list = []
	for i in range(0,100):
		
		r = (resource_params['radius'] - res_diam) * math.sqrt(random.random())
		theta = 2 * math.pi * random.random()

		item_list.append((r * math.cos(theta), r * math.sin(theta)))


def DrawInWorld():

	# Draw the Market
	environment.qt_draw.circle([0, 0, 0.001],[], market_params['radius'], 'brown', True)
	environment.qt_draw.circle([0, 0, 0.001],[], market_params['radius_dropoff'], 'brown', False)

	# Draw resources carried by robots
	with open(robot_file, 'r') as f:
		for line in f:
			robotID, x, y, quality = eval(line)
			environment.qt_draw.cylinder([x, y, 0.10],[], res_diam, res_height, quality)

	# Draw resource patches
	with open(resource_file, 'r') as f:
		for line in f:
			res = json.loads(line, object_hook=lambda d: SimpleNamespace(**d))
			environment.qt_draw.circle([res.x, res.y, 0.001],[], res.radius, res.quality, False)
			draw_items = min(30, res.quantity)
			for i in range(0, draw_items):
				environment.qt_draw.cylinder([res.x+item_list[i][0], res.y+item_list[i][1], 0.001],[], 0.0125, 0.05, res.quality)

	# Draw rays
	if generic_params['show_rays']:
		with open(rays_file, 'r') as f:
			for line in f:
				robotID, pos, vec_target, vec_avoid, vec_desired = eval(line)
				environment.qt_draw.ray([pos[0], pos[1] , 0.01],[pos[0] + vec_target[0], pos[1] + vec_target[1] , 0.01], 'red', 0.15)
				environment.qt_draw.ray([pos[0], pos[1] , 0.01],[pos[0] + vec_avoid[0], pos[1] + vec_avoid[1] , 0.01], 'blue', 0.15)
				environment.qt_draw.ray([pos[0], pos[1] , 0.01],[pos[0] + vec_desired[0], pos[1] + vec_desired[1] , 0.01], 'green', 0.15)

	for i in range(1,generic_params['num_robots']+1):
		with open(blockchainFolder+'/geth/logs/%s/scresources.txt' % i, 'r') as f:	
			for line in f:
				res = json.loads(line, object_hook=lambda d: SimpleNamespace(**d))
				environment.qt_draw.circle([res.x, res.y, 0.001],[], resource_params['radius'], 'gray70', True)


	resources = list()
	counts = list()
	for i in range(1,generic_params['num_robots']+1):
		with open(blockchainFolder+'/geth/logs/%s/scresources.txt' % i, 'r') as f:	
			for line in f:
				if line:
					res = json.loads(line, object_hook=lambda d: SimpleNamespace(**d))
					if (res.x, res.y) not in [(ressc.x,ressc.y) for ressc in resources]:
						counts.append(1)
						resources.append(res)
					else:
						counts[[(ressc.x,ressc.y) for ressc in resources].index((res.x, res.y))] += 1

	for res in resources:
		frac = counts[resources.index(res)]/generic_params['num_robots']
		environment.qt_draw.circle([res.x, res.y, 0.0005],[], res.radius, 'gray90', True)
		environment.qt_draw.circle([res.x, res.y, 0.0015],[], frac*res.radius, 'gray80', True)
		for i in range(res.quantity):
			environment.qt_draw.circle([res.x+1.1*res.radius, res.y+res.radius-0.01*2*i-0.001, 0.001],[], 0.01, 'black', True)


def destroy():
	print('Closing the QT window')
	# environment.qt_draw.close_window()