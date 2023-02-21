#!/usr/bin/env python3
import sys, os
import rpyc
import logging

experimentFolder = os.environ["EXPERIMENTFOLDER"]
sys.path.insert(1, experimentFolder)
    
logger = logging.getLogger(__name__)

def init_web3(_ip):
    
    conn = rpyc.connect(_ip, 4000, config = {"allow_all_attrs" : True})
    w3 = conn.root
    
    logger.info('ADDRESS: %s', w3.key)
    logger.info('ENODE: %s', w3.enode)

    return w3



# if __name__=='__main__':

#     w3 = init_web3(robotID = 3)