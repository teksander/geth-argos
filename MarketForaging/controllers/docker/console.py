#!/usr/bin/env python
from web3 import Web3, IPCProvider, WebsocketProvider
from web3.middleware import geth_poa_middleware

import json
import logging

logging.basicConfig(format='[%(levelname)s %(name)s] %(message)s')
logger = logging.getLogger(__name__)


def init_web3(__ip=None):

    w3 = None

    if __ip:
        provider = WebsocketProvider('ws://'+__ip+':8545')
    else:
        provider = IPCProvider('/root/.ethereum/devchain/geth.ipc')

    w3 = Web3(provider)
    w3.provider = provider
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    w3.geth.personal.unlockAccount(w3.eth.coinbase, "", 0)
    w3.eth.defaultAccount = w3.eth.coinbase
    w3.key = w3.eth.coinbase
    w3.enode = w3.geth.admin.nodeInfo().enode

    logger.info('VERSION: %s', w3.clientVersion)
    logger.info('ADDRESS: %s', w3.key)
    logger.info('ENODE: %s', w3.enode)

    return w3


def registerSC(w3):
    sc = None

    abiPath = '/root/contracts/deploy.abi'
    abi = json.loads(open(abiPath).read())
    addressPath = '/root/contracts/contractAddress.txt'
    address = '0x' + open(addressPath).read().rstrip()

    sc = w3.eth.contract(abi=abi, address=address)
    return sc

if __name__ == '__main__':

    w3 = init_web3()
    sc = registerSC(w3)
