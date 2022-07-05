#!/bin/bash  

# [PATHS]
export MAINFOLDER="/home/hzhao/blockchain_robots/geth-argos"
export DOCKERFOLDER="$MAINFOLDER/argos-blockchain"
export ARGOSFOLDER="$MAINFOLDER/argos-python"
export EXPERIMENTFOLDER="$MAINFOLDER/FraudForaging"
export BLOCKCHAINPATH="$HOME/eth_data_para/data"


# [FILES]
export CONTAINERNAMEBASE="ethereum_eth."
export CONTRACTNAME="ForagingPtManagement"
export GENESISNAME="genesis_poa"

export SCTEMPLATE="${EXPERIMENTFOLDER}/scs/kmeans_estimation.sol" # <- this is the smart contract you want to use
export GENESISFILE="${DOCKERFOLDER}/geth/files/$GENESISNAME.json"
export CONTRACTADDRESS="${EXPERIMENTFOLDER}/scs/contractAddress.txt"
export CONTRACTABI="${EXPERIMENTFOLDER}/scs/build/$CONTRACTNAME.abi"
export CONTRACTBIN="${EXPERIMENTFOLDER}/scs/build/$CONTRACTNAME.bin-runtime"

export SCFILE="${EXPERIMENTFOLDER}/scs/kmeans_estimation.x.sol"
export SCTEMPLATE="${EXPERIMENTFOLDER}/scs/kmeans_estimation.sol"

export ARGOSFILE="${EXPERIMENTFOLDER}/experiments/market-foraging.argos"
export ARGOSTEMPLATE="${EXPERIMENTFOLDER}/experiments/market-foraging.argosx"



# [ARGOS]
export CONTROLLER="${EXPERIMENTFOLDER}/controllers/mainloop_fraud.py"
export NUM1=10
export NUM2=0
export RABRANGE="0.3"

export ARENADIMX=2
export ARENADIMY=2
export ARENADIMXH=$(echo "scale=2 ; $ARENADIMX/2" | bc)
export ARENADIMYH=$(echo "scale=2 ; $ARENADIMY/2" | bc)



# export DENSITY=3
export NUMROBOTS=$(echo $NUM1+$NUM2 | bc)

export STARTDIM=$(echo "scale=2 ; $ARENADIMY/5" | bc)
export TPS=10

# [GETH]
export BLOCKPERIOD=2

# [SC]
export MAXRECRUITS=2
#On chain estimator
export NUMPT=100
export MAXLIFE=100
export MINREP=10
export RADIUS=10000 # 0.1
export DECIMAL_FACTOR=100000 # 1e5

# [OTHER]
export SEED=350
export TIMELIMIT=15
export REPS=2




