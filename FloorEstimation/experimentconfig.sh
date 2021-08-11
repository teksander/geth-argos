
export MAINFOLDER="$HOME/geth-argos"
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


# ARGOSTEMPLATE="$EXPERIMENTFOLDER/experiments/estimation-ludicrious.argosx"
# ARGOSFILE="$EXPERIMENTFOLDER/experiments/estimation-ludicrious.argos"
# NUMROBOTS=50


# ARGOSTEMPLATE="$EXPERIMENTFOLDER/experiments/estimation-large.argosx"
# ARGOSFILE="$EXPERIMENTFOLDER/experiments/estimation-large.argos"
# NUMROBOTS=30

# ARGOSTEMPLATE="$EXPERIMENTFOLDER/experiments/estimation-small.argosx"
# ARGOSFILE="$EXPERIMENTFOLDER/experiments/estimation-small.argos"
# NUMROBOTS=10

ARGOSTEMPLATE="$EXPERIMENTFOLDER/experiments/estimation-max.argosx"
ARGOSFILE="$EXPERIMENTFOLDER/experiments/estimation-max.argos"
NUMROBOTS=45


DENSITY=8.31
ARENADIM=$(echo "scale=3 ; sqrt($NUMROBOTS/$DENSITY)" | bc)
ARENADIMH=$(echo "scale=3 ; $ARENADIM/2" | bc)
REPETITIONS=1
VISUALIZATION=visualization # visualization or none
CELLDIMENSION="0.1"

