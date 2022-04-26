#!/bin/bash
set -e
# sleep 12
geth --datadir=~/.ethereum/devchain init "/root/files/genesis_poa.json"
ip=`hostname -i`
GETH_OPTS=${@/KEYSTORE/$SLOT}
GETH_OPTS=${GETH_OPTS/IPADDRESS/$ip}

echo "Starting geth with options:"
echo "$GETH_OPTS"
geth $GETH_OPTS&
# sleep 10

# bash /root/exec_template.sh "/root/templates/setEtherbase.txt"
# sleep 1


# bash /root/exec_template.sh "/root/templates/unlockAccount.txt"
# sleep 1


echo "Removing previous log files"
rm -rf root/logs/*

echo "Starting analytics logging"
python3 /root/python_scripts/analytics.py $SLOT&

echo "Starting peering buffer"
python3 /root/python_scripts/buffer.py&

echo "Starting web3 wrapper hosting"
python3 /root/python_scripts/web3wrapper_docker.py

# sleep 1

tail -f /dev/null


