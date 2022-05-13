#!/usr/bin/env python3
import sys, os

sys.path += [os.environ['EXPERIMENTFOLDER']+'/controllers', \
             os.environ['EXPERIMENTFOLDER']+'/loop_functions', \
             os.environ['EXPERIMENTFOLDER']]

import loop_params as lp
import control_params as cp

dict_list = [(name, value) for name, value in vars(lp).items() if isinstance(value, dict) and not name.startswith('__')]
dict_list.extend([(name, value) for name, value in vars(cp).items() if isinstance(value, dict) and not name.startswith('__')])

saveconfig = open(os.environ['EXPERIMENTFOLDER'] + '/logs/config.py', 'w+')

for name, param_dict in dict_list:
	saveconfig.write('%s = %s \n' % (name, repr(param_dict)))