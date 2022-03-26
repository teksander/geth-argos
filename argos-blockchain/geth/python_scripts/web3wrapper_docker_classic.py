import web3
import rpyc
from rpyc.utils.server import ThreadedServer

# Start the RPYC server
# Host the web3 module remotely 

if __name__ == '__main__':
    
    server = ThreadedServer(rpyc.classic.ClassicService, port = 4000, protocol_config={ 'allow_all_attrs': True })
    server.start()
