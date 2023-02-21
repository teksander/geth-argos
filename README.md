# ARGoS-Blockchain Interface in Python

This Branch is made for onchain malicious/faulty robot detection experiments.

Derived from MarketForaging experiments by Hanqing Zhao <hzhao@cim.mcgill.ca>


ORIGINAL AUTHOR: 

Alexandre Pacheco  <alexandre.melo.pacheco@gmail.com>

CREDITS:

Ken Hasselmann for argos-python wrapper <https://github.com/KenN7/argos-python>

Volker Strobel for docker-geth setup <https://github.com/Pold87/blockchain-swarm-robotics>

<<<<<<< HEAD
DATE: 22/06/2021


To-do-list:
- (DONE) Calculation of exact deposited credits based on state estimation uncertainty.
- (DONE) Food source position expiration mechanism.
- (DONE) Malicious/fault injection.
- Logging for foraging experiments

Improvements to argos-python:
-Implement IMU
=======
DATE: 15/02/2023


# Installation guide
This guide assumes a previously clean installation of Ubuntu20.04

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

Edit ```experimentconfig.sh``` and ```blockchainconfig``` files to match your paths\
Then run an experiment (HelloNeighbor is a good starting point (Not ready yet))

```
cd geth-argos/<ExperimentFolderName>
./starter -r -s
```
>>>>>>> bc61d6d3386d960c32a609a8fdd94847f72cf512
