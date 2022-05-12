
# Change to this script's folder
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"

N=$1
# SLEEPTIME=20

source global_config_blockchain.sh
# source ${ARGOSFOLDER}/global_config.sh
# echo ${ARGOSFOLDER}

# Start Ethereum network using Docker 
cd ${DOCKERBASE}
docker stack rm ${SWARMNAME} >/dev/null 2>&1

rm -f ${DOCKERBASE}/geth/my_enode.enode

sleep 1

docker stack deploy -c ./docker-compose.yml ${SWARMNAME}

# sleep 5

docker service scale ${SWARMNAME}_eth=$N

# sleep 5

docker ps -q

# sleep $SLEEPTIME
