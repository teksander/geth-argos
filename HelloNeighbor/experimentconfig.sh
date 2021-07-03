
export MAINFOLDER="$HOME/geth-argos"
export DOCKERFOLDER="$MAINFOLDER/argos-blockchain"
export ARGOSFOLDER="$MAINFOLDER/argos-python"
export EXPERIMENTFOLDER="$MAINFOLDER/HelloNeighbor"

BLOCKCHAINPATH="$HOME/eth_data_para/data"
CONTAINERNAMEBASE="ethereum_eth."

GENESISFILE="${DOCKERFOLDER}/geth/files/genesis_poa.json"
SCTEMPLATE="${DOCKERFOLDER}/geth/shared/greet.sol" # <- this is the smart contract you want to use
CONTRACTADDRESS="${DOCKERFOLDER}/geth/deployed_contract/contractAddress.txt"
CONTRACTABI="${DOCKERFOLDER}/geth/deployed_contract/HelloNeighbor.abi"

# EXPERIMENT FILES AND PARAMETERS

ARGOSTEMPLATE="$EXPERIMENTFOLDER/experiments/greeter.argosx"
ARGOSFILE="$EXPERIMENTFOLDER/experiments/greeter.argos"

NUMROBOTS=10
REPETITIONS=1
VISUALIZATION=visualization # visualization or none
ARENASIZE="1.0"

