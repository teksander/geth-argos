EXPERIMENT="SHARE_SECOND_BEST"

for REP in $(seq 1 ${REPS}); do

	killall argos3
	killall python3
	# Recreate the temporary logging folder
    base_log_folder='logs/'
    rm -rf logs
    mkdir logs

	# Restart docker containers
	source starter.sh

	# Run experiment
	
	sleep $SLEEPTIME
	argos3 -z -c $ARGOSFILE

	sleep 1
	# Collect logged data
	bash collect-logs "Experiment_${EXPERIMENT}/${NUMROBOTS}rob-${rep}"
	echo "Experiment_${EXPERIMENT}/${NUMROBOTS}rob-${rep}"

	sleep 1

done
done

