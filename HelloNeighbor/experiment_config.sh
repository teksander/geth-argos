
export MAINFOLDER="$HOME/geth-argos"
export DOCKERFOLDER="$MAINFOLDER/argos-blockchain"
export ARGOSFOLDER="$MAINFOLDER/argos-python"
export EXPERIMENTFOLDER="$MAINFOLDER/HelloNeighbor"

BLOCKCHAINPATH="$HOME/eth_data_para/data"
CONTAINERNAMEBASE="ethereum_eth."
ARGOSTEMPLATE="$EXPERIMENTFOLDER/experiments/greeter.argosx"
ARGOSFILE="$EXPERIMENTFOLDER/experiments/greeter.argos"

# TEMPLATE='./experiments/epuck_EC_locale_template.argos'
# CONTRACT="${DOCKERFOLDER}/geth/shared/Estimation.sol"
GENESISFILE="${DOCKERFOLDER}/geth/files/genesis_poa.json"
SCTEMPLATE="${DOCKERFOLDER}/geth/shared/greet.sol" # <- this is the smart contract you want to use
CONTRACTADDRESS="${DOCKERFOLDER}/geth/deployed_contract/contractAddress.txt"
CONTRACTABI="${DOCKERFOLDER}/geth/deployed_contract/HelloNeighbor.abi"

# SCOUTFILE="${DOCKERFOLDER}/geth/shared/Estimation.sol"


