#!/bin/bash
# Short script to execute a GETH command on docker containers
# Assumes docker containers are running
# 1 argument executes on all containers
# 2+ arguments executes the input robot IDs

NUMROBOTS=$(docker ps | grep ethereum_eth. | wc -l)

if [ "$#" -eq 1 ]; then
    for robotId  in $(seq 1 $NUMROBOTS)
    do
        containerId=$(docker ps -q -f name="ethereum_eth.${robotId}\.")
        # echo $robotId
        docker exec -it $containerId bash exec_cmd.sh $1
    done
fi

if [ "$#" -gt 1 ]; then
    for robotId in "${@:2}"
    do
        containerId=$(docker ps -q -f name="ethereum_eth.${robotId}\.")
        # echo $robotId
		docker exec -it $containerId bash exec_cmd.sh $1
    done
fi

