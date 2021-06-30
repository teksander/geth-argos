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
	key = w3.eth.coinbase
	enode = w3.geth.admin.nodeInfo().enode

	logger.info('VERSION: %s', w3.clientVersion)
	logger.info('ADDRESS: %s', key)
	logger.info('ENODE: %s', enode)

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
    return round(w3.fromWei(w3.eth.getBalance(me.key), 'ether'), 2)

def getEnodes():
		return [peer.enode for peer in w3.geth.admin.peers()]

def getIds():
		return [readEnode(enode) for enode in getEnodes('geth')]
	
if __name__ == '__main__':

    w3 = init_web3()
#    myID  = open("/boot/pi-puck_id", "r").read().strip()
    myEN  = w3.geth.admin.nodeInfo().enode
    myKEY = w3.eth.coinbase
#    me = Peer(myID, myEN, myKEY)
    sc = registerSC(w3)
