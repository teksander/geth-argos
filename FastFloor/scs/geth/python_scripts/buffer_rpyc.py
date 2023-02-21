#!/usr/bin/env python3

import rpyc
from rpyc.utils.server import ThreadedServer
import time
from console import *
import threading
import copy
from aux import TCP_server, Timer

w3 = init_web3()
sc = registerSC(w3)

def getEnodes():
    return [peer['enode'] for peer in w3.geth.admin.peers()]

def getEnodeById(__id, gethEnodes = None):
    if not gethEnodes:
        gethEnodes = getEnodes() 

    for enode in gethEnodes:
        if readEnode(enode, output = 'id') == __id:
            return enode

def getIds(__enodes = None):
    if __enodes:
        return [enode.split('@',2)[1].split(':',2)[0].split('.')[-1] for enode in __enodes]
    else:
        return [enode.split('@',2)[1].split(':',2)[0].split('.')[-1] for enode in getEnodes()]

def getIps(__enodes = None):
    if __enodes:
        return [enode.split('@',2)[1].split(':',2)[0] for enode in __enodes]
    else:
        return [enode.split('@',2)[1].split(':',2)[0] for enode in getEnodes()]



global clocks, peered, peers, peers_geth
peers = dict()
clocks = dict()
peers_geth = []
peered = set()

clocks['buffer'] = Timer(0.5)

def buffer():
	""" Control routine for robot-to-robot dynamic peering """
	global clocks, peered, peers, peers_geth

	while True:
		if clocks['buffer'].query(): 

			peers = rpyc_service.getPeers()
			peers_geth_enodes = getEnodes()
			peers_geth = set(getIps(peers_geth_enodes))

			for peer in peers:
				if peers[peer] not in peered:
					enode = tcp_enode.request(peers[peer], port) 

					if 'enode' in enode:
						w3.geth.admin.addPeer(enode)
						peered.add(peers[peer])
						print('Added peer#%s | %s' % (peer, enode))

			temp = copy.copy(peered)

			for peer in temp:
				if peer not in peers.values():
					enode = tcp_enode.request(peer, port)
					if 'enode' in enode:
						w3.provider.make_request("admin_removePeer",[enode])
						peered.remove(peer)
						print('Removed peer#%s | %s' % (peer, enode))

			# for peer in peers_geth:
			# 	if peer not in peers.values():
			# 		enode = tcp_enode.request(peer, port)
			# 		w3.provider.make_request("admin_removePeer",[enode])
			# 		print('Removed peer: %s|%s' % (peer, enode))


# Create an exposed wrapper for web3
class Web3_Wrapper_Service(rpyc.Service):

	def __init__(self):
		self.peers_erb = dict()

	def exposed_sendPeers(self, peers):
		self.peers_erb = eval(peers)

	def exposed_getCount(self):
		return len(peers_geth)

	def getPeers(self):
		return self.peers_erb



if __name__ == '__main__':

	data = w3.enode
	host = getIps([w3.enode])[0]
	port = 5001

	tcp_enode = TCP_server(data, host, port, unlocked = True)
	tcp_enode.start()

	rpyc_service = Web3_Wrapper_Service()

	bufferTh = threading.Thread(target=buffer)
	bufferTh.start()

	rpyc_server = ThreadedServer(rpyc_service, port = 4001)
	rpyc_server.start()


