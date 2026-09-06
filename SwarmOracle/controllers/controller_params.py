#!/usr/bin/env python3
import random, math
import os

params = dict()
params['scout_speed']    = 7
params['recruit_speed']  = 7
params['buy_duration']   = 30
params['explore_mu']     = float(os.environ["ARENASIZE"])/params['scout_speed']*100
params['explore_sg']     = 2
