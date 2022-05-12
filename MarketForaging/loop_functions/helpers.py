#!/usr/bin/env python3

# /* Import Packages */
#######################################################################
import random, math, copy
import sys, os

sys.path += [os.environ['EXPERIMENTFOLDER']+'/controllers', \
             os.environ['EXPERIMENTFOLDER']+'/loop_functions', \
             os.environ['EXPERIMENTFOLDER']]

from loop_function_params import *

class Location(object):
    def __init__(self, x, y, radius, quantity, quality):
        self.x = x
        self.y = y
        self.radius = radius
        self.quantity = quantity
        self.quality = quality
        self.utility = resource_params['utility'][self.quality]

    def getJSON(self):
        return str(vars(self)).replace("\'", "\"")

def is_in_circle(point, center, radius):
    dx = abs(point[0] - center[0])
    dy = abs(point[1] - center[1])

    if dx**2 + dy**2 <= radius**2:
        return True 
    else:
        return False

def is_in_rectangle(point, center, width, height):
    dx = abs(point[0] - center[0])
    dy = abs(point[1] - center[1])

    if dx < width/2 and dy < height/2:
        return True 
    else:
        return False

