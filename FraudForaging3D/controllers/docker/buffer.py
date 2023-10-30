#!/usr/bin/env python3
import time, sys, subprocess
from hexbytes import HexBytes

from console import init_web3, registerSC
from aux import TCP_mp, l2d, Logger, get_folder_size, get_process_stats


def getClusters():
    cluster_list = sc.functions.getClusters().call()
    cluster_dict = [l2d(c, cluster_keys) for c in cluster_list]
    return cluster_list, cluster_dict


def getPoints():
    point_list = sc.functions.getPoints().call()
    point_dict = [l2d(c, point_keys) for c in point_list]
    return point_list, point_dict


def getBalance(allpoints, allclusters):
    chain_balance  = float(w3.fromWei(w3.eth.getBalance(w3.eth.coinbase), "ether"))
    full_balance   = chain_balance

    cluster_buffer = [0] * len(allclusters)
    for point in allpoints:
        i = int(point['cluster'])

        try:
            allclusters[i]['verified'] == 0
        except:
            print(f'index error {i}')

        if point['sender'] == w3.eth.coinbase and allclusters[i]['verified'] == 0:
            if cluster_buffer[i] == 0:
                full_balance += float(point['credit']) / 1e18
                cluster_buffer[i] = 1
    return round(full_balance, 2), chain_balance

def blockHandle():
    """ Execute for each block when new blocks are synchronized """

    # Log relevant block details
    block = w3.eth.getBlock(blockHex)
    logs['block'].log([
        time.time()-block.timestamp,
        round(block.timestamp-logs['block'].tStart, 3),
        block.number,
        block.hash.hex(),
        block.parentHash.hex(),
        block.difficulty,
        block.totalDifficulty,
        block.size,
        len(block.transactions),
        len(block.uncles),
        str(eval(w3.geth.txpool.status()['pending'])),
        str(eval(w3.geth.txpool.status()['queued']))
    ])


def scHandle():
    """ Execute when new blocks are synchronized """

    lastBlock = w3.eth.getBlock('latest')

    _, allpoints = getPoints()
    _, allclusters = getClusters()
    balance, spendable_balance = getBalance(allpoints, allclusters)
    block = {key: value.hex() if isinstance(value, HexBytes) else value for key, value in dict(lastBlock).items()}

    balance_pending = 0
    # myPendingTxs =
    # for tx in myPendingTxs:
    # 	balance_pending += tx['value']

    # Log relevant smart contract details
    blockNumb = lastBlock['number']
    blockHash = lastBlock['hash'].hex()
    rep_stats  = sc.functions.getReportStatistics().call()
    n_clusters = len(allclusters)
    n_accepted = len([c for c in allclusters if c['verified']==1])
    n_rejected = len([c for c in allclusters if c['verified']==2])
    n_pending  = len([c for c in allclusters if c['verified']==0])

    logs['sc'].log([blockNumb, 
                    blockHash, 
                    balance, 
                    spendable_balance, 
                    balance_pending, 
                    n_clusters, 
                    n_accepted, 
                    n_rejected, 
                    n_pending, 
                    *rep_stats])
                    
    tcp_calls.setData({
        'balance': balance,
        'spendable_balance': spendable_balance,
        'block': block,
        'points': allpoints,
        'clusters': allclusters,
    })


if __name__ == '__main__':

    w3 = init_web3()
    sc = registerSC(w3)
    bf = w3.eth.filter('latest')

    robotID = sys.argv[1]
    logfolder = f'/root/logs/{robotID}'
    logs = dict()

    header = ['TELAPSED', 'TIMESTAMP', 'BLOCK', 'HASH', 'PHASH',
              'DIFF', 'TDIFF', 'SIZE', 'TXS', 'UNC', 'PENDING', 'QUEUED']
    logs['block'] = Logger(f'{logfolder}/block.csv', header, ID=robotID)

    header = ['BLOCK','HASH', 'BALANCE', 'SPENDABLE', 'PENDING', '#CLUSTERS', '#ACCEPT', '#REJECT', '#PENDING', 'RS1', 'RS2', 'RS3', 'RS4']
    logs['sc'] = Logger(f'{logfolder}/sc.csv', header, ID=robotID)
    # extrafields={'isbyz':isByz, 'isfau':isFau, 'iscol': isCol, 'type':behaviour})
    
    header = ['MEM', '%CPU', '%RAM']
    logs['extra'] = Logger(f'{logfolder}/extra.csv', header, 10, ID=robotID)

    for log in logs.values():
        log.start()

################################################################################################################
### TCP for calls ###
################################################################################################################

    host = subprocess.getoutput(
        "ip addr | grep 172.18.0. | tr -s ' ' | cut -d ' ' -f 3 | cut -d / -f 1")
    data = ""
    port = 9899

    tcp_calls = TCP_mp(data, host, port)
    tcp_calls.start()

    point_keys = sc.functions.getPointKeys().call()
    cluster_keys = sc.functions.getClusterKeys().call()
    scHandle()

################################################################################################################


    while True:

        newBlocks = bf.get_new_entries()

        if newBlocks:

            scHandle()

            for blockHex in newBlocks:
                blockHandle()

        if logs['extra'].query():
            mem = get_folder_size('/root/.ethereum/devchain/geth/chaindata')
            # cpu, ram = get_process_stats('geth ')
            logs['extra'].log([mem])

        time.sleep(0.25)