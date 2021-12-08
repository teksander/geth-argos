# [PATH]
export MAINFOLDER="$HOME/geth-argos"
export DOCKERFOLDER="$MAINFOLDER/argos-blockchain"
export ARGOSFOLDER="$MAINFOLDER/argos-python"
export EXPERIMENTFOLDER="$MAINFOLDER/MarketForaging"
export BLOCKCHAINPATH="$HOME/eth_data_para/data"
export CONTAINERNAMEBASE="ethereum_eth."

# [FILES]
CONTRACTNAME="MarketForaging"
GENESISNAME="genesis_poa"
SCTEMPLATE="${EXPERIMENTFOLDER}/scs/resource_market.sol" # <- this is the smart contract you want to use

GENESISFILE="${DOCKERFOLDER}/geth/files/$GENESISNAME.json"
CONTRACTADDRESS="${EXPERIMENTFOLDER}/scs/contractAddress.txt"
CONTRACTABI="${EXPERIMENTFOLDER}/scs/build/$CONTRACTNAME.abi"
CONTRACTBIN="${EXPERIMENTFOLDER}/scs/build/$CONTRACTNAME.bin-runtime"

ARGOSFILE="${EXPERIMENTFOLDER}/experiments/market-foraging.argos"
ARGOSTEMPLATE="${EXPERIMENTFOLDER}/experiments/market-foraging.argosx"

# [XML]
export NUMROBOTS=5
export DENSITY=1.5
export ARENADIM=$(echo "scale=3 ; sqrt($NUMROBOTS/$DENSITY)" | bc)
RAB_RANGE="0.3"
VISUALIZATION=none # visualization or none
ARENADIMH=$(echo "scale=3 ; $ARENADIM/2" | bc)


# [OTHER]
export FPS=20
export REPS=5
export SLEEPTIME=5
export TIMELIMIT=20




