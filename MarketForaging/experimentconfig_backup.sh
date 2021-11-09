# [PATH]
export MAINFOLDER="$HOME/geth-argos"
export DOCKERFOLDER="$MAINFOLDER/argos-blockchain"
export ARGOSFOLDER="$MAINFOLDER/argos-python"
export EXPERIMENTFOLDER="$MAINFOLDER/MarketForaging"
export BLOCKCHAINPATH="$HOME/eth_data_para/data"
export CONTAINERNAMEBASE="ethereum_eth."

# [FILES]
GENESISFILE="${DOCKERFOLDER}/geth/files/genesis_poa.json"
SCTEMPLATE="${EXPERIMENTFOLDER}/scs/experiment_volker.sol" # <- this is the smart contract you want to use

CONTRACTADDRESS="${EXPERIMENTFOLDER}/scs/contractAddress.txt"
CONTRACTABI="${EXPERIMENTFOLDER}/scs/build/Estimation.abi"

ARGOSFILE="${EXPERIMENTFOLDER}/experiments/market-foraging.argos"
ARGOSTEMPLATE="${EXPERIMENTFOLDER}/experiments/market-foraging.argosx"

# [XML]
export NUMROBOTS="20"
RAB_RANGE="0.3"
VISUALIZATION=visualization # visualization or none
export DENSITY=1.5
export ARENADIM=$(echo "scale=3 ; sqrt($NUMROBOTS/$DENSITY)" | bc)
ARENADIMH=$(echo "scale=3 ; $ARENADIM/2" | bc)





