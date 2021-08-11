
export MAINFOLDER="$HOME/alex-stuff/geth-argos"
export DOCKERFOLDER="$MAINFOLDER/argos-blockchain"
export ARGOSFOLDER="$MAINFOLDER/argos-python"
export EXPERIMENTFOLDER="$MAINFOLDER/FloorEstimation"

BLOCKCHAINPATH="$HOME/eth_data_para/data"
CONTAINERNAMEBASE="ethereum_eth."

GENESISFILE="${DOCKERFOLDER}/geth/files/genesis_poa.json"
SCTEMPLATE="${EXPERIMENTFOLDER}/scs/experiment_volker.sol" # <- this is the smart contract you want to use
CONTRACTADDRESS="${EXPERIMENTFOLDER}/scs/contractAddress.txt"
CONTRACTABI="${EXPERIMENTFOLDER}/scs/build/Estimation.abi"


# EXPERIMENT FILES AND PARAMETERS

ARGOSTEMPLATE="$EXPERIMENTFOLDER/experiments/estimation-small.argosx"
ARGOSFILE="$EXPERIMENTFOLDER/experiments/estimation-small.argos"
NUMROBOTS=8

#ARGOSTEMPLATE="$EXPERIMENTFOLDER/experiments/estimation-medium.argosx"
#ARGOSFILE="$EXPERIMENTFOLDER/experiments/estimation-medium.argos"
#NUMROBOTS=16

#ARGOSTEMPLATE="$EXPERIMENTFOLDER/experiments/estimation-large.argosx"
#ARGOSFILE="$EXPERIMENTFOLDER/experiments/estimation-large.argos"
#NUMROBOTS=24


ARGOSTEMPLATE="$EXPERIMENTFOLDER/experiments/estimation-max.argosx"
ARGOSFILE="$EXPERIMENTFOLDER/experiments/estimation-max.argos"
NUMROBOTS=60

REPETITIONS=1
VISUALIZATION=visualization # visualization or none

ARENADIM="2.7"
ARENADIMH="1.35"
CELLDIMENSION="0.1"

