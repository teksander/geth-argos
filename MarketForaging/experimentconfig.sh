#!/bin/bash  

# [PATHS]
export MAINFOLDER="$HOME/geth-argos"
export DOCKERFOLDER="$MAINFOLDER/argos-blockchain"
export ARGOSFOLDER="$MAINFOLDER/argos-python"
export EXPERIMENTFOLDER="$MAINFOLDER/MarketForaging"
export BLOCKCHAINPATH="$HOME/eth_data_para/data"


# [FILES]
export CONTAINERNAMEBASE="ethereum_eth."
export CONTRACTNAME="MarketForaging"
export GENESISNAME="genesis_poa"

export SCTEMPLATE="${EXPERIMENTFOLDER}/scs/resource_market.sol" # <- this is the smart contract you want to use
export GENESISFILE="${DOCKERFOLDER}/geth/files/$GENESISNAME.json"
export CONTRACTADDRESS="${EXPERIMENTFOLDER}/scs/contractAddress.txt"
export CONTRACTABI="${EXPERIMENTFOLDER}/scs/build/$CONTRACTNAME.abi"
export CONTRACTBIN="${EXPERIMENTFOLDER}/scs/build/$CONTRACTNAME.bin-runtime"

export SCFILE="${EXPERIMENTFOLDER}/scs/resource_market.x.sol" 
export SCTEMPLATE="${EXPERIMENTFOLDER}/scs/resource_market.sol" 

export ARGOSFILE="${EXPERIMENTFOLDER}/experiments/market-foraging.argos"
export ARGOSTEMPLATE="${EXPERIMENTFOLDER}/experiments/market-foraging.argosx"



# [ARGOS]
export CONTROLLER="${EXPERIMENTFOLDER}/controllers/mainloop.py"
export NUM1=5
export NUM2=0
export RABRANGE="0.3"

export ARENADIMX=2
export ARENADIMY=2
export ARENADIMXH=$(echo "scale=3 ; $ARENADIMX/2" | bc)
export ARENADIMYH=$(echo "scale=3 ; $ARENADIMY/2" | bc)

# export DENSITY=3
export NUMROBOTS=$(echo $NUM1+$NUM2 | bc)

export STARTDIM=$(echo "scale=3 ; $ARENADIMY/5" | bc)
export TPS=10


# [DOCKER]
export SWARMNAME=robot
# export LOOPNODE=true
# export LOOPNAME=loop

# [GETH]
export BLOCKPERIOD=2

# [SC]
export MAXRECRUITS=2

# [OTHER]
export SEED=350
export TIMELIMIT=15
export REPS=2




