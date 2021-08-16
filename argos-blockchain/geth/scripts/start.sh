#!/bin/bash
set -e
sleep 12
geth --datadir=~/.ethereum/devchain init "/root/files/genesis_poa.json"
ip=`hostname -i`
GETH_OPTS=${@/KEYSTORE/$SLOT}
GETH_OPTS=${GETH_OPTS/IPADDRESS/$ip}
echo "Printing GETH_OPTS"
echo "$GETH_OPTS"
geth $GETH_OPTS&
sleep 13

bash /root/exec_template.sh "/root/templates/setEtherbase.txt"
sleep 1

bash /root/get_enode.sh
sleep 1

bash /root/exec_template.sh "/root/templates/unlockAccount.txt"
sleep 1

echo "Starting web3 wrapper"
python3 /root/python_scripts/web3wrapper_docker.py &
echo "Finished: Starting web3 wrapper"

tail -f /dev/null


