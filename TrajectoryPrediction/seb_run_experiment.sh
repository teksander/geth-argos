#!/bin/bash
# note the first argument $1 should be either -t or nothing

config() {
	sed -i "s/^export ${1}=.*/export ${1}=${2}/" experimentconfig.sh
}

run() {

	# Configure experiment
	. experimentconfig.sh

	# If is a testrun
	if  [[ $2 = "--test" || $2 = "-t" ]]; then
		echo "Running test ${1}"
		. starter -r -sv -s
        python3 "tfserver/server_shutdown.py"

	else
		for REP in $(seq 1 ${REPS}); do
			echo "Runing experiment ${1}"
			echo "iteration ${REP}"

			# Perform experiment
			. starter -r -sv -sz
            #shutdown the tf server
            python3 "tfserver/server_shutdown.py"
            

			# Collect data
			if [ $# -eq 1 ]; then
			    bash collect-logs ${1}
			fi

			sleep 60
			
		done
	fi
	
	# shut down the last blockchain
	bash ../argos-blockchain-sm/local/stop-network
}

# EXP=first_security
# EXP=second_security
EXP=smart_byzantine
config "REPS" 8


# CFG=0b
# config "NUM1" 15
# config "NUM2" 0
# wait
# run    "${EXP}/${CFG}" $1

CFG=1b
config "NUM1" 14
config "NUM2" 1
wait
run    "${EXP}/${CFG}" $1

CFG=2b
config "NUM1" 13
config "NUM2" 2
wait
run    "${EXP}/${CFG}" $1

CFG=3b
config "NUM1" 12
config "NUM2" 3
wait
run    "${EXP}/${CFG}" $1

CFG=4b
config "NUM1" 11
config "NUM2" 4
wait
run    "${EXP}/${CFG}" $1

CFG=5b
config "NUM1" 10
config "NUM2" 5
wait
run    "${EXP}/${CFG}" $1

CFG=6b
config "NUM1" 9
config "NUM2" 6
wait
run    "${EXP}/${CFG}" $1

CFG=7b
config "NUM1" 8
config "NUM2" 7
wait
run    "${EXP}/${CFG}" $1