#!/bin/bash  

# [PATHS]
if [ $USER == "eksander" ]; then
	export MAINFOLDER="$HOME/geth-argos"

elif [ $USER == "hzhao" ]; then
	export MAINFOLDER="$HOME/blockchain-robots/geth-argos"

elif [ $USER == "ubuntu" ]; then
	export MAINFOLDER="$HOME/blockchain_robots_b/geth-argos"
fi

export DOCKERFOLDER="$MAINFOLDER/argos-blockchain-sm"
export ARGOSFOLDER="$MAINFOLDER/argos-python"
export EXPERIMENTFOLDER="$MAINFOLDER/FraudForaging3D"
export BLOCKCHAINPATH="$HOME/eth_data_para/data"

# [FILES]
export ARGOSNAME="market-foraging"
export GENESISNAME="genesis_poa"
export CONTRACTNAME="ForagingPtManagement"
export SCNAME="kmeans_estimation_3D"

export GENESISFILE="${DOCKERFOLDER}/geth/files/$GENESISNAME.json"
export CONTRACTADDRESS="${EXPERIMENTFOLDER}/scs/contractAddress.txt"
export CONTRACTABI="${EXPERIMENTFOLDER}/scs/build/$CONTRACTNAME.abi"
export CONTRACTBIN="${EXPERIMENTFOLDER}/scs/build/$CONTRACTNAME.bin-runtime"
export SCFILE="${EXPERIMENTFOLDER}/scs/$SCNAME.sol"
export SCTEMPLATE="${EXPERIMENTFOLDER}/scs/$SCNAME.x.sol"
export ARGOSFILE="${EXPERIMENTFOLDER}/experiments/market-foraging.argos"
export ARGOSTEMPLATE="${EXPERIMENTFOLDER}/experiments/market-foraging.argosx"

# [DOCKER]
export SWARMNAME=ethereum
export CONTAINERBASE=${SWARMNAME}_eth

# [ARGOS]
export CONTROLLER="${EXPERIMENTFOLDER}/controllers/mainloop_fraud.py"
export NUM1A=15
export NUM1B=0
export NUM2=0
export RABRANGE="0.3"

export ARENADIMX=2
export ARENADIMY=2
export ARENADIMXH=$(echo "scale=2 ; $ARENADIMX/2" | bc)
export ARENADIMYH=$(echo "scale=2 ; $ARENADIMY/2" | bc)
export ARENADIMXE=$(echo "scale=2 ; $ARENADIMX+0.25" | bc)
export ARENADIMYE=$(echo "scale=2 ; $ARENADIMY+0.25" | bc)

# export DENSITY=3
export NUMROBOTS=$(echo $NUM1A+$NUM1B+$NUM2 | bc)

export STARTDIM=$(echo "scale=2 ; $ARENADIMY/5" | bc)
export TPS=10

# [GETH]
export BLOCKPERIOD=2

# [SC]
export MAXRECRUITS=2
#On chain estimator
export DIMS=3
export NUMPT=100
export MAXLIFE=5
export MINREP=15
export RADIUS=10000 # 0.1
export DECIMAL_FACTOR=100000 # 1e5
export MAXUNVCLUSTER=3
# shellcheck disable=SC2155
export MINBALANCE=$(echo "200000000000000000000/$MAXUNVCLUSTER" | bc)
#export MINBALANCE=0

# [OTHER]
export SEED=350
export TIMELIMIT=90
export REPS=20




