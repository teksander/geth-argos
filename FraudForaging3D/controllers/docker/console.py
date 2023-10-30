#!/usr/bin/env python
from web3 import Web3, IPCProvider, WebsocketProvider
from web3.middleware import geth_poa_middleware

import json
import logging
from aux import print_table, mapping_id_keys, l2d

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


def call(show_points=True, raw=False):
    block = w3.eth.getBlock('latest')
    _, points = getPoints()
    _, clusters = getClusters()
    balance, usable = getBalance(points, clusters)
    unclustered_points = []

    if not raw:
        for point in points:
            if point['cluster'] >= 0:
                p1 = point['position']
                p2 = clusters[point['cluster']]['position']
            # point['RME'] = round(colourBGRDistance(p1,p2)/1e5, 2)
            # point['MAN'] = round(manhattan_distance(p1,p2)/1e5, 2)
            # point['CHS'] = round(chebyshev_distance(p1,p2)/1e5, 2)
            point['position'] = [round(i/1e5) for i in point['position']]
            point['credit'] //= 1e16
            point['sender'] = point['sender'][0:5]
            # point['sender'] = key_to_id[point['sender'].lower()]

        for idx, cluster in enumerate(clusters):
            del cluster['life']
            cluster['outlier_senders'] = len(cluster['outlier_senders'])
            cluster['position'] = [round(i/1e5) for i in cluster['position']]
            cluster['sup_position'] = [round(i/1e5)
                                       for i in cluster['sup_position']]
            cluster['total_credit'] //= 1e16
            cluster['total_credit_food'] //= 1e16
            cluster['total_credit_outlier'] //= 1e16
            cluster['init_reporter'] = cluster['init_reporter'][0:5]
            # cluster['init_reporter'] = key_to_id[cluster['init_reporter'].lower()]

            if show_points:
                cluster['points'] = [
                    point for point in points if point['cluster'] == idx]
                unclustered_points = [
                    point for point in points if point['cluster'] == -1]
    print_table(clusters)
    print()
    print(
        f"LAST BLOCK: block# (hash) {block['number']} ({block['hash'][0:8]})")
    print(f"MY BALANCE: usable (balance) {usable:.2f} ({balance:.2f})")
    if show_points:
        print_table(unclustered_points, indent=2)

def getClusters():
    cluster_list = sc.functions.getClusters().call()
    cluster_dict = [l2d(c, cluster_keys) for c in cluster_list]
    return cluster_list, cluster_dict


def getPoints():
    point_list = sc.functions.getPoints().call()
    point_dict = [l2d(c, point_keys) for c in point_list]
    return point_list, point_dict


def getBalance(allpoints, allclusters):
    # check all my balance, including those frozen in unverified clusters.
    myUsableBalance = float(w3.fromWei(
        w3.eth.getBalance(w3.eth.coinbase), "ether")) - 1
    myBalance = myUsableBalance
    # _, allpoints = getPoints()
    # _, allclusters = getClusters()
    for idx, cluster in enumerate(allclusters):
        if cluster['verified'] == 0:
            for point in allpoints:
                if point['sender'] == w3.key and int(point['cluster']) == idx:
                    myBalance += float(point['credit']) / 1e18
    return round(myBalance, 2), myUsableBalance


if __name__ == '__main__':

    w3 = init_web3()
    sc = registerSC(w3)

    _, key_to_id = mapping_id_keys("/home/eksander/geth-argos/argos-blockchain-sm/geth/files/keystores/", limit=200)
    point_keys = sc.functions.getPointKeys().call()
    cluster_keys = sc.functions.getClusterKeys().call()