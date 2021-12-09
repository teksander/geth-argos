#!/bin/bash
# Short script to execute a CONSOLE command on docker containers
# Assumes docker containers are running with name prefix ethereum_eth.
# 1 argument executes on all containers
# 2+ arguments executes the input robot IDs

NUM_ROB=$(docker ps | grep ethereum_eth. | wc -l) 


if [[ "$#" -eq 1 ]]; then
    for ID  in $(seq 1 $NUM_ROB); do
        CT=$(docker ps -q -f name="ethereum_eth.${ID}\.")
        # echo $ID
        docker exec -it ${CT} ${1}
    done
fi

if [ "$#" -gt 1 ]; then

    for ID in "${@:2}"
    do
        CT=$(docker ps -q -f name="ethereum_eth.${ID}\.")
        # echo $ID
		docker exec -it $CT $1
    done
fi
