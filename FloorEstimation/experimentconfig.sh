# This file contains FIXED parameters that are the same for ALL experiments

export repetitions=20
export SLEEPTIME=20
export MAINFOLDER="$HOME/geth-argos"
export DOCKERFOLDER="$MAINFOLDER/argos-blockchain"
export ARGOSFOLDER="$MAINFOLDER/argos-python"
export EXPERIMENTFOLDER="$MAINFOLDER/FloorEstimation"
export GENESISFILE="${DOCKERFOLDER}/geth/files/genesis_poa.json"
export SCTEMPLATE="${EXPERIMENTFOLDER}/scs/experiment_volker.sol" # <- this is the smart contract you want to use
export CONTRACTADDRESS="${EXPERIMENTFOLDER}/scs/contractAddress.txt"
export CONTRACTABI="${EXPERIMENTFOLDER}/scs/build/Estimation.abi"
export BLOCKCHAINPATH="$HOME/eth_data_para/data"
export CONTAINERNAMEBASE="ethereum_eth."
export ARGOSTEMPLATE="$EXPERIMENTFOLDER/experiments/estimation-dynamic.argosx"
export ARGOSFILE="$EXPERIMENTFOLDER/experiments/estimation-dynamic.argos"
export VISUALIZATION=visualization # visualization or none
export CELLDIMENSION="0.1"
export python_config_file="loop_function_params.py"
