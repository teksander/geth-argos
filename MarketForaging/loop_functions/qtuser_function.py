#!/usr/bin/env python3

# /* Import Packages */
#######################################################################
import random, math
import time, sys, os
import logging

sys.path += [os.environ['EXPERIMENTFOLDER']+'/controllers', \
             os.environ['EXPERIMENTFOLDER']+'/loop_functions', \
             os.environ['EXPERIMENTFOLDER']]

from groundsensor import Resource

from loop_params import *
from loop_params import params as lp
from control_params import *
lp['generic']['show_rays'] = False
lp['generic']['show_pos'] = True

# /* Global Variables */
#######################################################################
res_diam = 0.0125
res_height = 0.05

# Store the position of the market and cache
market   = Resource({"x":lp['market']['x'], "y":lp['market']['y'], "radius": lp['market']['radius']})
cache    = Resource({"x":lp['cache']['x'], "y":lp['cache']['y'], "radius": lp['cache']['radius']})

def init():
	global item_list

	# Create a list of random circles centered around (0,0)	
	item_list = []
	for i in range(0,100):
		
		r = (lp['patches']['radius'] - res_diam) * math.sqrt(random.random())
		theta = 2 * math.pi * random.random()

		item_list.append((r * math.cos(theta), r * math.sin(theta)))


def DrawInWorld():

	# Draw the Market
	environment.qt_draw.circle([market.x, market.y, 0.001],[], market.radius, 'custom2', True)
	environment.qt_draw.circle([cache.x, cache.y, 0.001],[], cache.radius, 'custom2', False)

	# Draw resource patches
	with open(lp['files']['patches'], 'r') as f:
		for line in f:
			res = Resource(line)
			environment.qt_draw.circle([res.x, res.y, 0.001],[], res.radius, res.quality, False)
			draw_items = min(30, res.quantity)
			for i in range(0, draw_items):
				environment.qt_draw.cylinder([res.x+item_list[i][0], res.y+item_list[i][1], 0.001],[], 0.0125, 0.05, res.quality)

	# Draw resources carried by robots
	with open(lp['files']['robots'], 'r') as f:
		for line in f:
			robotID, x, y, quality = eval(line)
			environment.qt_draw.cylinder([x, y, 0.10],[], res_diam, res_height, quality)
				
	# Draw rays
	if lp['generic']['show_rays']:
		with open(lp['files']['rays'], 'r') as f:
			for line in f:
				robotID, pos, vec_target, vec_avoid, vec_desired = eval(line)
				environment.qt_draw.ray([pos[0], pos[1] , 0.01],[pos[0] + vec_target[0], pos[1] + vec_target[1] , 0.01], 'red', 0.15)
				environment.qt_draw.ray([pos[0], pos[1] , 0.01],[pos[0] + vec_avoid[0], pos[1] + vec_avoid[1] , 0.01], 'blue', 0.15)
				environment.qt_draw.ray([pos[0], pos[1] , 0.01],[pos[0] + vec_desired[0], pos[1] + vec_desired[1] , 0.01], 'green', 0.15)
	
	# # Draw the odometry position error
	# if lp['generic']['show_pos']:
	# 	with open(lp['files']['position'], 'r') as f:
	# 		for line in f:
	# 			gps_pos, odo_pos = eval(line)
	# 			gps_pos, odo_pos = list(gps_pos)+[0.01], list(odo_pos)+[0.01]
	# 			environment.qt_draw.ray(gps_pos, odo_pos, 'red', 0.15)


	# Draw patches which are on SC
	for i in range(1,lp['generic']['num_robots']+1):
		with open(lp['environ']['DOCKERFOLDER']+'/geth/logs/%s/scresources.txt' % i, 'r') as f:	
			for line in f:
				res = Resource(line.rsplit(' ', 2)[0])

				# Draw a gray resource area
				environment.qt_draw.circle([res.x, res.y, 0.001],[], res.radius, 'gray70', True)

				# ## Draw a gray stake cylinder
				# stake = int(line.rsplit(' ', 2)[1])
				# stake_total = int(line.rsplit(' ', 2)[2])
				# environment.qt_draw.cylinder([res.x, res.y, 0.001],[], 0.015, stake/stake_total , 'gray30')

	resources = list()
	counts = list()
	for i in range(1,lp['generic']['num_robots']+1):
		with open(lp['environ']['DOCKERFOLDER']+'/geth/logs/%s/scresources.txt' % i, 'r') as f:	
			for line in f:
				if line:
					res = Resource(line.rsplit(' ', 2)[0])
					if (res.x, res.y) not in [(ressc.x,ressc.y) for ressc in resources]:
						counts.append(1)
						resources.append(res)
					else:
						counts[[(ressc.x,ressc.y) for ressc in resources].index((res.x, res.y))] += 1

	# Draw SC patch quantities and consensus
	for res in resources:
		frac = counts[resources.index(res)]/lp['generic']['num_robots']
		environment.qt_draw.circle([res.x, res.y, 0.0005],[], res.radius, 'gray90', True)
		environment.qt_draw.circle([res.x, res.y, 0.0015],[], frac*res.radius, 'gray80', True)
		for i in range(res.quantity):
			environment.qt_draw.circle([res.x+1.1*res.radius, res.y+res.radius-0.01*2*i-0.001, 0.001],[], 0.01, 'black', True)


def destroy():
	print('Closing the QT window')
	# environment.qt_draw.close_window()