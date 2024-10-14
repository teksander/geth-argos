# ARGoS-Blockchain Interface in Python

AUTHOR: 

Alexandre Pacheco  <alexandre.melo.pacheco@gmail.com>

CREDITS:

Ken Hasselmann for argos-python wrapper <https://github.com/KenN7/argos-python>

Volker Strobel for  setup <https://github.com/Pold87/blockchain-swarm-robotics>

DATE: 15/02/2023


# Installation guide
This guide assumes a previously clean installation of Ubuntu 20.04.6 LTS (Focal Fossa).

## ARGoS

Step 1: Download and compile ARGoS version 59 
(instructions at https://github.com/ilpincy/argos3)

Step 2: Download and compile E-puck plugin 
(instructions at https://github.com/demiurge-project/argos3-epuck)

## Docker
Step 1: Install docker
(instructions at https://docs.docker.com/engine/install/ubuntu/)

Step 2: Run docker as non-root user
(instructions at  https://docs.docker.com/engine/install/linux-postinstall)

## Put it all together

Step 1: Clone the repo

```git clone --recurse-submodules https://github.com/teksander/geth-argos.git```

Step 2: Compile ARGoS-Python

```
$ cd geth-argos/argos-python
$ git checkout temp
$ mkdir build
$ cd build
$ cmake ..
$ make
```

Step 3: Compile Docker image

```
$ cd geth-argos/argos-blockchain/geth/
$ docker build -t mygeth .
$ docker swarm init
```

Step 4: Other packages and reqs

```
$ sudo add-apt-repository ppa:ethereum/ethereum
$ sudo apt-get update
$ sudo apt-get install solc
```

```
$ sudo apt install python3-pip
$ pip3 install rpyc psutil
```

Step 5: Configuration and Run

Edit ```experimentconfig.sh``` and ```blockchainconfig.sh``` files to match your paths\
Then run an experiment (Tip: Start with HelloNeighbor. FloorEstimation is not implemented currently))

```
cd geth-argos/HelloNeighbor
./starter -r -s
```
