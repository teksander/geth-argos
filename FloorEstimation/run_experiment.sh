<<<<<<< HEAD:FloorEstimation/starters/starter_G9.sh
EXPERIMENT="G9"

config_file="loop_function_params.py"
num_byzantine=6
byzantine_swarm_style=1
repetitions=10
SLEEPTIME=20
robots=24

=======
>>>>>>> 7b3b6c92e1b5203d3965bf8df45d44f36b7a4b6c:FloorEstimation/run_experiment.sh
for rep in $(seq 1 ${repetitions});
do


	killall argos3
	killall python3
	# Recreate the temporary logging folder
    base_log_folder='logs/'
    rm -rf logs
    mkdir logs

	# Create config file

	echo "num_byzantine=${num_byzantine}" > $python_config_file
	echo "byzantine_swarm_style=${byzantine_swarm_style}" >> $python_config_file


	# Restart docker containers
	source starter.sh

	# Run experiment
	
	sleep $SLEEPTIME
	argos3 -z -c $ARGOSFILE

	sleep 5
	# Collect logged data
	bash collect-logs "Experiment_${EXPERIMENT}/${robots}rob-${num_byzantine}byz-$rep"
	echo "Experiment_${EXPERIMENT}/${robots}rob-${num_byzantine}byz-$rep"

	sleep 5

done

