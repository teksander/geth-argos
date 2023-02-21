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

from loop_function_params import params as lp
from controller_params import *
lp['generic']['show_rays'] = False

# /* Global Variables */
#######################################################################

def init():
	pass

def DrawInWorld():

	# Draw home
	rh = lp['home']['radius']
	environment.qt_draw.circle(lp['home']['position']+[0.01], [], rh,'green', True)

	rs = lp['source']['radius']
	for fs in  lp['source']['positions']:
		environment.qt_draw.circle(fs + [0.01], [], rs, 'blue', True)

	rs = lp['source']['radius']
	for fs in lp['source']['fake_positions']:
		environment.qt_draw.circle(fs + [0.01], [], rs, 'red', True)

	# Draw rays
	if lp['generic']['show_rays']:
		with open(rays_file, 'r') as f:
			for line in f:
				robotID, pos, vec_target, vec_avoid, vec_desired = eval(line)
				environment.qt_draw.ray([pos[0], pos[1] , 0.01],[pos[0] + vec_target[0], pos[1] + vec_target[1] , 0.01], 'red', 0.15)
				environment.qt_draw.ray([pos[0], pos[1] , 0.01],[pos[0] + vec_avoid[0], pos[1] + vec_avoid[1] , 0.01], 'blue', 0.15)
				environment.qt_draw.ray([pos[0], pos[1] , 0.01],[pos[0] + vec_desired[0], pos[1] + vec_desired[1] , 0.01], 'green', 0.15)

def destroy():
	print('Closing the QT window')
