#!/usr/bin/env python3
import time
import subprocess
import copy
from hexbytes import HexBytes

from console import *
from aux import TCP_mp, TCP_server, TCP_server2, l2d

def getEnodes():
    return [peer['enode'] for peer in w3.geth.admin.peers()]

def getIps(__enodes = None):
    if __enodes:
        return [enode.split('@',2)[1].split(':',2)[0] for enode in __enodes]
    else:
        return [enode.split('@',2)[1].split(':',2)[0] for enode in getEnodes()]

# peers_geth is the set [ips] we get from geth.admin 
# peers_buffer is our local buffer set [ips]
global peers_geth, peers_buffer
peers_geth, peers_buffer = set(), set()

def peering(peer_IPs):
	""" Control routine for robot-to-robot dynamic peering 
	argument: dict {id:ip} comes from ARGoS controller
	"""

	global peers_geth, peers_buffer
	
	peers_geth_enodes = getEnodes()
	peers_geth = set(getIps(peers_geth_enodes))

	for peer_ID, peer_IP in peer_IPs.items():
		if peer_IP not in peers_buffer:
			enode = tcp_enode.request(host=peer_IP, port=5000) 
			if 'enode' in enode:
				w3.geth.admin.addPeer(enode)
				peers_buffer.add(peer_IP)
				print('Added peer: %s|%s' % (peer_ID, enode))

	temp = copy.copy(peers_buffer)

	for peer_IP in temp:
		if peer_IP not in peer_IPs.values():
			enode = tcp_enode.request(host=peer_IP, port=5000)
			if 'enode' in enode:
				w3.provider.make_request("admin_removePeer",[enode])

				peers_geth_enodes = getEnodes()
				if enode not in peers_geth_enodes:
					peers_buffer.remove(peer_IP)
					print('Removed peer: %s|%s' % (peer_IP, enode))

	# for enode in peers_geth_enodes:
	# 	peer_IP = getIp(enode)
	# 	if peer_IP not in peer_IPs.values():
	# 		w3.provider.make_request("admin_removePeer",[enode])
	# 		peers_buffer.remove(peer_IP)
	# 		print('Timed out peer: %s|%s' % (peer_ID, enode))

	tcp_peering.setData(len(peers_geth))


def blockHandle():
	""" Every time new blocks are synchronized """
	pass

if __name__ == '__main__':

	w3 = init_web3()
	sc = registerSC(w3)
	bf = w3.eth.filter('latest')

################################################################################################################
### TCP for peering ###
################################################################################################################

	data = len(peers_geth)
	host = subprocess.getoutput("ip addr | grep 172.18.0. | tr -s ' ' | cut -d ' ' -f 3 | cut -d / -f 1")
	port = 9898    

	tcp_peering = TCP_server2(data, host, port)
	tcp_peering.start()   

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

		peers = tcp_peering.getNew()
		if peers:
			peering(peers)
		else:
			peering({})

		newBlocks = bf.get_new_entries()
		if newBlocks:
			blockHandle()

		time.sleep(0.25)