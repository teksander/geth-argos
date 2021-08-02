docker service rm ethereum_eth
sleep 3
docker stack rm ethereum
sleep 3

if docker ps | grep -q "Up"
then
	echo "Stopped containers:"
	docker stop $(docker ps -a -q) 
	docker rm $(docker ps -a -q)
else
	echo "No containers running"
fi
