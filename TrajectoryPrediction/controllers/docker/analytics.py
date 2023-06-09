#!/usr/bin/env python3
import time, os, sys

from aux import Logger, getFolderSize
from console import *

global clocks, counters, logs, txs
clocks, counters, logs, txs = dict(), dict(), dict(), dict()

def scHandle():
    """ Interact with SC every time new blocks are synchronized """
    pass

def blockHandle():
    """ Every time new blocks are synchronized """

    logs['block'].log([time.time()-block['timestamp'], 
            block['timestamp'], 
            block['number'], 
            block['hash'].hex(), 
            block['parentHash'].hex(), 
            block['difficulty'],
            block['totalDifficulty'], 
            block['size'], 
            len(block['transactions']), 
            len(block['uncles'])
            ])

if __name__ == '__main__':

    w3 = init_web3()
    sc = registerSC(w3)
    bf = w3.eth.filter('latest')

    robotID = sys.argv[1]

    logfolder = '/root/logs/%s/' % robotID
    os.system("rm -rf " + logfolder)

    scresourcesfile = logfolder + 'scresources.txt'
    os.makedirs(os.path.dirname(scresourcesfile), exist_ok=True)
    os.system("touch " + scresourcesfile)

    screcruitsfile = logfolder + 'screcruits.txt'
    os.makedirs(os.path.dirname(screcruitsfile), exist_ok=True)
    os.system("touch " + screcruitsfile)


    # Experiment data logs (recorded to file)
    name          = 'block.csv'
    header        = ['TELAPSED','TIMESTAMP','BLOCK', 'HASH', 'PHASH', 'DIFF', 'TDIFF', 'SIZE','TXS', 'UNC', 'PENDING', 'QUEUED']
    logs['block'] = Logger(logfolder+name, header, ID=robotID)

    name          = 'extra.csv'
    header        = ['MB']
    logs['extra'] = Logger(logfolder+name, header, 10, ID=robotID)

    startFlag = False
    mining = False

    while True:

        if not startFlag:
            mining = w3.eth.mining

        if mining or startFlag:

            # Actions to perform on the first step
            if not startFlag:
                startFlag = True

                for log in logs.values():
                    log.start()

            # Actions to perform continuously
            else:

                if logs['extra'].query():
                    logs['extra'].log([getFolderSize('/root/.ethereum/devchain/geth/chaindata')])

                newBlocks = bf.get_new_entries()
                if newBlocks:

                    # 1) Log relevant block details 
                    for blockHex in newBlocks:

                        scHandle()

                        block = w3.eth.getBlock(blockHex)

                        blockHandle()

        time.sleep(0.1)



