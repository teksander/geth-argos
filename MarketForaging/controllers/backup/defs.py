import multiprocess as mp
import time

from multiprocess.managers import BaseManager


def worker():
	from web3 import Web3, IPCProvider, WebsocketProvider
	from web3.middleware import geth_poa_middleware
	print('Process to host web3.py')

	provider = WebsocketProvider('ws://'+'172.18.0.11'+':8545')
	w3 = Web3(provider)
	w3.middleware_onion.inject(geth_poa_middleware, layer=0)
	w3.enable_unstable_package_management_api()
	print(w3.eth.coinbase)
	x = 5
	BaseManager.register('get_cb', callable=lambda:x)


	# def x():
	# 	return 6
	#BaseManager.register('x', callable=x)

	manager = BaseManager(address=('', 50000), authkey=b'abc')
	server = manager.get_server()
	server.serve_forever()

	return

if __name__ == '__main__':

	jobs = []
	mp.set_start_method('spawn')
	p = mp.Process(target=worker)
	jobs.append(p)
	p.start()
	time.sleep(2)

	print('test')
	m = BaseManager(address=('127.0.0.1', 50000), authkey=b'abc')
	m.connect()

	# m.register('x')
	# print(m.x())   # <------ This works!

	# w3 = m.x()
	m.register('get_cb')
	# print(m.w3.eth.coinbase)
	# print(w3.eth.coinbase)
	# while True:
	# 	time.sleep(1)


#### #### #### #### #### #### #### #### #### #### #### #### #### 


# #### #### #### #### #### #### #### #### #### #### #### #### #### 
# #### ALL CHEAP CHEAPSI SOLUTIONS; USE TCP VIA LOCALHOST?
# def identifersExtract(robotID, query = 'IP'):
#     namePrefix = 'ethereum_eth.'+str(robotID)
#     containersFile = open('identifiers.txt', 'r')
#     for line in containersFile.readlines():
#         if line.__contains__(namePrefix):
#             if query == 'IP':
#                 return line.split()[-1]
#             if query == 'ENODE':
#                 return line.split()[1]
