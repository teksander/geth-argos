#!/usr/bin/env python3
import random, math
import os

params = dict()
params['speed']    = 10

params['scout_speed']    = 2.5
params['recruit_speed']  = 7
params['buy_duration']   = 30
params['explore_mu']     = float(os.environ["ARENADIM"])/params['scout_speed']*100
params['explore_sg']     = 2
params['max_forages']    = 3

params['gsFreq']     = 20
params['erbtFreq']   = 10
params['erbDist']    = 175
