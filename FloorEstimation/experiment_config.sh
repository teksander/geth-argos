
export MAINFOLDER="$HOME/Desktop/argos-geth-python"
export DOCKERFOLDER="$MAINFOLDER/argos-blockchain"
export ARGOSFOLDER="$MAINFOLDER/argos-python"
export EXPERIMENTFOLDER="$MAINFOLDER/FloorEstimation"

BLOCKCHAINPATH="$HOME/eth_data_para/data"
CONTAINERNAMEBASE="ethereum_eth."
ARGOSTEMPLATE="$EXPERIMENTFOLDER/experiments/estimation-large.argosx"
ARGOSFILE="$EXPERIMENTFOLDER/experiments/estimation-large.argos"

GENESISFILE="${DOCKERFOLDER}/geth/files/genesis_poa.json"
SCTEMPLATE="${DOCKERFOLDER}/geth/shared/experiment_volker.sol" # <- this is the smart contract you want to use
CONTRACTADDRESS="${DOCKERFOLDER}/geth/deployed_contract/contractAddress.txt"
CONTRACTABI="${DOCKERFOLDER}/geth/deployed_contract/Estimation.abi"

# SCOUTFILE="${DOCKERFOLDER}/geth/shared/Estimation.sol"


