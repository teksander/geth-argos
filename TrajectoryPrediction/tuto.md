# to run the code 
first you will need to go into the right folder :
```
cd geth-argos/thesis/
```
and you will run the script which launch the docker files and the argos files : 
```
./starter -r -s
```

if the docker container are already running you can simply run 
```
./starter -s
```
This avoids to re start the docker container when they are already running and no changes have been made to them.

# change the docker container libraries 
if you want to add libraries, for example numpy, to be available in the docker container's code, you will have to bring changes to the docker file located at : 
```
/home/seb/geth-argos/argos-blockchain-sm/geth/Dockerfile
```

add the lines you need, then you will need to compile the modified dockerfile for the changes to take place.
First go in the right folder : 
```
cd geth-argos/argos-blockchain-sm/geth/
```

Once in the right folder, you will need to rebuild the docker file, to do so run :
```
docker build -t mygeth .
```
From this you can monitor with a simple command, but not really effective for proper testing, if the code you produced is working or not. For that simply run :
```
docker service logs ethereum_eth 
```

# proper monitoring

When you want to monitor the code that is executing in docker and comunicating with your argos file, you would want a view with message posted by each robot in a proper individual window. A script is has been designed to do so. 

First head to the right folder :
```
cd geth-argos/thesis/
```
Then launch the script : 
```
./tmux-all -s bash
```

you should end up in a terminal looking like this : 
![tmux](images/tmux.png "tmux")

notice that when you type something, it types it in all terminals, this is normal. Now we want to watch the results of the docker file (the prints for example) associated to each container to be printed respectively in their window. 
first head to the right folder
```
cd python_scripts
```
then we will have to kill the python process first by running : 
```
pkill -f fedlerv2.py
```
finaly you can run the buffer.py file simply by running:
```
python3 fedlerv2.py $SLOT
```

```
cd python_scripts
pkill -f fedlerv2.py
python3 fedlerv2.py $SLOT
```



