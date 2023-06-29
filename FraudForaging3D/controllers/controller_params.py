#!/usr/bin/env python3
import random, math
import os

controller_params = dict()
controller_params['scout_speed']    = 7
controller_params['recruit_speed']  = 7
controller_params['buy_duration']   = 30
controller_params['explore_mu']     = float(os.environ["ARENASIZE"])/controller_params['scout_speed']*100
controller_params['explore_sg']     = 2
