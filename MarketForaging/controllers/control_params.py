#!/usr/bin/env python3
import random, math
import os

params = dict()
params['scout_speed']    = 13
params['recruit_speed']  = 13
params['buy_duration']   = 30
params['explore_mu']     = float(os.environ["ARENADIM"])/params['scout_speed']*100
params['explore_sg']     = 2
params['max_forages']    = 3

params['gsFreq']     = 20
params['erbtFreq']   = 10
params['erbDist']    = 175

# Maximum quantity of resource a robot can transport
params['maxQ'] = 10
