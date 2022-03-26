#!/usr/bin/env python
from web3 import Web3, IPCProvider, WebsocketProvider
from web3.middleware import geth_poa_middleware
import os
import sys
import subprocess
import json
import time
import logging
import os

logging.basicConfig(format='[%(levelname)s %(name)s] %(message)s')
logger = logging.getLogger(__name__)

def init_web3(__ip = None):
	w3 = None
	provider = IPCProvider('/root/.ethereum/devchain/geth.ipc')

	w3 = Web3(provider)
	w3.provider = provider
	w3.middleware_onion.inject(geth_poa_middleware, layer=0)
	w3.geth.personal.unlockAccount(w3.eth.coinbase,"",0)
	w3.eth.defaultAccount = w3.eth.coinbase
	w3.key = w3.eth.coinbase
	w3.enode = w3.geth.admin.nodeInfo().enode

	logger.info('VERSION: %s', w3.clientVersion)
	logger.info('ADDRESS: %s', w3.key)
	logger.info('ENODE: %s', w3.enode)

	return w3

def registerSC(w3):
    sc = None

    abiPath = '/root/deployed_contract/' + sys.argv[1]
    abi = json.loads(open(abiPath).read())
    addressPath = '/root/deployed_contract/contractAddress.txt'
    address = '0x' + open(addressPath).read().rstrip()

    sc = w3.eth.contract(abi=abi, address=address)
    return sc
				
def getBalance():
    # Return own balance in ether
    return round(w3.fromWei(w3.eth.getBalance(w3.key), 'ether'), 2)

def getEnodes():
		return [peer.enode for peer in w3.geth.admin.peers()]

def getIds():
		return [readEnode(enode) for enode in getEnodes('geth')]
	
if __name__ == '__main__':

    w3 = init_web3()
#    myID  = open("/boot/pi-puck_id", "r").read().strip()
    myEN  = w3.geth.admin.nodeInfo().enode
    myKEY = w3.eth.coinbase
    sc = registerSC(w3)


### THIS SCRIPT NOW GOES IN CONTROLLER AND IS IMPORTED INTO ARGOS ####

# import rpyc
# import os
# import sys
# import logging
# experimentFolder = os.environ["EXPERIMENTFOLDER"]
# sys.path.insert(1, experimentFolder)

# logging.basicConfig(format='[%(levelname)s %(name)s] %(message)s')
# logger = logging.getLogger(__name__)

# def init_web3(robotID):

#     # Connect to the remove server which hosts the module web3.py
#     dockerIP = identifersExtract(robotID, 'IP')
#     conn = rpyc.classic.connect(dockerIP, 4000)
#     web3 = conn.modules.web3
#     Web3 = web3.Web3
#     IPCProvider = web3.IPCProvider
#     WebsocketProvider = web3.WebsocketProvider
#     geth_poa_middleware = web3.middleware.geth_poa_middleware

#     w3 = None
#     robotIP = identifersExtract(robotID)

#     if robotIP:
#         provider = WebsocketProvider('ws://'+robotIP+':8545')
#     else:
#         provider = IPCProvider('~/geth-pi-pucks/geth.ipc')

#     w3 = Web3(provider)
#     w3.provider = provider
#     w3.middleware_onion.inject(geth_poa_middleware, layer=0)
#     w3.geth.personal.unlockAccount(w3.eth.coinbase,"",0)
#     w3.eth.defaultAccount = w3.eth.coinbase


#     w3.key = w3.eth.coinbase
#     w3.enode = w3.geth.admin.nodeInfo().enode

#     def removePeer(enode):
#         w3.provider.make_request("admin_removePeer",[enode])

#     def getBalance(address = w3.key):
#         w3.fromWei(w3.eth.getBalance(address), 'ether')

#     w3.geth.admin.removePeer = removePeer
#     w3.getBalance = getBalance

#     logger.info('VERSION: %s', w3.clientVersion)
#     logger.info('ADDRESS: %s', w3.key)
#     logger.info('ENODE: %s', w3.enode)

#     return w3


# def identifersExtract(robotID, query = 'IP'):
#     namePrefix = 'ethereum_eth.' + str(robotID) + '.'
#     containersFile = open(experimentFolder+'/identifiers.txt', 'r')
#     for line in containersFile.readlines():
#         if line.__contains__(namePrefix):
#             if query == 'IP':
#                 return line.split()[-1]
#             if query == 'ENODE':
#                 return line.split()[1]

# if __name__=='__main__':

#     w3 = init_web3(robotID = 1)