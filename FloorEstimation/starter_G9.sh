EXPERIMENT="G9"

config_file="loop_function_params.py"
num_byzantine=0
byzantine_swarm_style=1

repetitions=2


for rep in $(seq 1 ${repetitions});
do


	killall argos3
	killall python3 # This should kill web3
	# Create config file

	echo "num_byzantine=${num_byzantine}" > $config_file
	echo "byzantine_swarm_style=${byzantine_swarm_style}" >> $config_file


	# Restart docker containers
	source starter.sh

	# Run experiment
	
	sleep 20
	argos3 -z -c $ARGOSFILE

	# Collect logged data
	bash collect-logs "rep_$rep"

done










