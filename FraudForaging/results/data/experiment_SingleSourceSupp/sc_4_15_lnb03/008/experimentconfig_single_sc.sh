#!/bin/bash  

# [PATHS]
export MAINFOLDER="/home/ubuntu/blockchain_robots/geth-argos"
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

export ARGOSFILE="${EXPERIMENTFOLDER}/experiments/single_source_exp.argos"
export ARGOSTEMPLATE="${EXPERIMENTFOLDER}/experiments/single_source_exp.argosx"

#experiment type 1=normal, 2=onesource lsa/wmsr 3=onesource sc

export EXPTYPE=3
export NUMFOOD=1

# [ARGOS]
export CONTROLLER="${EXPERIMENTFOLDER}/controllers/mainloop_single_sc.py"
#export NUM1A=15
export NUM1B=0
# export NUM2=0
export RABRANGE="0.3"

export USEWMSR=0

export ARENADIMX="1.5"
export ARENADIMY="1.5"
export ARENADIMXH=$(echo "scale=2 ; $ARENADIMX/2" | bc)
export ARENADIMYH=$(echo "scale=2 ; $ARENADIMY/2" | bc)
export FOODSOURCERADIUS="0.17"


# export DENSITY=3
export NUMROBOTS=$(echo $NUM1A+$NUM1B+$NUM2 | bc)

export STARTDIM=$(echo "scale=2 ; $ARENADIMY/5" | bc)
export TPS=10

# [GETH]
export BLOCKPERIOD=2

# [SC]
export MAXRECRUITS=2
#On chain estimator
export NUMPT=100
export MAXLIFE=5
#export MINREP=10
export RADIUS=25000 # 0.25
export DECIMAL_FACTOR=100000 # 1e5
#export MINBALANCE=28000000000000000000
export MINBALANCE=90000000000000000001
#export MINBALANCE=0

# [OTHER]
export SEED=350
export TIMELIMIT=120
export REPS=11




