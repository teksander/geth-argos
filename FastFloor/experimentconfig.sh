# [PATHS]
export HOMEFOLDER=$HOME
export MAINFOLDER="$HOMEFOLDER/geth-argos-docker-inside"
export DOCKERFOLDER="$MAINFOLDER/argos-blockchain"
export ARGOSFOLDER="$MAINFOLDER/argos-python"
export EXPERIMENTFOLDER="$MAINFOLDER/FastFloor"
export BLOCKCHAINPATH="$HOMEFOLDER/eth_data_para/data"

# [FILES]
export ARGOSNAME="fast-floor"
export GENESISNAME="genesis_poa"
export CONTRACTNAME="MarketForaging"
export SCNAME="experiment_volker"

export GENESISFILE="${DOCKERFOLDER}/geth/files/$GENESISNAME.json"
export CONTRACTADDRESS="${EXPERIMENTFOLDER}/scs/contractAddress.txt"
export CONTRACTABI="${EXPERIMENTFOLDER}/scs/build/$CONTRACTNAME.abi"
export CONTRACTBIN="${EXPERIMENTFOLDER}/scs/build/$CONTRACTNAME.bin-runtime"
export SCFILE="${EXPERIMENTFOLDER}/scs/${SCNAME}.sol" 
export SCTEMPLATE="${EXPERIMENTFOLDER}/scs/${SCNAME}.x.sol" 
export ARGOSFILE="${EXPERIMENTFOLDER}/experiments/${ARGOSNAME}.argos"
export ARGOSTEMPLATE="${EXPERIMENTFOLDER}/experiments/${ARGOSNAME}.x.argos"

# [DOCKER]
export SWARMNAME=ethereum
export CONTAINERBASE=${SWARMNAME}_eth

# [ARGOS]

export REALTIME=true
export FLOORFILE=85.png
export NUM1=120
export NUMBYZANTINE=30
export BYZANTINESWARMSTYLE=1
export CON1="/home/ubuntu/geth-argos-docker-inside/FastFloor/controllers/main.py"


export RABRANGE=0.13
export WHEELNOISE="0"
export TPS=1
export DENSITY="1"

export NUMROBOTS=$(echo $NUM1 | bc)
export ARENADIM=4.35
export ARENADIMH=2.175
export STARTDIM=0.6

# [GETH]
export BLOCKPERIOD=15

# [SC]

# [OTHER]
export SEED=1500
export TIMELIMIT=100
export SLEEPTIME=5
export REPS=20
export NOTES="Basic long-term experiment with 120 robots and a run-time of 600 minutes"




