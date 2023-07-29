#!/usr/bin/env python3

# /* Import Packages */
#######################################################################
import random, math
import sys, os

blockchainFolder = os.environ["DOCKERFOLDER"]
experimentFolder = os.environ["EXPERIMENTFOLDER"]
sys.path.insert(1, experimentFolder+'/controllers')
sys.path.insert(1, experimentFolder+'/loop_functions')
sys.path.insert(1, experimentFolder)

from loop_functions.loop_function_params import params as lp
from controllers.controller_params import params as cp

# /* Global Variables */
#######################################################################
global robot, environment

def init():
	pass

def draw_in_world():
	pass

def draw_in_robot():

	# Draw circle for visibility
	environment.qt_draw.circle([0,0,0.01], [], 0.075, 'gray90', True)

	# Draw the rays seen by robots
	readings = robot.colored_blob_omnidirectional_camera.get_readings()
	for reading in readings:
		color, angle, dist = reading
		x, y = dist*math.cos(angle)/100,  dist*math.sin(angle)/100
		environment.qt_draw.ray([0,0,0.01], [x, y, 0.01], color, 0.15)

def destroy():
	print('Closing the QT window')
