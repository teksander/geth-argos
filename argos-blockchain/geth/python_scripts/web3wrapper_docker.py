import time
import sys
import os
from console import *
import rpyc
from rpyc.utils.server import ThreadedServer
from threading import Thread
import ast
import socket


def toDict(dictToParse):
    # convert any 'AttributeDict' type found to 'dict'
    parsedDict = dict(dictToParse)
    for key, val in parsedDict.items():
        # check for nested dict structures to iterate through
        if  'dict' in str(type(val)).lower():
            parsedDict[key] = toDict(val)
        # convert 'HexBytes' type to 'str'
        elif 'HexBytes' in str(type(val)):
            parsedDict[key] = val.hex()
    return parsedDict


class Web3_Wrapper(object):

    def __init__(self, wsAddr):
        
        self.w3 = init_web3(wsAddr)
        self.sc = registerSC(self.w3)
        self.bf = self.w3.eth.filter('latest')

    ########## ETH WRAPPER #############
    def getKey(self):
        return self.w3.eth.coinbase

    def getBalance(self):
        return self.w3.fromWei(self.w3.eth.getBalance(self.w3.eth.coinbase), 'ether')

    def blockNumber(self):
        return self.w3.eth.blockNumber

    def getTransaction(self, txHash):
        return self.w3.eth.getTransaction(txHash)

    def getTransactionReceipt(self, txHash):
        return self.w3.eth.getTransactionReceipt(txHash)

    def isMining(self):
        return self.w3.eth.mining

    def start(self):
        self.w3.geth.miner.start()

    def stop(self):
        self.w3.geth.miner.stop()

    def addPeer(self, __en):
        self.w3.geth.admin.addPeer(__en)

    def removePeer(self, __en):
        self.w3.provider.make_request("admin_removePeer",[__en])

    def getPeers(self):
        return self.w3.geth.admin.peers()

    def getEnode(self):
        # This enode is incorrect since the IP is localhost.
        # When web3wrapper is moved into docker, it should fix the enode by reading "hostname -i"
        return self.w3.geth.admin.nodeInfo().enode

    def toWei(self, value):
        return self.w3.toWei(value ,"ether")

    def getBlock(self, blockHex):
        return toDict(self.w3.eth.getBlock(blockHex))

    def getTxPoolStatus(self):
        return self.w3.geth.txpool.status()

    ############ SC WRAPPER #####################
    def transact2(self, func, arg1, arg2):
        return getattr(self.sc.functions, func)(arg1).transact(ast.literal_eval(arg2))

    def transact1(self, func, arg1):
        getattr(self.sc.functions, func)().transact(ast.literal_eval(arg1))

    def transact(self, func):
        getattr(self.sc.functions, func)().transact()

    def call(self, func):
        return getattr(self.sc.functions, func)().call()

    def call1(self, func, arg1):
        return getattr(self.sc.functions, func)().call(ast.literal_eval(arg1))

    def call2(self, func, arg1, arg2):
        return getattr(self.sc.functions, func)(arg1).call(ast.literal_eval(arg2))

    ############ FILTER WRAPPER #####################
    def blockFilter(self): 
        return self.bf.get_new_entries()


# RPYC service definition
class Web3_Wrapper_Service(rpyc.Service):

    # def on_connect(self):
    #     print(self._conn)

    def __init__(self, wsAddr):
        self.w3if = Web3_Wrapper(wsAddr)

    def exposed_getKey(self):
        return self.w3if.getKey()

    def exposed_getBalance(self):
        return self.w3if.getBalance()

    def exposed_blockNumber(self):
        return self.w3if.blockNumber()

    def exposed_start(self):
        return self.w3if.start()

    def exposed_stop(self):
        return self.w3if.stop()

    def exposed_isMining(self):
        return self.w3if.isMining()

    def exposed_addPeer(self, enode):
        self.w3if.addPeer(enode)

    def exposed_removePeer(self, enode):
        self.w3if.removePeer(enode)

    def exposed_getPeers(self):
        return self.w3if.getPeers()

    def exposed_getEnode(self):
        return self.w3if.getEnode()

    def exposed_toWei(self, value):
        return self.w3if.toWei(value)

    def exposed_transact(self, function):
        return self.w3if.transact(function)

    def exposed_transact1(self, function, arg1):
        return self.w3if.transact1(function, str(arg1))

    def exposed_transact2(self, function, arg1, arg2):
        return self.w3if.transact2(function, arg1, str(arg2))

    def exposed_call(self, function):
        return self.w3if.call(function)

    def exposed_call1(self, function, arg1):
        return self.w3if.call1(function, str(arg1))

    def exposed_call2(self, function, arg1, arg2):
        return self.w3if.call2(function, arg1, str(arg2))

    def exposed_blockFilter(self):
        return self.w3if.blockFilter()

    def exposed_getBlock(self, blockHex):
        return self.w3if.getBlock(blockHex)

    def exposed_getTransaction(self, txHash):
        return self.w3if.getTransaction(txHash)

    def exposed_getTransactionReceipt(self, txHash):
        return self.w3if.getTransactionReceipt(txHash)

    def exposed_getTxPoolStatus(self):
        return self.w3if.getTxPoolStatus()

# Start the RPYC servers
# When the server is moved to docker, this for cycle is executed just once per container

if __name__ == '__main__':

    wsAddr = 'localhost'

    server = ThreadedServer(Web3_Wrapper_Service(wsAddr), port = 4000)
    server.start()
