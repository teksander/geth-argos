#!/usr/bin/env python3

import random
import loop_function_params as lfp
import configparser

def init():

    # Determine which robots are Byzantines
    byzantines = random.sample(allrobots, k=lfp.num_byzantine)
    for b in byzantines:
        b.variables.set_byzantine_style(lfp.byzantine_swarm_style)
        print("Making robot", b.variables.get_id(), "Byzantine.")
    
def reset():
    pass

def destroy():
    pass

def pre_step():
    pass

def post_step():
    pass

def is_experiment_finished():

    finished = False

    # # Determine whether all robots have reached a consensus 
    # finished = True
    # for r in allrobots: 
    #     finished = finished and r.variables.get_consensus()

    # if finished:
    #     print("A consensus was reached")

    return finished

def post_experiment():
    print("Finished from Python!!")




