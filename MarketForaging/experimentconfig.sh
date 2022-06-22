# [PATHS]
export HOMEFOLDER=$HOME
export MAINFOLDER="$HOMEFOLDER/geth-argos"
export DOCKERFOLDER="$MAINFOLDER/argos-blockchain"
export ARGOSFOLDER="$MAINFOLDER/argos-python"
export EXPERIMENTFOLDER="$MAINFOLDER/MarketForaging"
export BLOCKCHAINPATH="$HOMEFOLDER/eth_data_para/data"

# [FILES]
export CONTRACTNAME="MarketForaging"
export GENESISNAME="genesis_poa"

export GENESISFILE="${DOCKERFOLDER}/geth/files/$GENESISNAME.json"
export CONTRACTADDRESS="${EXPERIMENTFOLDER}/scs/contractAddress.txt"
export CONTRACTABI="${EXPERIMENTFOLDER}/scs/build/$CONTRACTNAME.abi"
export CONTRACTBIN="${EXPERIMENTFOLDER}/scs/build/$CONTRACTNAME.bin-runtime"

export SCFILE="${EXPERIMENTFOLDER}/scs/resource_market.sol" 
export SCTEMPLATE="${EXPERIMENTFOLDER}/scs/resource_market.x.sol" 

export ARGOSFILE="${EXPERIMENTFOLDER}/experiments/market-foraging.argos"
export ARGOSTEMPLATE="${EXPERIMENTFOLDER}/experiments/market-foraging.x.argos"

# [DOCKER]
export SWARMNAME=ethereum
export CONTAINERBASE=${SWARMNAME}_eth

# [ARGOS]
export NUM1=7
export CON1="${EXPERIMENTFOLDER}/controllers/main_collab.py"

export NUM2=0
export CON2="${EXPERIMENTFOLDER}/controllers/main_greedy.py"

export RABRANGE="0.3"
export WHEELNOISE="0"
export TPS=10
export DENSITY=3

export NUMROBOTS=$(echo $NUM1+$NUM2 | bc)
export ARENADIM=$(echo "scale=3 ; sqrt($NUMROBOTS/$DENSITY)" | bc)
export ARENADIMH=$(echo "scale=3 ; $ARENADIM/2" | bc)
export STARTDIM=$(echo "scale=3 ; $ARENADIM/5" | bc)

# [GETH]
export BLOCKPERIOD=2

# [SC]
export MAXSTAKERS=10
export MAXWORKERS=$(echo $NUMROBOTS)

export STAKERSHARE=30
export WORKERSHARE=$(echo 100-$STAKERSHARE | bc)


# [OTHER]
export SEED=350
export TIMELIMIT=15
export SLEEPTIME=5
export REPS=5




