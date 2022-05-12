docker service rm ${SWARMNAME}_eth
sleep 1
docker stack rm ${SWARMNAME}
sleep 1

if docker ps | grep -q "Up"
then
	echo "Stopped containers:"
	docker stop $(docker ps -a -q) 
	docker rm $(docker ps -a -q)
else
	echo "No containers running"
fi
