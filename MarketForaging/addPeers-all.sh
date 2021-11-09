#!/bin/bash
# Short script to add all peers currently in docker containers
# Assumes docker containers are running
# No arguments adds all availiable peers
# 1+ arguments adds input peer enodes (TODO)

bash exec-all.sh "cat my_enode.enode" > temp.txt 

for enode in $(cat temp.txt)
do 
	bash execGeth-all.sh "admin.addPeer($enode)" 
done

rm temp.txt
