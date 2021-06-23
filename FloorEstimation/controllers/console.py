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
dockerFolder = os.environ["DOCKERFOLDER"]

logging.basicConfig(format='[%(levelname)s %(name)s] %(message)s')
logger = logging.getLogger(__name__)

def init_web3(__ip = None):
	w3 = None

	if __ip:
		provider = WebsocketProvider('ws://'+__ip+':8545')
	else:
		provider = IPCProvider('~/geth-pi-pucks/geth.ipc')

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

    abiPath = dockerFolder+'/geth/deployed_contract/Estimation.abi'
    # abiPath = '/home/eksander/Desktop/HelloNeighbor/argos-blockchain'+'/geth/deployed_contract/HelloNeighbor.abi'
    abi = json.loads(open(abiPath).read())
    addressPath = dockerFolder+'/geth/deployed_contract/contractAddress.txt'
    address = '0x'+open(addressPath).read().rstrip()

    sc = w3.eth.contract(abi=abi, address=address)
    return sc

def waitForPC():
	while True:
		try:
			pc.enode = tcp.request(pc.ip, tcp.port)
			pc.key = tcp.request(pc.ip, 40422)
			w3.geth.admin.addPeer(pc.enode)
			# print('Peered to PC')
			break
		except:
			time.sleep(0.5)

def globalBuffer():
	peerFile = open('pi-pucks.txt', 'r') 
	
	for newId in peerFile:
		newId = newId.strip()
		if newId not in [peer.id for peer in peerBuffer]:
			newPeer = Peer(newId)
			newPeer.w3 = w3
			peerBuffer.append(newPeer)

	for peer in peerBuffer:
		while True:
			try:
				peer.enode = tcp.request(peer.ip, tcp.port)
				w3.geth.admin.addPeer(peer.enode)
				print('Peered to', peer.id)
				break
			except:
				time.sleep(0.5)
				
def waitForTS():
	while True:
		try:
			TIME = tcp.request(pc.ip, 40123)
			subprocess.call(["sudo","timedatectl","set-time",TIME])
			print('Synced Time')
			break
		except:
			time.sleep(1)

def getBalance():
    # Return own balance in ether
    return round(w3.fromWei(w3.eth.getBalance(me.key), 'ether'), 2)

def getEnodes():
		return [peer.enode for peer in w3.geth.admin.peers()]

def getIds():
		return [readEnode(enode) for enode in getEnodes('geth')]
	
if __name__ == '__main__':
	logger.setLevel(10)