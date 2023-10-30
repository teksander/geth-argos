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
export NUMROBOTS=12

export SIDE_W=0.01
export SIDE_H=0.1
export COLOR_L=0.1

export SIDE_L=1.25
export ARENASIZE=$(echo "scale=2 ; $SIDE_L*2" | bc)
export SPAWNSIZE=$(echo "scale=2 ; $ARENASIZE/10" | bc)


export xL1=0.5625
export yL1=0.3247
export xL2=-0.5625
export yL2=0.3247
export xL3=0
export yL3=-0.649519

export SIDE_S=0.50
export xS1=0
export yS1=0.866025
export xS2=-0.75
export yS2=-0.433013
export xS3=0.75
export yS3=-0.433013

# Calculate the coordinates of the vertices for the lights
export F=0.95
export xV1=$(echo "scale=2; $xS1*$F" | bc)
export yV1=$(echo "scale=2; $yS1*$F" | bc)
export xV2=$(echo "scale=2; $xS2*$F" | bc)
export yV2=$(echo "scale=2; $yS2*$F" | bc)
export xV3=$(echo "scale=2; $xS3*$F" | bc)
export yV3=$(echo "scale=2; $yS3*$F" | bc)

# # Calculate the coordinates of the midpoints for the walls
# export xAB=$(echo "scale=2; 0" | bc)
# export yAB=$(echo "scale=2; -sqrt(3)*$SIDE_L/6" | bc)
# export xBC=$(echo "scale=2; $SIDE_L/4" | bc)
# export yBC=$(echo "scale=2; sqrt(3)*$SIDE_L/12" | bc)
# export xAC=$(echo "scale=2; -$SIDE_L/4" | bc)
# export yAC=$(echo "scale=2; sqrt(3)*$SIDE_L/12" | bc)

# # Calculate the height of the triangles
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

# [EXPERIMENT]
export NUM_BYZ=0
export NUM_FAU=0
export NUM_COL=0

# [GETH]
export BLOCKPERIOD=10
export STARTTOKENS="0x1236efcbcbb340000"

# [SC]
export DECIMAL_FACTOR=100000 # 1e5
export MAXUNVCLUSTER=3

export DIMS=3
export NUMPT=100
export MAXLIFE=3
export MINREP=0
export RADIUS=$(echo 50*$DECIMAL_FACTOR | bc)

export TOTALASSETS=$(echo $NUMROBOTS*20000000000000000000 | bc)
export MINBALANCE=$(echo $TOTALASSETS/$MAXUNVCLUSTER*2/3 | bc)

# [OTHER]
export SEED=350
export TIMELIMIT=20
export REPS=1
export NOTES="Variation of number of malicious robots; short runs; first test"



