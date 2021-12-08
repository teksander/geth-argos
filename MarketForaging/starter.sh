# Iterate over experimental settings and start experiments
 #!/bin/sh

source experimentconfig_backup.sh

echo "MAINFOLDER IS $MAINFOLDER"

# echo "Updating the Floor image"
# echo "+-----------------------------------------------------------+"
# python3 experiments/floors/generate_floor.py

echo "Updating the ARGoS XML file"
echo "+-----------------------------------------------------------+"

sed -e "s|NUMROBOTS|$NUMROBOTS|g"\
    -e "s|FPS|$FPS|g"\
    -e "s|RAB_RANGE|$RAB_RANGE|g"\
    -e "s|NUMBYZANTINE|$NUMBYZANTINE|g"\
    -e "s|EXPERIMENTFOLDER|$EXPERIMENTFOLDER|g"\
    -e "s|FLOORFILE|$FLOORFILE|g"\
    -e "s|ARGOSFOLDER|$ARGOSFOLDER|g"\
    -e "s|ARENADIMH|$ARENADIMH|g"\
    -e "s|ARENADIM|$ARENADIM|g"\
  $ARGOSTEMPLATE > $ARGOSFILE

  
# Generate the genesis block; first: read in compiled smart contract
echo "Compiling the Smart Contract"
echo "+-----------------------------------------------------------+"

solc --overwrite --abi --bin-runtime -o  "${EXPERIMENTFOLDER}/scs/build/" $SCTEMPLATE
cp -r "${EXPERIMENTFOLDER}/scs/build/." "${DOCKERFOLDER}/geth/deployed_contract/"

BINDATA=`cat ${CONTRACTBIN}`

echo "+-----------------------------------------------------------+"

# Create genesis using puppeth
bash ${DOCKERFOLDER}/geth/files/reset-genesis ${NUMROBOTS}

echo "Deploying the Smart Contract"
echo "+-----------------------------------------------------------+"

# Insert the smart contract into the genesis 
sed -ie "s|123\": {|123\": {\n\"code\": \"0xBINDATA\",|g" ${GENESISFILE}
sed -ie "s|BINDATA|$BINDATA|g" ${GENESISFILE}

# Change the gas limit
sed -ie "s|0x47b760|0x9000000000000|g" ${GENESISFILE}

# Change the value of the pre-funded accounts
sed -ie "s|\"0x200000000000000000000000000000000000000000000000000000000000000\"|\"0x1236efcbcbb340000\"|g" ${GENESISFILE}
# 0x1236efcbcbb340000 = 21 ether
# 0xde0b6b3a7640000 = 1 ether
# Undo for the contract account (first match)
sed -ie "0,/\"0x1236efcbcbb340000\"/s//\"0x200000000000000000000000000000000000000000000000000000000000000\"/" ${GENESISFILE}

# Update the contract ABI to make it compatible with the
# geth console (latest solc and latest geth console are
# incompatibe)
cp $CONTRACTABI ./OLDABI.abi
sed -e "s|\"stateMutability\":\"payable\"|\"stateMutability\":\"payable\",\"payable\":\"true\"|g" ./OLDABI.abi > $CONTRACTABI
rm ./OLDABI.abi

if [[ $1 == "--reset-docker" ]]; then
    # Restart docker
    docker service scale ethereum_eth=0
    echo "Shuting down docker process..."
    bash ${DOCKERFOLDER}/local_scripts/stop_network.sh $NUMROBOTS

    echo "Starting new docker process..."
    # sudo systemctl restart docker.service
    bash ${DOCKERFOLDER}/local_scripts/start_network.sh $NUMROBOTS
fi

# Get containers
docker ps --format '{{.Names}} {{.ID}}' > temp1.txt
sort -o temp1.txt temp1.txt

# Create a list of IDs (temporary solution)
seq 1 $NUMROBOTS > ids.txt

# Get IPs
./exec-all.sh "ip a" | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" | grep "172." | grep -v ".255" > temp2.txt

# Collect everything in a single file
paste ids.txt temp1.txt temp2.txt > identifiers.txt
# paste ids.txt temp3.txt > enodes.txt
rm temp1.txt temp2.txt ids.txt 

# rm -r logs
# mkdir logs

echo "Starting Experiment"
echo "+-----------------------------------------------------------+"

# argos3 -c $ARGOSFILE
# sleep 2
# ./tmux-all -l monitor.log
