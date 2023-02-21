#!/bin/bash  

# [PATHS]
if [ $USER == "eksander" ]; then
	export MAINFOLDER="$HOME/geth-argos"

elif [ $USER == "hzhao" ]; then
	export MAINFOLDER="$HOME/blockchain-robots/geth-argos"
fi

<<<<<<< HEAD
export DOCKERFOLDER="$MAINFOLDER/argos-blockchain"
=======
export DOCKERFOLDER="$MAINFOLDER/argos-blockchain-sm"
>>>>>>> bc61d6d3386d960c32a609a8fdd94847f72cf512
export ARGOSFOLDER="$MAINFOLDER/argos-python"
export EXPERIMENTFOLDER="$MAINFOLDER/FraudForaging"
export BLOCKCHAINPATH="$HOME/eth_data_para/data"

<<<<<<< HEAD

# [FILES]
export ARGOSNAME="market-foraging"
export CONTAINERNAMEBASE="ethereum_eth."
export GENESISNAME="genesis_poa"
export CONTRACTNAME="ForagingPtManagement"

export SCTEMPLATE="${EXPERIMENTFOLDER}/scs/kmeans_estimation.sol" # <- this is the smart contract you want to use
=======
# [FILES]
export ARGOSNAME="market-foraging"
export GENESISNAME="genesis_poa"
export CONTRACTNAME="ForagingPtManagement"
export SCNAME="kmeans_estimation_3D"

>>>>>>> bc61d6d3386d960c32a609a8fdd94847f72cf512
export GENESISFILE="${DOCKERFOLDER}/geth/files/$GENESISNAME.json"
export CONTRACTADDRESS="${EXPERIMENTFOLDER}/scs/contractAddress.txt"
export CONTRACTABI="${EXPERIMENTFOLDER}/scs/build/$CONTRACTNAME.abi"
export CONTRACTBIN="${EXPERIMENTFOLDER}/scs/build/$CONTRACTNAME.bin-runtime"
<<<<<<< HEAD

export SCFILE="${EXPERIMENTFOLDER}/scs/kmeans_estimation_3D.sol"
export SCTEMPLATE="${EXPERIMENTFOLDER}/scs/kmeans_estimation_3D.x.sol"

export ARGOSFILE="${EXPERIMENTFOLDER}/experiments/market-foraging.argos"
export ARGOSTEMPLATE="${EXPERIMENTFOLDER}/experiments/market-foraging.argosx"


=======
export SCFILE="${EXPERIMENTFOLDER}/scs/$SCNAME.sol"
export SCTEMPLATE="${EXPERIMENTFOLDER}/scs/$SCNAME.x.sol"
export ARGOSFILE="${EXPERIMENTFOLDER}/experiments/market-foraging.argos"
export ARGOSTEMPLATE="${EXPERIMENTFOLDER}/experiments/market-foraging.argosx"

# [DOCKER]
export SWARMNAME=ethereum
export CONTAINERBASE=${SWARMNAME}_eth
>>>>>>> bc61d6d3386d960c32a609a8fdd94847f72cf512

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
<<<<<<< HEAD
export DIMS=2
=======
export DIMS=3
>>>>>>> bc61d6d3386d960c32a609a8fdd94847f72cf512
export NUMPT=100
export MAXLIFE=5
export MINREP=15
export RADIUS=10000 # 0.1
export DECIMAL_FACTOR=100000 # 1e5
export MINBALANCE=28000000000000000000
#export MINBALANCE=0

# [OTHER]
export SEED=350
export TIMELIMIT=90
export REPS=20




