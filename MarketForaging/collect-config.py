#!/usr/bin/env python3
import sys, os

sys.path += [os.environ['EXPERIMENTFOLDER']+'/controllers', \
             os.environ['EXPERIMENTFOLDER']+'/loop_functions', \
             os.environ['EXPERIMENTFOLDER']]

import loop_params as lp
import control_params as cp

# Collect the loop parameters
dict_list = [(param, value) for param, value in lp.params.items() if isinstance(value, dict)]

# Collect the control parameters
dict_list.extend([('control', cp.params)])

# Collect the experiment configuration
f = open('experimentconfig.sh', 'r')
experimentconfig = f.read()
experimentparams = {param:value for param,value in os.environ.items() if param in experimentconfig}
dict_list.extend([('experiment',experimentparams)])

savefile = open(os.environ['EXPERIMENTFOLDER'] + '/logs/config.py', 'w+')
for name, param_dict in dict_list:
	savefile.write('%s = %s \n' % (name, repr(param_dict)))