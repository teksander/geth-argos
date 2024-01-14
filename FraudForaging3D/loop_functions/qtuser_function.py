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

SIDE_W=0.01
SIDE_H=0.3
COLOR_L=0.1

SIDE_L=1.25
xL1=0.5625
yL1=0.3247
xL2=-0.5625
yL2=0.3247
xL3=0
yL3=-0.649519

SIDE_S=0.50
xS1=0
yS1=0.866025
xS2=-0.75
yS2=-0.433013
xS3=0.75
yS3=-0.433013

def init():
	pass

def draw_in_world():
	# environment.qt_draw.box([xS1,yS1,0.35], [], [SIDE_S, SIDE_W, 0.7], 'red')
	# environment.qt_draw.box([xS2,yS2,0.35], [], [SIDE_S, SIDE_W, 0.7], 'green')
	# environment.qt_draw.box([xS3,yS3,0.35], [], [SIDE_S, SIDE_W, 0.7], 'blue')
	pass

def draw_in_robot():

	# Draw circle for visibility
	environment.qt_draw.circle([0,0,0.01], [], 0.075, 'gray90', True)

	# Draw the rays seen by robots
	readings = robot.colored_blob_omnidirectional_camera.get_readings()

	closest_dist = float('inf')
	closest_index = None
	for i, (color, angle, dist) in enumerate(readings):
		if dist < closest_dist:
			closest_dist = dist
			closest_index = i
	if closest_index != None:
		color, angle, dist = readings[closest_index]
		x, y = dist*math.cos(angle)/100,  dist*math.sin(angle)/100
		environment.qt_draw.ray([0,0,0.01], [x, y, 0.01], color, 0.15)

def destroy():
	print('Closing the QT window')
