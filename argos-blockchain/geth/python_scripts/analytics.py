#!/usr/bin/env python3
import time
import os
import sys
# import psutil
from console import *

class Logger(object):
    """ Logging Class to Record Data to a File
    """
    def __init__(self, logfile, header, rate = 0, buffering = 1, ID = None):

        os.makedirs(os.path.dirname(logfile), exist_ok=True)

        self.file = open(logfile, 'w+', buffering = buffering)
        self.rate = rate
        self.tStamp = 0
        self.tStart = 0
        self.latest = time.time()
        pHeader = ' '.join([str(x) for x in header])
        self.file.write('{} {} {}\n'.format('ID', 'TIME', pHeader))
        
        if ID:
            self.id = ID
        else:
            self.id = open("/boot/pi-puck_id", "r").read().strip()

    def log(self, data):
        """ Method to log row of data
        :param data: row of data to log
        :type data: list
        """ 
        
        if self.isReady():
            self.tStamp = time.time()
            try:
                tString = str(round(self.tStamp-self.tStart, 3))
                pData = ' '.join([str(x) for x in data])
                self.file.write('{} {} {}\n'.format(self.id, tString, pData))
                self.latest = self.tStamp
            except:
                pass
                logger.warning('Failed to log data to file')

    def isReady(self):
        return time.time()-self.tStamp > self.rate

    def start(self):
        self.tStart = time.time()

    def close(self):
        self.file.close()

def getFolderSize(folder):
    # Return the size of a folder
    total_size = os.path.getsize(folder)
    for item in os.listdir(folder):
        itempath = os.path.join(folder, item)
        if os.path.isfile(itempath):
            total_size += os.path.getsize(itempath)
        elif os.path.isdir(itempath):
            total_size += getFolderSize(itempath)
    return total_size

global clocks, counters, logs, txs
clocks, counters, logs, txs = dict(), dict(), dict(), dict()

def scHandle():
    """ Interact with SC when new blocks are synchronized """
    global ubi, payout, newRound, balance

    # 2) Log relevant smart contract details
    blockNr = w3.blockNumber()
    balance = w3.getBalance()
    ubi = w3.call('askForUBI')
    payout = w3.call('askForPayout')
    robotCount = w3.call('robotCount')
    mean = w3.call('getMean')
    voteCount = w3.call('getVoteCount') 
    voteOkCount = w3.call('getVoteOkCount') 
    myVoteCounter = None
    myVoteOkCounter = None
    newRound = w3.call('isNewRound')
    consensus = w3.call('isConverged')

    logs['sc'].log([blockNr, balance, ubi, payout, robotCount, mean, voteCount, voteOkCount, myVoteCounter,myVoteOkCounter, newRound, consensus])


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

    name        = 'sc.csv'  
    header      = ['BLOCK', 'BALANCE', '#RESOURCES']   
    logs['sc']  = Logger(logfolder+name, header, ID=robotID)

    name         = 'sync.csv' 
    header       = ['#BLOCKS']
    logs['sync'] = Logger(logfolder+name, header, ID=robotID)
    
    name          = 'extra.csv'
    header        = ['MB']
    logs['extra'] = Logger(logfolder+name, header, 10, ID=robotID)

    # header       = ['MINED?', 'BLOCK', 'NONCE', 'VALUE', 'STATUS', 'HASH']
    # log_filename = log_folder + 'tx.csv'     
    # logs['tx']   = Logger(log_filename, header)

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

                if logs['extra'].isReady():
                    logs['extra'].log([getFolderSize('/root/.ethereum/devchain/geth/chaindata')])

                newBlocks = bf.get_new_entries()
                if newBlocks:

                    resources = sc.functions.getResources().call()
                    json_list = [x[11] for x in resources]
                    recruits_list = [repr(x[1]) for x in resources]

                    with open(scresourcesfile, 'w+', buffering=1) as f:
                        for json in json_list:
                            f.write(json+'\n')

                    with open(screcruitsfile, 'w+', buffering=1) as f:
                        for recruits in recruits_list:
                            f.write(recruits+'\n')

                    logs['sync'].log([len(newBlocks)])

                    logs['sc'].log([w3.eth.blockNumber, 
                               sc.functions.balances(w3.key).call(),
                               len(resources) 
                               ])

                    # 1) Log relevant block details 
                    for blockHex in newBlocks:
                        
                        block = w3.eth.getBlock(blockHex)

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

        time.sleep(0.1)



