#!/usr/bin/env python3
import rpyc
from rpyc.utils.server import ThreadedServer
from _thread import start_new_thread as thread

from console import *

wsAddr = 'localhost'
w3 = init_web3()
sc = registerSC(w3)
bf = w3.eth.filter('latest')

# Create an exposed wrapper for web3
class Web3_Wrapper_Service(rpyc.Service):

    @property
    def exposed_key(self):
        return w3.eth.coinbase
    @property
    def exposed_enode(self):
        return w3.geth.admin.nodeInfo().enode
    @property
    def exposed_balance(self):
        return w3.fromWei(w3.eth.getBalance(w3.eth.coinbase), 'ether')

    def exposed_toWei(self, value, currency):
        return w3.toWei(value, currency)

    class exposed_eth:
        def exposed_coinbase():
            return w3.eth.coinbase

        def exposed_getBalance(self):
            return w3.eth.getBalance(w3.eth.coinbase)

        def exposed_blockNumber():
            return w3.eth.blockNumber

        def exposed_mining():
            return w3.eth.mining

        def exposed_getBlock(blockHex):
            return w3.eth.getBlock('latest')

        def exposed_sendTransaction(tx):
            return w3.eth.sendTransaction(tx) 

        def exposed_getTransaction(txHash):
            return w3.eth.getTransaction(txHash)

        def exposed_getTransactionReceipt(txHash):
            return w3.eth.getTransactionReceipt(txHash)

    class exposed_geth:

        class exposed_miner:
            def exposed_start():
                w3.geth.miner.start()
            def exposed_stop():
                w3.geth.miner.stop()

        class exposed_admin:
            def exposed_addPeer(enode):
                w3.geth.admin.addPeer(enode)

            def exposed_removePeer(enode):
                w3.provider.make_request("admin_removePeer",[enode])

            def exposed_peers():
                return w3.geth.admin.peers()

        class exposed_txpool:
            def status():
                return w3.geth.txpool.status()

    class exposed_sc:

        class exposed_functions:

            funs = [x for x in dir(sc.functions) if not x.startswith('_')]

            # Expose .functions.<function>(*args).call() and .functions.<function>(*args).transact(*args)
            for fun in funs:
                exec('class exposed_%s:\
                    \n\tdef __init__(self,*args):\
                    \n\t\tself.args = args\
                    \n\tdef exposed_call(self):\
                    \n\t\treturn sc.functions.%s(*self.args).call()\
                    \n\tdef exposed_transact(self, *args):\
                    \n\t\treturn sc.functions.%s(*self.args).transact(*args)' % (fun,fun,fun))

    class exposed_bf:
        def exposed_get_new_entries():
            return bf.get_new_entries()


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


if __name__ == '__main__':

    # Start the RPYC server for this container
    server = ThreadedServer(Web3_Wrapper_Service(), port = 4000)
    server.start()

