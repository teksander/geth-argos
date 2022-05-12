#!/usr/bin/env python3
import os, math, random

params = dict()
params['compass_noise']  = 15
params['scout_speed']    = 7
params['recruit_speed']  = 7
params['buy_duration']   = 30
params['explore_mu']     = float(os.environ["ARENADIMY"])/params['scout_speed']*100
params['explore_sg']     = 2

params['erbDist']  = 175
params['erbtFreq'] = 10
params['gsFreq']   = 20
