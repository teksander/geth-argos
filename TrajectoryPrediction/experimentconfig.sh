# [PATHS]
export HOMEFOLDER=$HOME
export MAINFOLDER="$HOMEFOLDER/geth-argos"
export DOCKERFOLDER="$MAINFOLDER/argos-blockchain-sm"
export ARGOSFOLDER="$MAINFOLDER/argos-python"
export EXPERIMENTFOLDER="$MAINFOLDER/TrajectoryPrediction"
export SERVERFOLDER="$EXPERIMENTFOLDER/tfserver"
export BLOCKCHAINPATH="$HOMEFOLDER/eth_data_para/data"

# [FILES]
export ARGOSNAME="greeter"
export GENESISNAME="genesis_poa"
export CONTRACTNAME="FederatedLearning"
export SCNAME="federatedsc3V2"

export GENESISFILE="${DOCKERFOLDER}/geth/files/$GENESISNAME.json"
export CONTRACTADDRESS="${EXPERIMENTFOLDER}/scs/contractAddress.txt"
export CONTRACTABI="${EXPERIMENTFOLDER}/scs/build/$CONTRACTNAME.abi"
export CONTRACTBIN="${EXPERIMENTFOLDER}/scs/build/$CONTRACTNAME.bin-runtime"
export SCFILE="${EXPERIMENTFOLDER}/scs/${SCNAME}.sol" 
export SCTEMPLATE="${EXPERIMENTFOLDER}/scs/${SCNAME}.x.sol" 
export ARGOSFILE="${EXPERIMENTFOLDER}/experiments/${ARGOSNAME}.argos"
export ARGOSTEMPLATE="${EXPERIMENTFOLDER}/experiments/${ARGOSNAME}.argosx"
export SERVERFILE="${SERVERFOLDER}/main.py"

# [DOCKER]
export SWARMNAME=ethereum
export CONTAINERBASE=${SWARMNAME}_eth

# [ARGOS]
export NUM1=15
export CON1="${EXPERIMENTFOLDER}/controllers/main.py"

export NUM2=0
export CON2="${EXPERIMENTFOLDER}/controllers/main_byzantine.py"

export NUMBOX=5
export NUMCYL=5

export RABRANGE="2"
export TPS=10
export DENSITY="3"

export NUMROBOTS=$(echo $NUM1+$NUM2 | bc)

export ARENADIM=5
export ARENADIMH=2
export STARTDIM=$(echo "scale=3 ; $ARENADIM*2/5" | bc)
export OBJRANGE=1.5

# export ARENADIM=$(echo "scale=3 ; sqrt($NUMROBOTS/$DENSITY)" | bc)
# export ARENADIMH=$(echo "scale=3 ; $ARENADIM/2" | bc)
# export STARTDIM=$(echo "scale=3 ; $ARENADIM/5" | bc)
export MAXWORKERS=$NUMROBOTS

# [GETH]
export BLOCKPERIOD=10

# [OTHER]
export SEED=0
export TIMELIMIT=83
export SLEEPTIME=5
export REPS=8
export NOTES=""




