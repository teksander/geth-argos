import rpyc
import logging
import json
import os
import sys
from hexbytes import HexBytes
experimentFolder = os.environ["EXPERIMENTFOLDER"]
sys.path.insert(1, experimentFolder)

# logging.basicConfig(format='[%(levelname)s %(name)s] %(message)s')
# logger = logging.getLogger(__name__)


def init_web3(robotID):

    # Get ID from argos
    robotID = int(robotID)

    # Connect to the RPYC which hosts web3.py (port 4xxx where xxx is robot ID)
    dockerIP = identifersExtract(robotID, 'IP')
    
    conn = rpyc.connect(dockerIP, 4000, config = {"allow_all_attrs" : True})
    w3 = conn.root

    return w3


# def init_web3(robotID):

#     # Connect to the remove server which hosts the module web3.py
#     dockerIP = identifersExtract(robotID, 'IP')
#     conn = rpyc.classic.connect(dockerIP, 4000)
#     web3 = conn.modules.web3
#     Web3 = web3.Web3
#     IPCProvider = web3.IPCProvider
#     WebsocketProvider = web3.WebsocketProvider
#     geth_poa_middleware = web3.middleware.geth_poa_middleware

#     w3 = None
#     robotIP = identifersExtract(robotID)

#     if robotIP:
#         provider = WebsocketProvider('ws://'+robotIP+':8545')
#     else:
#         provider = IPCProvider('~/geth-pi-pucks/geth.ipc')

#     w3 = Web3(provider)
#     w3.provider = provider
#     w3.middleware_onion.inject(geth_poa_middleware, layer=0)
#     w3.geth.personal.unlockAccount(w3.eth.coinbase,"",0)
#     w3.eth.defaultAccount = w3.eth.coinbase


#     w3.key = w3.eth.coinbase
#     w3.enode = w3.geth.admin.nodeInfo().enode



#     def getBalance(address = w3.key):
#         return float(w3.fromWei(w3.eth.getBalance(address), 'ether'))

#     def removePeer(enode):
#         print(enode)
#         print(enode.__class__)
#         w3.provider.make_request("admin_removePeer", [HexBytes(enode)])

#     w3.geth.admin.removePeer = removePeer
#     w3.getBalance = getBalance

#     # provider.make_request("admin_removePeer", [w3.enode])

#     # logger.info('VERSION: %s', w3.clientVersion)
#     # logger.info('ADDRESS: %s', w3.key)
#     # logger.info('ENODE: %s', w3.enode)

#     return w3


def identifersExtract(robotID, query = 'IP'):
    namePrefix = 'ethereum_eth.' + str(robotID) + '.'
    containersFile = open(experimentFolder+'/identifiers.txt', 'r')
    for line in containersFile.readlines():
        if line.__contains__(namePrefix):
            if query == 'IP_DOCKER':
                return line.split()[-1]
            if query == 'IP':
                return line.split()[-2]
            if query == 'ENODE':
                return line.split()[1]

if __name__=='__main__':

    w3 = init_web3(robotID = 3)