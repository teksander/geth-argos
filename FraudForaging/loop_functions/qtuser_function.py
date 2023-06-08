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

def init():
	global item_list, stone_list

	# Create a list of random quarry stones
	stone_list = []
	for i in range(0,50):
		dx = params['quarry']['width']/2
		dy = params['quarry']['height']/2
		x  = random.uniform(params['quarry']['position'][0]-dx, params['quarry']['position'][0]+dx)
		y  = random.uniform(params['quarry']['position'][1]-dy, params['quarry']['position'][1]+dy)

		stone_list.append((x, y))

def draw_in_world():

	# Draw home
	rh = params['home']['radius']
	environment.qt_draw.circle(params['home']['position']+[0.01], [], rh,'green', True)

	rs = params['source']['radius']
	for fs in  params['source']['positions']:
		environment.qt_draw.circle(fs + [0.01], [], rs, 'blue', True)

	rs = params['source']['radius']
	for fs in params['source']['fake_positions']:
		environment.qt_draw.circle(fs + [0.01], [], rs, 'red', True)
	# Draw rays
	if generic_params['show_rays']:
		with open(rays_file, 'r') as f:
			for line in f:
				robotID, pos, vec_target, vec_avoid, vec_desired = eval(line)
				environment.qt_draw.ray([pos[0], pos[1] , 0.01],[pos[0] + vec_target[0], pos[1] + vec_target[1] , 0.01], 'red', 0.15)
				environment.qt_draw.ray([pos[0], pos[1] , 0.01],[pos[0] + vec_avoid[0], pos[1] + vec_avoid[1] , 0.01], 'blue', 0.15)
				environment.qt_draw.ray([pos[0], pos[1] , 0.01],[pos[0] + vec_desired[0], pos[1] + vec_desired[1] , 0.01], 'green', 0.15)

def draw_in_robot():
	pass

def destroy():
	print('Closing the QT window')
	# environment.qt_draw.close_window()