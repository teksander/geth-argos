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

from loop_params import *
from loop_params import params as lp
from loop_helpers import *
from controller_params import *

# /* Global Variables */
#######################################################################

def init():
	pass

def DrawInWorld():

	# Draw the market
	dx = params['market']['width']/2
	dy = params['market']['height']/2
	environment.qt_draw.polygon(params['market']['position']+[0.01],[], [[-dx,-dy],[-dx,dy],[dx,dy],[dx,-dy]], 'custom2', True)

	# Draw the quarry
	dx = params['quarry']['width']/2
	dy = params['quarry']['height']/2
	environment.qt_draw.polygon(params['quarry']['position']+[0.01],[], [[-dx,-dy],[-dx,dy],[dx,dy],[dx,-dy]], 'gray70', True)

	# Draw the construction site
	dx = params['bsite']['width']/2
	dy = params['bsite']['height']/2
	environment.qt_draw.polygon(params['bsite']['position']+[0.01],[], [[-dx,-dy],[-dx,dy],[dx,dy],[dx,-dy]], 'custom', True)

	# Draw stones
	with open(lp['files']['stones'], 'r') as f:
		for line in f:
			stone = json.loads(line, object_hook=lambda d: SimpleNamespace(**d))
			environment.qt_draw.box([stone.x, stone.y, 0.01], [], [0.04,0.06,0.08],'gray40')

	# Draw lots
	with open(lp['files']['lots'], 'r') as f:
		for line in f:
			lot = json.loads(line, object_hook=lambda d: SimpleNamespace(**d))
			environment.qt_draw.box([lot.x, lot.y, 0.01], [], [params['lots']['height'], params['lots']['width'],0.01],'brown')

	# Draw stones carried by robots
	with open(lp['files']['robots'], 'r') as f:
		for line in f:
			robotID, x, y = eval(line)
			environment.qt_draw.box([x, y, 0.10], [], [0.04,0.06,0.08],'gray40')

	# Draw rays
	if lp['qt']['show_rays']:
		with open(lp['files']['rays'], 'r') as f:
			for line in f:
				robotID, pos, vec_target, vec_avoid, vec_desired = eval(line)
				environment.qt_draw.ray([pos[0], pos[1] , 0.01],[pos[0] + vec_target[0], pos[1] + vec_target[1] , 0.01], 'red', 0.15)
				environment.qt_draw.ray([pos[0], pos[1] , 0.01],[pos[0] + vec_avoid[0], pos[1] + vec_avoid[1] , 0.01], 'blue', 0.15)
				environment.qt_draw.ray([pos[0], pos[1] , 0.01],[pos[0] + vec_desired[0], pos[1] + vec_desired[1] , 0.01], 'green', 0.15)

def destroy():
	print('Closing the QT window')
	# environment.qt_draw.close_window()