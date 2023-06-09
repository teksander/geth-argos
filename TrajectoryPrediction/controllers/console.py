#!/usr/bin/env python3
import sys, os
import rpyc
import logging

experimentFolder = os.environ["EXPERIMENTFOLDER"]
sys.path.insert(1, experimentFolder)

from aux import Timer
    
logger = logging.getLogger(__name__)


def init_web3(_ip):
    
    conn = rpyc.connect(_ip, 4000, config = {"allow_all_attrs" : True})
    w3 = conn.root
    
    logger.info('ADDRESS: %s', w3.key)
    logger.info('ENODE: %s', w3.enode)

    return w3


class Transaction(object):

    def __init__(self, w3, txHash, name = "", query_latency = 2):
        self.name      = name
        self.w3        = w3
        self.timer     = Timer(query_latency)
        self.reset(txHash)
    
    def query(self, min_confirmations = 0):
        confirmations = 0

        if not self.hash:
            return False

        if self.timer.query():
            self.getTransaction()
            self.getTransactionReceipt()
            self.block = self.w3.eth.blockNumber()

        if not self.tx:
            robot.log.warning('Fail: Not found')
            self.fail = True
            return False

        elif not self.receipt:
            return False

        elif not self.receipt['status']:
            robot.log.warning('Fail: Status 0')
            self.fail = True
            return False

        else:
            confirmations = self.block - self.receipt['blockNumber']

            if self.last < confirmations:
                self.last = confirmations
                robot.log.info('Confirming: %s/%s', confirmations, min_confirmations)
                
            if confirmations >= min_confirmations:
                return True
            else:
                return False

    def failed(self, reset = True):

        if not self.fail:
            return False

        elif reset:
            self.reset(None)
            
        return True

    def getTransaction(self):
        try:
            self.tx = self.w3.eth.getTransaction(self.hash)
        except Exception as e:
            self.tx = None

    def getTransactionReceipt(self):
        try:
            self.receipt = self.w3.eth.getTransactionReceipt(self.hash)
        except Exception as e:
            self.receipt = None

    def reset(self, txHash):

        self.hash      = txHash
        self.tx        = None
        self.receipt   = None

        self.fail      = False
        self.block     = 0
        self.last      = 0

        if self.hash:
            self.getTransaction()


if __name__=='__main__':

    w3 = init_web3(robotID = 3)