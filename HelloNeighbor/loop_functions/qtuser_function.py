#!/usr/bin/env python3

# /* Import Packages */
#######################################################################
import time, sys, os
import logging

sys.path += [os.environ['EXPERIMENTFOLDER']+'/controllers', \
             os.environ['EXPERIMENTFOLDER']+'/loop_functions', \
             os.environ['EXPERIMENTFOLDER']]

from aux import Vector2D

from loop_params import params as lp
from control_params import params as cp

# /* Global Variables */
#######################################################################
res_diam   = 0.015
rob_diam   = 0.07/2
res_height = 0.015

# /* Global Functions */
#######################################################################

	
# /* ARGoS Functions */
#######################################################################

def init():
	pass

def DrawInWorld():
	pass
	
def destroy():
	print('Closing the QT window')







