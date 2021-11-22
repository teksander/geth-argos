ulimit -n 16000

for rep in $(seq 1 ${repetitions}); do
for num_byzantine in "${num_byzantines[@]}"; do
    
	killall argos3
	killall python3
	# Recreate the temporary logging folder
    base_log_folder='logs/'
    rm -rf logs
    mkdir logs

	# Create config file

	# Comment this out for all experiments except Exp. 2
	python3 experiments/generate_floor/generate_floor.py 

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
done

