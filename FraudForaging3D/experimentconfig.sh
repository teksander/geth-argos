#!/bin/bash  

# [PATHS]
if [ $USER == "eksander" ]; then
	export MAINFOLDER="$HOME/geth-argos"

elif [ $USER == "ubuntu" ]; then
	export MAINFOLDER="$HOME/blockchain_robots_temp_debug/geth-argos"
fi

export DOCKERFOLDER="$MAINFOLDER/argos-blockchain-sm"
export ARGOSFOLDER="$MAINFOLDER/argos-python"
export EXPERIMENTFOLDER="$MAINFOLDER/FraudForaging3D"
export BLOCKCHAINPATH="$HOME/eth_data_para/data"

# [FILES]
export ARGOSNAME="3colors"
export GENESISNAME="genesis_poa"
export CONTRACTNAME="ForagingPtManagement"
export SCNAME="kmeans_estimation_3D"

export GENESISFILE="${DOCKERFOLDER}/geth/files/$GENESISNAME.json"
export CONTRACTADDRESS="${EXPERIMENTFOLDER}/scs/contractAddress.txt"
export CONTRACTABI="${EXPERIMENTFOLDER}/scs/build/$CONTRACTNAME.abi"
export CONTRACTBIN="${EXPERIMENTFOLDER}/scs/build/$CONTRACTNAME.bin-runtime"

export SCFILE="${EXPERIMENTFOLDER}/scs/$SCNAME.sol"
export SCTEMPLATE="${EXPERIMENTFOLDER}/scs/$SCNAME.x.sol"
export ARGOSFILE="${EXPERIMENTFOLDER}/experiments/$ARGOSNAME.argos"
export ARGOSTEMPLATE="${EXPERIMENTFOLDER}/experiments/$ARGOSNAME.x.argos"

# [DOCKER]
export SWARMNAME=ethereum
export CONTAINERBASE=${SWARMNAME}_eth

# [ARGOS]
export TPS=10
export RABRANGE="0.3"
export CONTROLLER="${EXPERIMENTFOLDER}/controllers/mainloop_fraud.py"
export NUM1A=10
export NUM1B=0
export NUM2=0
export NUMROBOTS=$(echo $NUM1A+$NUM1B+$NUM2 | bc)

export SIDE_W=0.01
export SIDE_H=0.1
export SIDE_L=3
export COLOR_L=0.1
export ARENASIZE=$(echo "scale=2 ; $SIDE_L*2" | bc)
export SPAWNSIZE=$(echo "scale=2 ; $ARENASIZE/10" | bc)

# Calculate the coordinates of the vertices for the lights
export SIDE_LL=$(echo "scale=2; $SIDE_L*0.9" | bc)
export xA=$(echo "scale=2; -$SIDE_LL/2" | bc)
export yA=$(echo "scale=2; -sqrt(3)*$SIDE_LL/6" | bc)
export xB=$(echo "scale=2; $SIDE_LL/2" | bc)
export yB=$(echo "scale=2; -sqrt(3)*$SIDE_LL/6" | bc)
export xC=0
export yC=$(echo "scale=2; sqrt(3)*$SIDE_LL/3" | bc)

# Calculate the coordinates of the midpoints for the walls
export xAB=$(echo "scale=2; 0" | bc)
export yAB=$(echo "scale=2; -sqrt(3)*$SIDE_L/6" | bc)
export xBC=$(echo "scale=2; $SIDE_L/4" | bc)
export yBC=$(echo "scale=2; sqrt(3)*$SIDE_L/12" | bc)
export xAC=$(echo "scale=2; -$SIDE_L/4" | bc)
export yAC=$(echo "scale=2; sqrt(3)*$SIDE_L/12" | bc)

# # Calculate the height of the triangle
# height=$(echo "scale=2; sqrt(3)/2 * $SIDE_L" | bc)

# # Calculate the coordinates for line 1
# export xA=$(echo "scale=2; 0" | bc)
# export yA=$(echo "scale=2; $COLOR_L - $height" | bc)

# # Calculate the coordinates for line 2
# export xB=$(echo "scale=2; $COLOR_L/2" | bc)
# export yB=$(echo "scale=2; $height - $COLOR_L/2" | bc)

# # Calculate the coordinates for line 3
# export xC=$(echo "scale=2; -$COLOR_L/2" | bc)
# export yC=$(echo "scale=2; $height - $COLOR_L/2" | bc)

# [GETH]
export BLOCKPERIOD=2
export STARTTOKENS="0x1236efcbcbb340000"

# [SC]
export DECIMAL_FACTOR=100000 # 1e5
export MAXUNVCLUSTER=3

export DIMS=3
export NUMPT=100
export MAXLIFE=3
export MINREP=0
export RADIUS=$(echo 30*$DECIMAL_FACTOR | bc)

export TOTALASSETS=$(echo $NUMROBOTS*20000000000000000000 | bc)
export MINBALANCE=$(echo $TOTALASSETS/$MAXUNVCLUSTER*2/3 | bc)

# [OTHER]
export SEED=350
export TIMELIMIT=90
export REPS=20




