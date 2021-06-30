# Interface for sending a transaction to a smart contract
INTERFACETEMPLATE="/root/templates/contractInterfaceCallTemplate0.txt"
ABI=`cat /root/deployed_contract/contractABI.abi` # This is the ABI file which provides all functions of the SC
ADDRESS=`cat /root/deployed_contract/contractAddress.txt` # Address of the deployed smart contract
FUNC=$1
VALUE=0
sed -e "s/ABI/${ABI}/g" -e "s/ADDRESS/${ADDRESS}/g" -e "s/FUNC/${FUNC}/g" -e "s/VALUE/${VALUE}/g" ${INTERFACETEMPLATE} > fast_command.txt
bash /root/exec_template.sh fast_command.txt
