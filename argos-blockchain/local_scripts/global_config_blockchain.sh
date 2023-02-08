
if [ $USER == "eksander" ]; then
	MAINFOLDER="$HOME/geth-argos"

elif [ $USER == "hzhao" ]; then
	MAINFOLDER="$HOME/blockchain-robots/geth-argos"
fi

DOCKERBASE="$MAINFOLDER/argos-blockchain"
ARGOSFOLDER="$MAINFOLDER/argos-python"
