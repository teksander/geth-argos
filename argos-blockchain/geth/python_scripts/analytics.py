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

    sclog.log([blockNr, balance, ubi, payout, robotCount, mean, voteCount, voteOkCount, myVoteCounter,myVoteOkCounter, newRound, consensus])


if __name__ == '__main__':

    wsAddr = 'localhost'
    w3 = init_web3()
    sc = registerSC(w3)
    bf = w3.eth.filter('latest')

    robotID = sys.argv[1]
    logfolder = '/root/logs/%s/' % robotID

    scresourcesfile = logfolder + 'scresources.txt'
    os.system("rm -rf " + logfolder)
    os.makedirs(os.path.dirname(scresourcesfile), exist_ok=True)
    os.system("touch " + scresourcesfile)

    screcruitsfile = logfolder + 'screcruits.txt'
    os.makedirs(os.path.dirname(screcruitsfile), exist_ok=True)
    os.system("touch " + screcruitsfile)

    header = ['TELAPSED','TIMESTAMP','BLOCK', 'HASH', 'PHASH', 'DIFF', 'TDIFF', 'SIZE','TXS', 'UNC', 'PENDING', 'QUEUED']
    logfile = logfolder + 'block.csv'
    blocklog = Logger(logfile, header, ID=robotID)

    header = ['BLOCK', 'BALANCE', '#RESOURCES']
    logfile = logfolder + 'sc.csv'     
    sclog = Logger(logfile, header, ID=robotID)

    header = ['#BLOCKS']
    logfile = logfolder + 'sync.csv' 
    synclog = Logger(logfile, header, ID=robotID)

    header = ['MB']
    logfile = logfolder + 'extra.csv'
    extralog = Logger(logfile, header, 10, ID=robotID)

    logs = [blocklog, sclog, synclog, extralog]

    # header = ['MINED?', 'BLOCK', 'NONCE', 'VALUE', 'STATUS', 'HASH']
    # log_filename = log_folder + 'tx.csv'     
    # txlog = Logger(log_filename, header)

    startFlag = False
    mining = False

    while True:

        if not startFlag:
            mining = w3.eth.mining

        if mining or startFlag:
            # Actions to perform on the first step
            if not startFlag:
                
                for log in logs:
                    log.start()
                startFlag = True

            else:
                newBlocks = bf.get_new_entries()
                if newBlocks:

                    resources = sc.functions.getResources().call()
                    json_list = [x[3] for x in resources]
                    recruits_list = [repr(x[1]) for x in resources]

                    with open(scresourcesfile, 'w+', buffering=1) as f:
                        for json in json_list:
                            f.write(json+'\n')

                    with open(screcruitsfile, 'w+', buffering=1) as f:
                        for recruits in recruits_list:
                            f.write(recruits+'\n')

                    synclog.log([len(newBlocks)])

                    sclog.log([w3.eth.blockNumber, 
                               round(w3.fromWei(w3.eth.getBalance(w3.key), 'ether'), 2),
                               len(resources) 
                               ])

                    # 1) Log relevant block details 
                    for blockHex in newBlocks:
                        
                        block = w3.eth.getBlock(blockHex)

                        blocklog.log([time.time()-block['timestamp'], 
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


                if extralog.isReady():
                    extralog.log([getFolderSize('/root/.ethereum/devchain/geth/chaindata')])
        else:
            time.sleep(0.5)

        time.sleep(0.5)



