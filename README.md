============ geth-argos ===============
==                                   ==
== ARGoS Blockchain Python Interface ==
==                                   ==
=======================================

AUTHOR: 

Alexandre Pacheco  <alexandre.melo.pacheco@gmail.com>

CREDITS:

Ken Hasselmann for argos-python wrapper <https://github.com/KenN7/argos-python>

Volker Strobel for docker-geth setup <https://github.com/Pold87/blockchain-swarm-robotics>

DATE: 22/06/2021


To-do-list:

- Make RPYC server hosted in docker containers (one web3.py instance per container)
- Expose entire w3 instance in RPYC rather than individual functions
- Get ENODES from TCP not file
- Create "reset-geth.sh" which does not reinialize docker but rather reset geth folder and process in every container (if faster/more efficient)
- Improve "stop_network.sh" since docker stop and docker rm is not working properly
[DONE] open geth console with ./tmux-all for all docker containers
- Link robot ID to availiable IP in docker ()