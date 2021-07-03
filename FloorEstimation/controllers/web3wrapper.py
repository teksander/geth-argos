import time
import sys
import os
experimentFolder = os.environ["EXPERIMENTFOLDER"]
sys.path.insert(1, experimentFolder)
from console import *
import rpyc
from rpyc.utils.server import ThreadedServer
from threading import Thread
import ast


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

    def isMining(self):
        return self.w3.eth.mining

    def minerStart(self):
        self.w3.geth.miner.start()

    def minerStop(self):
        self.w3.geth.miner.stop()

    def addPeer(self, __en):
        self.w3.geth.admin.addPeer(__en)

    def removePeer(self, __en):
        self.w3.provider.make_request("admin_removePeer",[__en])

    def getPeers(self):
        return self.w3.geth.admin.peers()

    def getEnode(self):
        return self.w3.geth.admin.nodeInfo().enode

    def toWei(self, value):
        return self.w3.toWei(value ,"ether")

    ############ SC WRAPPER #####################
    def transact2(self, func, arg1, arg2):
        getattr(self.sc.functions, func)(arg1).transact(ast.literal_eval(arg2))

    def transact1(self, func, arg1):
        getattr(self.sc.functions, func)().transact(ast.literal_eval(arg1))

    def transact(self, func):
        getattr(self.sc.functions, func)().transact()

    def call(self, func):
        return getattr(self.sc.functions, func)().call()

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

    def exposed_minerStart(self):
        return self.w3if.minerStart()

    def exposed_minerStop(self):
        return self.w3if.minerStop()

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

    def exposed_blockFilter(self):
        return self.w3if.blockFilter()



# Start the RPYC servers
# When the server is moved to docker, this for cycle is executed just once per container

identifiers = open('identifiers.txt', 'r')
serverList = []
for row in identifiers.readlines():

    robotID = row.split()[0]
    wsAddr = row.split()[-1]
    print(robotID, wsAddr)

    server = ThreadedServer(Web3_Wrapper_Service(wsAddr), port = 4000+int(robotID))
    t = Thread(target = server.start)
    t.daemon = True
    t.start()
    serverList.append(t)

