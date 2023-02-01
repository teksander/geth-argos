#!/usr/bin/env python3

import socket
import time
import subprocess
from console import *
import threading
import copy
from hexbytes import HexBytes

from aux import TCP_mp, TCP_server

w3 = init_web3()
sc = registerSC(w3)
bf = w3.eth.filter('latest')

##### CLEAN IT UP ALREADY ###

class TCP_server2(object):
	""" Set up TCP_server on a background thread
	The __hosting() method will be started and it will run in the background
	until the application exits.
	"""

	def __init__(self, data, host, port):
		""" Constructor
		:type data: str
		:param data: Data to be sent back upon request
		:type ip: str
		:param ip: IP address to host TCP server at
		:type port: int
		:param port: TCP listening port for enodes
		"""
		
		self.data = str(data).encode()
		self.host = host
		self.port = port  

		self.__received = dict()                            
		self.__stop = False

		logger.info('TCP-Server OK')

	def __hosting(self):
		""" This method runs in the background until program is closed """ 

		 # create a socket object
		__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
		# set important options
		__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		# bind to the port
		__socket.bind((self.host, self.port))
		# listen on the port
		__socket.listen()

		print('TCP Server OK')  

		while True:

			if self.__stop:
				__socket.close()
				break 

			else:
				# establish a connection
				__clientsocket, addr = __socket.accept()   

				# read the data
				data = __clientsocket.recv(1024)
				if data:
					self.__received = eval(data)
				else:
					self.__received = dict()

				# reply to data
				__clientsocket.send(self.data)


	def getNew(self):
		if self.__stop:
			return None
			print('TCP is OFF')
		else:
			return self.__received

	def setData(self, data):
		self.data = str(data).encode()    

	def request(self, host, port):
		msg = ""

		try:
			""" This method is used to request data from a running TCP server """
			# create the client socket
			__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
			# set the connection timeout
			__socket.settimeout(5)
			# connect to hostname on the port
			__socket.connect((host, port))                               
			# Receive no more than 1024 bytes
			msg = __socket.recv(1024)  
			msg = msg.decode('ascii') 
			__socket.close()

		except:
			print('TCP connection failed')

		return msg


	def start(self):
		""" This method is called to start __hosting a TCP server """
		if self.__stop:
			print('TCP Server already ON')  

		else:
			# Initialize background daemon thread
			thread = threading.Thread(target=self.__hosting, args=())
			thread.daemon = True 

			# Start the execution                         
			thread.start()   

	def stop(self):
		""" This method is called before a clean exit """   
		self.__stop = True
		print('TCP is OFF') 


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



global peered_IPs, peer_IPs, peers_geth

# peer_IPs is the dict {id:ip} we get from argos controller that is reset every step
peer_IPs = dict()

# peers_geth is the list of IPs we get from geth.admin 
peers_geth = []

# peered_IPs is our local buffer 
peered_IPs = set()


def peering():
	""" Control routine for robot-to-robot dynamic peering """
	global peered_IPs, peer_IPs, peers_geth
	
	peers_geth_enodes = getEnodes()
	peers_geth = set(getIps(peers_geth_enodes))
	# print(peers_geth)

	for peer_ID, peer_IP in peer_IPs.items():
		if peer_IP not in peered_IPs:
			enode = tcp_enode.request(host=peer_IP, port=5000) 
			if 'enode' in enode:
				w3.geth.admin.addPeer(enode)
				peered_IPs.add(peer_IP)
				print('Added peer: %s|%s' % (peer_ID, enode))

	temp = copy.copy(peered_IPs)

	for peer_IP in temp:
		if peer_IP not in peer_IPs.values():
			enode = tcp_enode.request(host=peer_IP, port=5000)
			if 'enode' in enode:
				w3.provider.make_request("admin_removePeer",[enode])

				peers_geth_enodes = getEnodes()
				if enode not in peers_geth_enodes:
					peered_IPs.remove(peer_IP)
					print('Removed peer: %s|%s' % (peer_IP, enode))

	# for enode in peers_geth_enodes:
	# 	peer_IP = getIp(enode)
	# 	if peer_IP not in peer_IPs.values():
	# 		w3.provider.make_request("admin_removePeer",[enode])
	# 		peered_IPs.remove(peer_IP)
	# 		print('Timed out peer: %s|%s' % (peer_ID, enode))


	peer_IPs = dict()
	tcp_peering.setData(len(peers_geth))


# Patch_key = sc.functions.Patch_key().call()
# Epoch_key = sc.functions.Epoch_key().call()
# Robot_key = sc.functions.Robot_key().call()
# Token_key = sc.functions.Token_key().call()

def l2d(l,k):
	if l:
		return {a: l[i] for i, a in enumerate(k)}
	else:
		return None

def blockHandle():
	""" Every time new blocks are synchronized """

	# patches = [l2d(x, Patch_key) for x in sc.functions.getPatches().call()]
	# for index, patch in enumerate(patches):
	# 	patches[index]['epoch'] = l2d(patch['epoch'], Epoch_key)

	# patch   = l2d(sc.functions.getPatch().call(), Patch_key)
	# patch['epoch'] = l2d(patch['epoch'], Epoch_key)

	# epochs  = [l2d(x, Epoch_key) for x in sc.functions.getEpochs().call()]
	# robot   = l2d(sc.functions.robot(w3.key).call(), Robot_key)
	# token   = l2d(sc.functions.token().call(), Token_key)
	# availiable = sc.functions.findAvailiable().call() < 9999\

	block      = dict(w3.eth.getBlock('latest'))
	ticket_price = sc.functions.getTicketPrice().call()
	am_registered = sc.functions.robot(w3.key).call()[0]
	print("I am registered", am_registered)
        
	ubi = sc.functions.askForUBI().call()
	payout = sc.functions.askForPayout().call()
	newRound = sc.functions.isNewRound().call()
	mean = sc.functions.mean().call()
	balance = w3.fromWei(w3.eth.get_balance(w3.eth.coinbase), 'ether')
	
	for key, value in block.items():
		if type(value)==HexBytes:
			block[key] = value.hex()

	tcp_calls.setData({
		'getTicketPrice': ticket_price,
		'amRegistered': am_registered,
		'askForUBI': ubi,
		'askForPayout': payout,
		'isNewRound': newRound, 
		'block': block,
		'mean': mean,
		'balance': balance
		})

if __name__ == '__main__':


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

		peer_IPs = tcp_peering.getNew()

		peering()
		
		# requests = tcp_reqs.getNew()
		# if requests:
		# 	for req in requests:
		#		eval(sc.%s().%s(*req['args']) % (req['func'],req[''])
		#

		newBlocks = bf.get_new_entries()
		if newBlocks:
			blockHandle()

		time.sleep(0.5)
