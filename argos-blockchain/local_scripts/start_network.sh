# This script should maybe be executed outside of C++ because then, we
# can use it independently of ARGoS and start the experiments after the
# initialization phase has started

# Change to this script's folder
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"

N=$1
SLEEPTIME=10

source global_config_blockchain.sh
# source ${ARGOSFOLDER}/global_config.sh
# echo ${ARGOSFOLDER}

# Start Ethereum network using Docker 
cd ${DOCKERBASE}
docker stack rm ethereum >/dev/null 2>&1

rm -f ${DOCKERBASE}/geth/my_enode.enode
sleep 5
docker stack deploy -c ./docker-compose.yml ethereum

# docker stack deploy -c ./docker-compose-bs.yml ethereum 
docker service scale ethereum_eth=$N

docker ps -q

sleep $SLEEPTIME
