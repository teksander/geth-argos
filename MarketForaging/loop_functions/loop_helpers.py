#!/usr/bin/env python3

# /* Import Packages */
#######################################################################
import random, math, copy
import sys, os
from aux import Vector2D

sys.path += [os.environ['EXPERIMENTFOLDER']+'/controllers', \
             os.environ['EXPERIMENTFOLDER']+'/loop_functions', \
             os.environ['EXPERIMENTFOLDER']]

from loop_params import params as lp

for file in lp['files']:
    open(file, 'w+').close()

class Stone(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self._pos = Vector2D(x,y)

    @property
    def _json(self):
        public_vars = { k:v for k,v in vars(self).items() if not k.startswith('_')}
        return str(public_vars).replace("\'", "\"")

    @property
    def _desc(self):
        return '{%s, %s}' % (self.x, self.y)

class Lot(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self._pos = Vector2D(x,y)

    @property
    def _json(self):
        public_vars = { k:v for k,v in vars(self).items() if not k.startswith('_')}
        return str(public_vars).replace("\'", "\"")

    @property
    def _desc(self):
        return '{%s, %s}' % (self.x, self.y)

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