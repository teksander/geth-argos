#!/usr/bin/env python3
import sys, os

experimentFolder = os.environ["EXPERIMENTFOLDER"]
sys.path.insert(1, experimentFolder+'/controllers')
sys.path.insert(1, experimentFolder+'/loop_functions')

import loop_function_params as lfp
import controller_params as ctp

dict_list = [(name, value) for name, value in vars(lfp).items() if isinstance(value, dict) and not name.startswith('__')]
dict_list.extend([(name, value) for name, value in vars(ctp).items() if isinstance(value, dict) and not name.startswith('__')])

saveconfig = open(experimentFolder + '/logs/config.py', 'w+')

for name, param_dict in dict_list:
	saveconfig.write('%s = %s \n' % (name, repr(param_dict)))