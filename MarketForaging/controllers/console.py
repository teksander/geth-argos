import rpyc
import logging
import json
from hexbytes import HexBytes
from aux import identifersExtract
import sys, os

sys.path += [os.environ['EXPERIMENTFOLDER']+'/controllers', \
             os.environ['EXPERIMENTFOLDER']+'/loop_functions', \
             os.environ['EXPERIMENTFOLDER']]

# logging.basicConfig(format='[%(levelname)s %(name)s] %(message)s')
# logger = logging.getLogger(__name__)

def init_web3(robotID):

    # Get ID from argos
    robotID = int(robotID)

    # Connect to the RPYC which hosts web3.py (port 4xxx where xxx is robot ID)
    dockerIP = identifersExtract(robotID, 'DOCKER_IP')

    conn = rpyc.connect(dockerIP, 4000, config = {"allow_all_attrs" : True})
    w3 = conn.root

    return w3

def init_peer_buffer(robotID):

    # Get ID from argos
    robotID = int(robotID)

    # Connect to the RPYC which hosts web3.py (port 4xxx where xxx is robot ID)
    dockerIP = identifersExtract(robotID, 'IP')
    
    conn = rpyc.connect(dockerIP, 4001, config = {"allow_all_attrs" : True})
    pb = conn.root
    sendPeers = rpyc.async_(pb.sendPeers)
    getCount  = rpyc.async_(pb.getCount)

    return pb, sendPeers, getCount



# def identifersExtract(robotID, query = 'IP'):
#     namePrefix = '_eth.' + str(robotID) + '.'
#     with open(experimentFolder+'/identifiers.txt', 'r') as identifiersFile:
#         for line in identifiersFile.readlines():
#             if line.__contains__(namePrefix):
#                 if query == 'IP':
#                     return line.split()[-1]
#                 if query == 'ENODE':
#                     return line.split()[1]

if __name__=='__main__':

    w3 = init_web3(robotID = 3)




















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