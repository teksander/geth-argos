#!/bin/bash

echo "Killing geth"
killall geth

echo "Removing geth datadir"
rm -rf ~/.ethereum/devchain

echo "Restarting geth"
bash start.sh


