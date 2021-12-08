#!/usr/bin/env python3

import random
import loop_function_params as lfp
import configparser

def init():

    # Determine which robots are Byzantines
    byzantines = random.sample(allrobots, k=lfp.num_byzantine)
    for robot in byzantines:
        robot.variables.set_byzantine_style(lfp.byzantine_swarm_style)
        print("Making robot", robot.variables.get_id(), "Byzantine.")
        robot.variables.set_attribute("isByz","True")
    
def reset():
    pass

def destroy():
    pass

def pre_step():
    pass

def post_step():
    pass

def is_experiment_finished():

    # For the long runime experiments:
    finished = False

    # Determine whether all robots have reached a consensus 
    #finished = True
    #for robot in allrobots: 
    #    finished = finished and robot.variables.get_consensus()

    return finished

def post_experiment():
    print("Finished from Python!!")





