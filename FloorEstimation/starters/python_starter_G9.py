import configparser
import os
import subprocess

EXPERIMENT="G9"

num_byzantine = str(2)
byzantine_swarm_style = str(1)

repetitions = 10


for rep in range(repetitions):

	# Create config file
	config = configparser.ConfigParser()
	config['parameters'] = {}
	config['parameters']['num_byzantine']= num_byzantine
	config['parameters']['byzantine_swarm_style'] = byzantine_swarm_style

	with open('loop_function_params.ini', 'w') as configfile:    # save
	    config.write(configfile)


	# Restart docker containers
	subprocess.Popen('source /home/volker/alex-stuff/geth-argos/FloorEstimation/starter.sh', shell=True, executable='/bin/bash')
	#os.system("source starter.sh")


	# Run experiment
	#os.system("argos3 -z -c experiments/estimation-small.argos")


	# Collect logged data
	#os.system("./collect-logs rep_" + str(rep))	












