
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

# SCOUTFILE="${DOCKERFOLDER}/geth/shared/Estimation.sol"

# EXPERIMENT FILES AND PARAMETERS

# ARGOSTEMPLATE="$EXPERIMENTFOLDER/experiments/estimation-large.argosx"
# ARGOSFILE="$EXPERIMENTFOLDER/experiments/estimation-large.argos"
# NUMROBOTS=20

ARGOSTEMPLATE="$EXPERIMENTFOLDER/experiments/estimation-small.argosx"
ARGOSFILE="$EXPERIMENTFOLDER/experiments/estimation-small.argos"
NUMROBOTS=10


REPETITIONS=1
VISUALIZATION=visualization # visualization or none
ARENASIZEDIM="1.0"
CELLDIMENSION="0.1"

