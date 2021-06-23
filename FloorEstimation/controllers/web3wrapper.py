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

# Some required transaction appendices
global gasLimit
global gasprice
global gas
gasLimit = 0x9000000
gasprice = 0x900000
gas = 0x90000


identifiers = open('identifiers.txt', 'r')
w3List = []
scList = []
filterList = []
for row in identifiers.readlines():
    wsAddr = row.split()[-1]
    print(wsAddr)
    w3List.append(init_web3(wsAddr))

for w3 in w3List:
    scList.append(registerSC(w3))
    filterList.append(w3.eth.filter('latest'))

identifiers.close()


class web3Interface(object):

    def getKey(self, __id):
        return w3List[__id].eth.coinbase

    def getBalance(self,__id):
        return w3List[__id].fromWei(w3List[__id].eth.getBalance(w3List[__id].eth.coinbase), 'ether')

    def blockNumber(self,__id):
        return w3List[__id].eth.blockNumber

    def minerStart(self,__id):
        w3List[__id].geth.miner.start()

    def minerStop(self,__id):
        w3List[__id].geth.miner.stop()

    def isMining(self,__id):
        return w3List[__id].eth.mining

    def addPeer(self,__id, __en):
        w3List[__id].admin.addPeer(enode)

    def removePeer(self,__id, __en):
        w3List[__id].provider.make_request("admin_removePeer",[enode])

    def toWei(self, __id, value):
        return w3List[__id].toWei(value ,"ether")

class scInterface(object):

    def transact2(self, __id, func, arg1, arg2):
        return getattr(scList[__id].functions, func)(arg1).transact(ast.literal_eval(arg2))

    def transact1(self, __id, func, arg1):
        return getattr(scList[__id].functions, func)().transact(ast.literal_eval(arg1))

    def transact(self, __id, func):
        return getattr(scList[__id].functions, func)().transact()

    def call(self, __id, func):
        return getattr(scList[__id].functions, func)().call()

class filterInterface(object):

    def blockFilter(self, __id): 
        return filterList[__id].get_new_entries()

# RPYC service definition

class W3_Wrapper_Service(rpyc.Service):

    # def on_connect(self):
    #     print(self._conn)

    def exposed_getKey(self, myID):
        return w3if.getKey(myID)

    def exposed_getBalance(self, myID):
        return w3if.getBalance(myID)

    def exposed_blockNumber(self, myID):
        return w3if.blockNumber(myID)

    def exposed_minerStart(self, myID):
        return w3if.minerStart(myID)

    def exposed_minerStop(self, myID):
        return w3if.minerStop(myID)

    def exposed_isMining(self, myID):
        return w3if.isMining(myID)

    def exposed_addPeer(self, myID, enode):
        return w3if.addPeer(myID, enode)

    def exposed_removePeer(self, myID, enode):
        return w3if.removePeer(myID, enode)

    def exposed_transact(self, myID, function):
        return scif.transact(myID, function)

    def exposed_transact1(self, myID, function, arg1):
        return scif.transact1(myID, function, str(arg1))

    def exposed_transact2(self, myID, function, arg1, arg2):
        return scif.transact2(myID, function, arg1, str(arg2))

    def exposed_call(self, myID, function):
        return scif.call(myID, function)

    def exposed_blockFilter(self, myID):
        return ftif.blockFilter(myID)

    def exposed_toWei(self, myID, value):
        return w3if.toWei(myID, value)

# Start the RPYC server
server = ThreadedServer(W3_Wrapper_Service, port = 4000)
t = Thread(target = server.start)
t.daemon = True
t.start()

w3if = web3Interface()
scif = scInterface()
ftif = filterInterface()

while True:
    time.sleep(1)


# # LOOK INTO THIS:
# def exposify(cls):
#     # cls.__dict__ does not include inherited members, so we can't use that.
#     for key in dir(cls):
#         val = getattr(cls, key)
#         if callable(val) and not key.startswith("_"):
#             setattr(cls, "exposed_%s" % (key,), val)

#     return cls


    # @server.decorators.exposify
    # class exposed_DbApi(dbApi.DbApi):
    #     pass

# alternatively

# rpyc.classic.upload_package