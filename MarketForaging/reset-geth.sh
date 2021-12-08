
source experimentconfig_backup.sh

echo "MAINFOLDER IS $MAINFOLDER"

# Restart docker
echo "Shuting down docker process..."
bash ${DOCKERFOLDER}/local_scripts/stop_network.sh $NUMROBOTS

echo "Starting new docker process..."
sudo systemctl restart docker.service
bash ${DOCKERFOLDER}/local_scripts/start_network.sh $NUMROBOTS