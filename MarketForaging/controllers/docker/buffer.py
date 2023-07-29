#!/usr/bin/env python3
import time, sys, subprocess
from hexbytes import HexBytes

from console import init_web3, registerSC
from aux import TCP_mp, TCP_server, TCP_server2, l2d

def getEnodes():
    return [peer['enode'] for peer in w3.geth.admin.peers()]

def getIps(__enodes = None):
    if __enodes:
        return [enode.split('@',2)[1].split(':',2)[0] for enode in __enodes]
    else:
        return [enode.split('@',2)[1].split(':',2)[0] for enode in getEnodes()]

def blockHandle():
	""" Every time new blocks are synchronized """

	patches = [l2d(x, Patch_key) for x in sc.functions.getPatches().call()]
	for index, patch in enumerate(patches):
		patches[index]['epoch'] = l2d(patch['epoch'], Epoch_key)

	patch   = l2d(sc.functions.getPatch().call(), Patch_key)
	patch['epoch'] = l2d(patch['epoch'], Epoch_key)

	epochs  = [l2d(x, Epoch_key) for x in sc.functions.getEpochs().call()]
	robot   = l2d(sc.functions.robot(w3.key).call(), Robot_key)
	token   = l2d(sc.functions.token().call(), Token_key)
	availiable = sc.functions.findAvailiable().call() < 9999
	block      = dict(w3.eth.getBlock('latest'))

	for key, value in block.items():
		if type(value)==HexBytes:
			block[key] = value.hex()

	tcp_calls.setData({
		'getAvailiable': availiable, 
		'getPatches': patches, 
		'getEpochs': epochs,
		'getPatch': patch, 
		'getRobot': robot,
		'token':    token,
		'block':    block
		})

if __name__ == '__main__':

	w3 = init_web3()
	sc = registerSC(w3)
	bf = w3.eth.filter('latest')

	Patch_key = sc.functions.Patch_key().call()
	Epoch_key = sc.functions.Epoch_key().call()
	Robot_key = sc.functions.Robot_key().call()
	Token_key = sc.functions.Token_key().call()

################################################################################################################
### TCP for peering ###
################################################################################################################

	host = subprocess.getoutput("ip addr | grep 172.18.0. | tr -s ' ' | cut -d ' ' -f 3 | cut -d / -f 1")
	port = 9898    


################################################################################################################
### TCP for calls ###
################################################################################################################

	data = ""
	port = 9899    

	tcp_calls = TCP_mp(data, host, port)
	tcp_calls.start()   

	blockHandle()

################################################################################################################
### TCP for enodes ###
################################################################################################################

	data = w3.enode
	host = getIps([w3.enode])[0]
	port = 5000

	tcp_enode = TCP_server(w3.enode, host, port, unlocked = True)
	tcp_enode.start()

################################################################################################################

	while True:

		newBlocks = bf.get_new_entries()
		if newBlocks:
			blockHandle()

		time.sleep(0.25)