# Interface for sending a transaction to a peer
INTERFACETEMPLATE="/root/templates/sendTransaction.txt"
TO=$1 # This is the ABI file which provides all functions of the SC
VALUE=$2
sed -e "s/TO/${TO}/g" -e "s/VALUE/${VALUE}/g" ${INTERFACETEMPLATE} > command.txt
bash /root/exec_template.sh command.txt 
