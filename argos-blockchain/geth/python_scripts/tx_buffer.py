#!/usr/bin/env python3

import rpyc
from rpyc.utils.server import ThreadedServer
import time
import threading

from console import *
w3 = init_web3()
sc = registerSC(w3)
tf = w3.eth.filter('pending')

txList = []
class Transaction(object):

	def __init__(self, txHash):

		self.hash      = txHash.hex()
		self.tx        = None
		self.receipt   = None
		self.block     = w3.eth.blockNumber

		self.failed    = False
		self.reason    = ""
		self.nconfs    = 0

	def update(self):

		self.getTransaction()
		self.getTransactionReceipt()
		self.getBlock()

		if not self.tx:
			self.failed = True
			self.reason = "Tx not found"
			return False


		elif not self.receipt:
			return 0

		elif not self.receipt['status']:
			self.failed = True
			self.reason = "Tx status 0"
			return False

		else:
			self.nconfs = self.block - self.receipt['blockNumber']		
			return self.nconfs

	def getTransaction(self):
		try:
			self.tx = w3.eth.getTransaction(self.hash)
		except Exception as e:
			print(e)
			self.tx = None

	def getTransactionReceipt(self):
		try:
			self.receipt = w3.eth.getTransactionReceipt(self.hash)
		except Exception as e:
			print(e)
			self.receipt = None

	def getBlock(self):
		self.block = w3.eth.blockNumber


def txQuery(txHash, field = 'nconfs'):
	for tx in txList:
		if tx.hash == txHash:
			return tx.field


if __name__ == '__main__':

	min_confs = 10

	def update_tasks():

		while True:
			txHashes = tf.get_new_entries()

			for txHash in txHashes:
				tx = w3.eth.getTransaction(txHash)

				if tx['from'] == w3.key:
					txList.append(Transaction(txHash))

			for tx in txList:
				if tx.nconfs < min_confs:
					tx.update()

			time.sleep(0.5)

	updateTh = threading.Thread(target=update_tasks)
	updateTh.start()

		# w3.eth.sendTransaction({'from': w3.key, 'to': w3.key, 'value':1})
