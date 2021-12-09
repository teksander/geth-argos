 #!/bin/bash
# Iterate over experimental settings and start experiments


source experimentconfig_backup.sh

echo "MAINFOLDER IS $MAINFOLDER"

# echo "Updating the Floor image"
# echo "+-----------------------------------------------------------+"
# python3 experiments/floors/generate_floor.py

echo "Updating the ARGoS XML file"
echo "+-----------------------------------------------------------+"

sed -e "s|NUMROBOTS|$NUMROBOTS|g"\
    -e "s|STARTDIM|$STARTDIM|g"\
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
bash ${DOCKERFOLDER}/geth/files/reset-genesis ${NUMROBOTS} $BLOCKPERIOD

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


if [[ $1 == "--reset-geth" ]]; then
    ./reset-geth
fi

# Get containers
docker ps --format '{{.Names}} {{.ID}}' > temp1.txt
sort -o temp1.txt temp1.txt

# Create a list of IDs (temporary solution)
seq 1 $NUMROBOTS > ids.txt

# Get IPs
./bash-all "ip a" | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" | grep "172." | grep -v ".255" > temp2.txt

# Collect everything in a single file
paste ids.txt temp1.txt temp2.txt > identifiers.txt
# paste ids.txt temp3.txt > enodes.txt
rm temp1.txt temp2.txt ids.txt 


echo "Cleaning logs folder..."
echo "+-----------------------------------------------------------+"

# Keep files 0-$NUMROBOTS in order to prevent having to reopen logs
eval $(echo "rm -rf logs/{$(($NUMROBOTS+1))..100}")


echo "Waiting web3 to respond..."
echo "+-----------------------------------------------------------+"

ready=0
while [[ $ready != $NUMROBOTS ]]; do
    ready=0
    for host in $(awk '{print $4}' identifiers.txt); do
        if echo -e '\x1dclose\x0d' | telnet $host 4000 2>/dev/null | grep -q Connected ; then
            let "ready=ready+1"
        fi
    done
done

if [[ $2 == "--start" ]]; then
    echo "Starting Experiment"
    echo "+-----------------------------------------------------------+"

    argos3 -c $ARGOSFILE
fi
