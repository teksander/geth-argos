#!/usr/bin/env python3
import time, os, sys, psutil

from aux import Logger, getFolderSize
from console import *

global clocks, counters, logs, txs
clocks, counters, logs, txs = dict(), dict(), dict(), dict()

def scHandle(block):
    """ Interact with SC every time new blocks are synchronized """

    robot = sc.functions.robot(w3.key).call()

    mean = sc.functions.mean().call()
    voteCount = sc.functions.getVoteCount().call()
    voteOkCount = sc.functions.getVoteOkCount().call()    
    
    # Write to the log file used data analysis
    logs['sc'].log([
        block['number'], 
        block['hash'].hex(), 
        block['parentHash'].hex(),
        mean,
        voteCount,
        voteOkCount
        ])

def blockHandle(block):
    """ Every time new blocks are synchronized """

    logs['block'].log([time.time()-block['timestamp'], 
            block['timestamp'], 
            block['number'], 
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

    # Experiment data logs (recorded to file)
    name          = 'block.csv'
    header        = ['TELAPSED','TIMESTAMP','BLOCK', 'SIZE','TXS', 'UNC']
    logs['block'] = Logger(logfolder+name, header, ID=robotID)

    name        = 'sc.csv'  
    header      = ['BLOCK', 'MEAN', 'VOTECOUNT', 'VOTEOKCOUNT']   
    logs['sc']  = Logger(logfolder+name, header, ID=robotID)

    name          = 'extra.csv'
    header        = ['CPU', 'RAM', 'KB']
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
                # Log CPU, RAM, and MB of blockchain

                    cpu = psutil.cpu_percent()
                    ram = psutil.virtual_memory().percent
                    chainSize_raw = subprocess.run(["du", "-cs", "/root/.ethereum/devchain/geth/chaindata/"], stdout=subprocess.PIPE)
                    chainSize = chainSize_raw.stdout.decode('utf-8').split('\t')[0]

                    logs['extra'].log([
                        cpu,
                        ram,
                        chainSize
                        ])

                newBlocks = bf.get_new_entries()
                if newBlocks:

                    # 1) Log relevant block details 
                    for blockHex in newBlocks:

                        block = w3.eth.getBlock(blockHex)
                        scHandle(block)
                        blockHandle(block)


        time.sleep(1)



