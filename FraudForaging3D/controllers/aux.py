#!/usr/bin/env python3
import time
import sys
import threading
import socket
import subprocess
import os
import logging
import psutil
import math
import json
from types import SimpleNamespace
from multiprocessing.connection import Listener, Client
experimentFolder = os.environ["EXPERIMENTFOLDER"]
sys.path.insert(1, experimentFolder)



# The logs that go to console
# logging.basicConfig(format='[%(levelname)s %(name)s %(relativeCreated)d] %(message)s')

# # The logs that go to a file (include debugging logs)
# fh = logging.FileHandler('logs/main.log','w')
# fh.setFormatter(logging.Formatter(logsFormat))
# fh.setLevel(10)
# logging.getLogger('').addHandler(fh)

logger = logging.getLogger(__name__)

class Transaction(object):

    def __init__(self, w3, txHash, name="", query_latency=2, verified_idx=-1, myID=-1):
        self.name = name
        self.w3   = w3
        self.tx   = None
        self.hash = txHash
        self.receipt = None
        self.fail = False
        self.block = w3.eth.blockNumber()
        self.last = 0
        self.timer = Timer(query_latency)
        self.verify = verified_idx
        self.myID = myID
        if self.hash:
            self.getTransaction()

    def query(self, min_confirmations=0):
        confirmations = 0

        if not self.hash:
            return False

        if self.timer.query():
            self.getTransaction()
            self.getTransactionReceipt()
            self.block = self.w3.eth.blockNumber()

        if not self.tx:
            logger.warning('Failed: not found')
            self.fail = True
            return False

        elif not self.receipt:
            return False

        elif not self.receipt['status']:
            logger.warning('Failed: Status 0')
            self.fail = True
            return False

        else:
            confirmations = self.block - self.receipt['blockNumber']

            if self.last < confirmations:
                self.last = confirmations
                logger.info('Confirming: %s/%s', confirmations, min_confirmations)
                print(self.myID, ' Confirming: ', confirmations, min_confirmations)
            if confirmations >= min_confirmations:
                self.last = 0
                return True
            else:
                return False

    def getTransactionReceipt(self):
        try:
            self.receipt = self.w3.eth.getTransactionReceipt(self.hash)
        except Exception as e:
            self.receipt = None

    def getTransaction(self):
        try:
            self.tx = self.w3.eth.getTransaction(self.hash)
        except Exception as e:
            self.tx = None

class Counter:
    def __init__(self, rate = None, name = None):
        self.name  = name
        self.rate  = rate
        self.count = 0

    def query(self, step = True, reset = True):
        print(self.count)
        if self.remaining() <= 0:
            if reset: self.reset()
            return True
        else: 
            if step: self.step()
            return False

    def remaining(self):
        return self.rate - self.count

    def step(self):
        self.count += 1

    def dec(self):
        self.count -= 1

    def get(self):
        return self.count

    def set(self, rate):
        self.rate = rate
        self.count = 0

    def reset(self):
        self.count = 0

class Accumulator:
    def __init__(self, rate = 0, name = None):
        self.name = name
        self.rate = rate
        self.value = 0
        self.isLocked = False

    def query(self, reset = True):
        if self.remaining() < 0:
            if reset:
                self.reset()
            return True
        else:
            return False

    def remaining(self):
        return self.rate - self.value

    def set(self, rate):
        if not self.isLocked:
            self.rate = rate
            self.value = 0
        return self

    def get(self):
        return self.value
        
    def acc(self, quantity):
        self.value += quantity

    def reset(self):
        if not self.isLocked:
            self.value = 0
        return self

    def lock(self):
        self.isLocked = True
        return self

    def unlock(self):
        self.isLocked = False
        return self

class Timer:
    def __init__(self, rate = 0, name = None):
        self.name = name
        self.rate = rate
        self.time = time.time()
        self.isLocked = False

    def query(self, reset = True):
        if self.remaining() < 0:
            if reset:
                self.reset()
            return True
        else:
            return False

    def remaining(self):
        return self.rate - (time.time() - self.time)

    def set(self, rate):
        if not self.isLocked:
            self.rate = rate
            self.time = time.time()
        return self

    def reset(self):
        if not self.isLocked:
            self.time = time.time()
        return self

    def lock(self):
        self.isLocked = True
        return self

    def unlock(self):
        self.isLocked = False
        return self


class TicToc(object):
    """ Pendulum Class to Synchronize Output Times
    """
    def __init__(self, delay, name = None, sleep = True):
        """ Constructor
        :type delay: float
        :param delay: Time to wait
        """         
        self.delay = delay      
        self.stime = time.time()  
        self.name = name
        self.sleep = sleep

    def tic(self):
        self.stime = time.time()    

    def toc(self):
        dtime = time.time() - self.stime

        if not self.sleep:
            print(round(dtime,3)) 

        if self.sleep and dtime < self.delay:
            time.sleep(self.delay - dtime)
        else:
            # logger.warning('{} Pendulum too Slow. Elapsed: {}'.format(self.name,dtime))
            pass
            
class TCP_mp(object):
    """ Set up TCP_server on a background thread
    The __hosting() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self, data = None, host = None, port = None):
        """ Constructor
        :type data: any
        :param data: Data to be sent back upon request
        :type host: str
        :param host: IP address to host TCP server at
        :type port: int
        :param port: TCP listening port for enodes
        """
        
        self.data = data
        self.host = host
        self.port = port  

        self.running  = False
        self.received = []

    def __hosting(self):
        """ This method runs in the background until program is closed """ 
        logger.info('TCP server running')

        # Setup the listener
        listener = Listener((self.host, self.port))

        while True:
            try:
                __conn = listener.accept()
                __call = __conn.recv()
                __conn.send(self.data[__call])

            except Exception as e:
                print('TCP send failed')

            if not self.running:
                __conn.close()
                break 
                
    def request(self, data = None, host = None, port = None):
        """ This method is used to request data from a running TCP server """

        __msg = ""

        if not data:
            data = self.data
        if not host:
            host = self.host
        if not port:
            port = self.port
  
        try:
            __conn = Client((host, port))
            __conn.send(data)
            __msg  = __conn.recv()
            __conn.close()

            return __msg

        except Exception as e:
            logger.error(f'TCP request failed: {e}')

    def getNew(self):
        if self.running:
            temp = self.received
            self.received = []
            return temp
        else:
            print('TCP server is OFF')
            return []

    def setData(self, data):
        self.data = data   

    def start(self):
        """ This method is called to start __hosting a TCP server """

        if not self.running:
            # Initialize background daemon thread
            thread = threading.Thread(target=self.__hosting, args=())
            thread.daemon = True 

            # Start the execution                         
            thread.start()   
            self.running = True
        else:
            print('TCP server already ON')  

    def stop(self):
        """ This method is called before a clean exit """   
        self.running = False
        logger.info('TCP server is OFF') 
class TCP_server(object):
    """ Set up TCP_server on a background thread
    The __hosting() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self, data, ip, port, unlocked = False):
        """ Constructor
        :type data: str
        :param data: Data to be sent back upon request
        :type ip: str
        :param ip: IP address to host TCP server at
        :type port: int
        :param port: TCP listening port for enodes
        """
        self.__stop = 1
        
        self.data = data
        self.ip = ip
        self.port = port                              
        self.newIds = set()
        self.allowed = set()
        self.unlocked = unlocked
        self.count = 0 # For debugging
        self.allowedCount = 0 # For debugging

        logger.info('TCP-Server OK')

    def __hosting(self):
        """ This method runs in the background until program is closed """ 
         # create a socket object
        __socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        # set important options
        __socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # get local machine name
        __host = socket.gethostbyname(self.ip)
        # bind to the port
        __socket.bind((__host, self.port))  

        logger.info('TCP Server OK')  

        while True:
            try:
                # set the timeout
                __socket.settimeout(5)
                # queue one request
                __socket.listen(10)    
                # establish a connection
                __clientsocket,addr = __socket.accept()   
                logger.debug("TCP request from %s" % str(addr))
                self.count += 1

                if (addr[0][-3:] in self.allowed) or self.unlocked:
                    __clientsocket.send(self.data.encode('ascii'))
                    self.unallow(addr[0][-3:])
                    self.allowedCount += 1

                __clientsocket.close()

                # make of set of connection IDs
                newId = str(addr[0]).split('.')[-1]
                self.newIds.add(newId)

            except socket.timeout:
                pass

            time.sleep(0.01)

            if self.__stop:
                __socket.close()
                break 

    def request(self, server_ip, port):
        """ This method is used to request data from a running TCP server """
        # create the client socket
        __socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        # set the connection timeout
        __socket.settimeout(5)
        # connect to hostname on the port
        __socket.connect((server_ip, port))                               
        # Receive no more than 1024 bytes
        msg = __socket.recv(1024)  
        msg = msg.decode('ascii') 

        if msg == '':
            raise ValueError('Connection Refused')

        __socket.close()   
        return msg

        return 

    def lock(self):
        self.unlocked = False
    def unlock(self):
        self.unlocked = True

    def allow(self, client_ids):
        for client_id in client_ids:
            self.allowed.add(client_id)

    def unallow(self, client_ids):
        for client_id in client_ids:
            self.allowed.discard(client_id)

    def getNew(self):
        if self.__stop:
            return set()
            logger.warning('getNew: TCP is OFF')

        temp = self.newIds
        self.newIds = set()
        return temp

    def setData(self, data):
        self.data = data       

    def getData(self):
        return self.data

    def start(self):
        """ This method is called to start __hosting a TCP server """
        if self.__stop:
            self.__stop = 0
            # Initialize background daemon thread
            thread = threading.Thread(target=self.__hosting, args=())
            thread.daemon = True 

            # Start the execution                         
            thread.start()   
        else:
            logger.warning('TCP Server already ON')  

    def stop(self):
        """ This method is called before a clean exit """   
        self.__stop = 1
        logger.info('TCP Server OFF') 



class Peer(object):
    """ Establish the Peer class 
    """
    def __init__(self, _id, _ip = None, enode = None, key = None):
        """ Constructor
        :type _id: str
        :param _id: id of the peer
        """
        # Add the known peer details
        self.id = _id
        self.ip = _ip
        self.enode = enode
        self.key = key
        self.tStamp = time.time()

        # self.ageLimit = ageLimit
        self.isDead = False
        self.age = 0
        self.trials = 0
        self.timeout = 0
        self.timeoutStamp = 0

    def resetAge(self):
        """ This method resets the timestamp of the robot meeting """ 
        self.tStamp = time.time()

    def kill(self):
        """ This method sets a flag which identifies aged out peers """
        self.isDead = True

    def setTimeout(self, timeout = 10):
        """ This method resets the timestamp of the robot timing out """ 
        self.trials = 0
        self.timeout = timeout
        self.timeoutStamp = time.time()

class PeerBuffer(object):
    """ Establish the Peer class 
    """
    def __init__(self, ageLimit = 2):
        """ Constructor
        :type id__: str
        :param id__: id of the peer
        """
        # Add the known peer details
        self.buffer = []
        self.ageLimit = ageLimit
        self.__stop = True

    def start(self):
        """ This method is called to start calculating peer ages"""
        if self.__stop:  
            self.__stop = False

            # Initialize background daemon thread
            self.thread = threading.Thread(target=self.__aging, args=())
            self.thread.daemon = True   
            # Start the execution                         
            self.thread.start()   

    def stop(self):
        """ This method is called before a clean exit """   
        self.__stop = True
        self.thread.join()
        logger.info('Peer aging stopped') 

    def __aging(self):
        """ This method runs in the background until program is closed 
        self.age is the time elapsed since the robots meeting.
        """            
        while True:

            self.step()

            if self.__stop:
                break
            else:
                time.sleep(0.05);   

    def step(self):
        """ This method performs a single sequence of operations """          

        for peer in self.buffer:
            peer.age = time.time() - peer.tStamp

            if peer.age > self.ageLimit:
                peer.kill()

            if peer.timeout != 0:
                if (peer.timeout - (time.time() - peer.timeoutStamp)) <= 0:
                    peer.timeout = 0      


    def addPeer(self, newIds):
        """ This method is called to add a peer Id
            newPeer is the new peer object
        """   
        for newId in newIds:
            if newId not in self.getIds():
                newPeer = Peer(newId)  
                self.buffer.append(newPeer)
            else:
                self.getPeerById(newId).resetAge()

    def removePeer(self, oldId):
        """ This method is called to remove a peer Id
            newPeer is the new peer object
        """   
        self.buffer.pop(self.getIds().index(oldId))

    def getIds(self): 
        return [peer.id for peer in self.buffer]
    def getAges(self):
        return [peer.age for peer in self.buffer]
    def getEnodes(self):
        return [peer.enode for peer in self.buffer]
    def getIps(self):
        return [peer.ip for peer in self.buffer]       
    def getkeys(self):
        return [peer.key for peer in self.buffer]

    def getPeerById(self, id):
        return self.buffer[self.getIds().index(id)]

    def getPeerByEnode(self, enode):
        return self.buffer[self.getEnodes().index(enode)]

class Logger(object):
    """ Logging Class to Record Data to a File
    """
    def __init__(self, logfile, header, rate = 0, buffering = 1, ID = None):

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
        
        if self.query():
            self.tStamp = time.time()
            try:
                tString = str(round(self.tStamp-self.tStart, 3))
                pData = ' '.join([str(x) for x in data])
                self.file.write('{} {} {}\n'.format(self.id, tString, pData))
                self.latest = self.tStamp
            except:
                pass
                logger.warning('Failed to log data to file')

    def log_force(self, data):
        """ Method to log row of data
        :param data: row of data to log
        :type data: list
        """


        self.tStamp = time.time()
        try:
            tString = str(round(self.tStamp - self.tStart, 3))
            pData = ' '.join([str(x) for x in data])
            self.file.write('{} {} {}\n'.format(self.id, tString, pData))
            self.latest = self.tStamp
        except:
            pass
            logger.warning('Failed to log data to file')

    def query(self):
        return time.time()-self.tStamp > self.rate

    def start(self):
        self.tStart = time.time()

    def close(self):
        self.file.close()

def readEnode(enode, output = 'id'):
    # Read IP or ID from an enode
    ip_ = enode.split('@',2)[1].split(':',2)[0]

    if output == 'ip':
        return ip_
    elif output == 'id':
        return ip_.split('.')[-1] 

def getCPUPercent():
    return psutil.cpu_percent()

def getRAMPercent():
    return psutil.virtual_memory().percent

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

class Vector2D:
    """A two-dimensional vector with Cartesian coordinates."""

    def __init__(self, x = 0, y = 0, polar = False, degrees = False):

            self.x = x
            self.y = y

            if isinstance(x, (list, tuple)) and not y: 
                self.x = x[0]
                self.y = x[1]
            
            if degrees:
                y = math.radians(y)

            if polar:
                self.x = x * math.cos(y)
                self.y = x * math.sin(y)

            self.length = self.__abs__()
            self.angle = math.atan2(self.y, self.x)

    def __str__(self):
        """Human-readable string representation of the vector."""
        return '{:g}i + {:g}j'.format(self.x, self.y)

    def __repr__(self):
        """Unambiguous string representation of the vector."""
        return repr((self.x, self.y))

    def dot(self, other):
        """The scalar (dot) product of self and other. Both must be vectors."""

        if not isinstance(other, Vector2D):
            raise TypeError('Can only take dot product of two Vector2D objects')
        return self.x * other.x + self.y * other.y
    # Alias the __matmul__ method to dot so we can use a @ b as well as a.dot(b).
    __matmul__ = dot

    def cross(self, other):
        """The vector (cross) product of self and other. Both must be vectors."""

        if not isinstance(other, Vector2D):
            raise TypeError('Can only take cross product of two Vector2D objects')
        return abs(self) * abs(other) * math.sin(self-other)
    # Alias the __matmul__ method to dot so we can use a @ b as well as a.dot(b).
    __matmul__ = cross

    def __sub__(self, other):
        """Vector subtraction."""
        return Vector2D(self.x - other.x, self.y - other.y)

    def __add__(self, other):
        """Vector addition."""
        return Vector2D(self.x + other.x, self.y + other.y)

    def __radd__(self, other):
        """Recursive vector addition."""
        return Vector2D(self.x + other.x, self.y + other.y)

    def __mul__(self, scalar):
        """Multiplication of a vector by a scalar."""

        if isinstance(scalar, int) or isinstance(scalar, float):
            return Vector2D(self.x*scalar, self.y*scalar)
        raise NotImplementedError('Can only multiply Vector2D by a scalar')

    def __rmul__(self, scalar):
        """Reflected multiplication so vector * scalar also works."""
        return self.__mul__(scalar)

    def __neg__(self):
        """Negation of the vector (invert through origin.)"""
        return Vector2D(-self.x, -self.y)

    def __truediv__(self, scalar):
        """True division of the vector by a scalar."""
        return Vector2D(self.x / scalar, self.y / scalar)

    def __mod__(self, scalar):
        """One way to implement modulus operation: for each component."""
        return Vector2D(self.x % scalar, self.y % scalar)

    def __abs__(self):
        """Absolute value (magnitude) of the vector."""
        return math.sqrt(self.x**2 + self.y**2)

    def rotate(self, angle):
        return Vector2D(self.length, self.angle + angle, polar = True)

    def normalize(self):
        """Normalized vector"""
        if self.x == 0 and self.y == 0:
            return self
        else:
            return Vector2D(self.x/abs(self), self.y/abs(self))
            
            # self.x = normalized.x
            # self.y = normalized.y

    def distance_to(self, other):
        """The distance between vectors self and other."""
        return abs(self - other)

    def to_polar(self):
        """Return the vector's components in polar coordinates."""
        return self.length, self.angle

class Vector3D:
    """A three-dimensional vector with Cartesian coordinates."""

    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

        if isinstance(x, (list, tuple)) and not y and not z:
            self.x = x[0]
            self.y = x[1]
            self.z = x[2]
        
        self.length = self.__abs__()

    def __str__(self):
        """Human-readable string representation of the vector."""
        return '{:g}i + {:g}j + {:g}k'.format(self.x, self.y, self.z)

    def __repr__(self):
        """Unambiguous string representation of the vector."""
        return repr((self.x, self.y, self.z))

    def dot(self, other):
        """The scalar (dot) product of self and other. Both must be vectors."""
        if not isinstance(other, Vector3D):
            raise TypeError('Can only take dot product of two Vector3D objects')
        return self.x * other.x + self.y * other.y + self.z * other.z
    # Alias the __matmul__ method to dot so we can use a @ b as well as a.dot(b).
    __matmul__ = dot

    def cross(self, other):
        """The vector (cross) product of self and other. Both must be vectors."""
        if not isinstance(other, Vector3D):
            raise TypeError('Can only take cross product of two Vector3D objects')
        return Vector3D(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )
    def minimums(self, other):
        """Recursive vector minimums."""
        return Vector3D(min(self.x, other.x), min(self.y, other.y), min(self.z, other.z))
    
    def maximums(self, other):
        """Recursive vector maximums."""
        return Vector3D(max(self.x, other.x), max(self.y, other.y), max(self.z, other.z))

    def __sub__(self, other):
        """Vector subtraction."""
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)

    def __add__(self, other):
        """Vector addition."""
        return Vector3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __radd__(self, other):
        """Recursive vector addition."""
        return Vector3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __mul__(self, scalar):
        """Multiplication of a vector by a scalar."""
        if isinstance(scalar, int) or isinstance(scalar, float):
            return Vector3D(self.x * scalar, self.y * scalar, self.z * scalar)
        raise NotImplementedError('Can only multiply Vector3D by a scalar')

    def __rmul__(self, scalar):
        """Reflected multiplication so vector * scalar also works."""
        return self.__mul__(scalar)
    
    def __abs__(self):
        """Absolute value (magnitude) of the vector."""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def __eq__(self, other):
        """Element-wise comparison of vectors (==)."""
        if not isinstance(other, Vector3D):
            raise TypeError('Can only compare Vector3D objects with Vector3D objects')
        return (self.x == other.x) and (self.y == other.y) and (self.z == other.z)

    def __ne__(self, other):
        """Element-wise comparison of vectors (!=)."""
        return not self.__eq__(other)

    def __lt__(self, other):
        """Element-wise comparison of vectors (<)."""
        if not isinstance(other, Vector3D):
            raise TypeError('Can only compare Vector3D objects with Vector3D objects')
        return (self.x < other.x) and (self.y < other.y) and (self.z < other.z)

    def __le__(self, other):
        """Element-wise comparison of vectors (<=)."""
        if not isinstance(other, Vector3D):
            raise TypeError('Can only compare Vector3D objects with Vector3D objects')
        return (self.x <= other.x) and (self.y <= other.y) and (self.z <= other.z)

    def __gt__(self, other):
        """Element-wise comparison of vectors (>)."""
        if not isinstance(other, Vector3D):
            raise TypeError('Can only compare Vector3D objects with Vector3D objects')
        return (self.x > other.x) and (self.y > other.y) and (self.z > other.z)

    def __ge__(self, other):
        """Element-wise comparison of vectors (>=)."""
        if not isinstance(other, Vector3D):
            raise TypeError('Can only compare Vector3D objects with Vector3D objects')
        return (self.x >= other.x) and (self.y >= other.y) and (self.z >= other.z)
    
    
class mydict(dict):
    def __mul__(self, k):
        return mydict([[key, self[key] * k] for key in self])

    def __truediv__(self, k):
        return mydict([[key, self[key] / k] for key in self])

    def root(self, n):
        return mydict([[key, math.sqrt(self[key])] for key in self])

    def power(self, n):
        return mydict([[key, math.power(self[key])] for key in self])

    def round(self, n = 0):
        if n == 0:
            return mydict([[key, round(self[key])] for key in self])
        return mydict([[key, round(self[key], n)] for key in self])


def identifiersExtract(robotID, query = 'IP'):

    identifier = os.environ['CONTAINERBASE'] + '.' + str(robotID) + '.'

    with open(os.environ['EXPERIMENTFOLDER']+'/identifiers.txt', 'r') as identifiersFile:
        for line in identifiersFile.readlines():
            if line.__contains__(identifier):
                if query == 'IP':
                    return line.split()[-2]
                if query == 'IP_DOCKER':
                    return line.split()[-1]

def euclidean_distance(point1, point2):
    if len(point1) != len(point2):
        raise ValueError("Points must have the same dimensionality")
    
    squared_diff_sum = sum((x - y) ** 2 for x, y in zip(point1, point2))
    distance = math.sqrt(squared_diff_sum)
    
    return distance

def print_color(*variables, color_rgb = None, color_bgr = None):

    if color_bgr:
        color_rgb = color_bgr[::-1]

    # Convert variables to strings
    strings = [str(var) for var in variables]
    
    # Generate the ANSI escape sequence for the specified RGB color
    color_code = f"\033[38;2;{color_rgb[0]};{color_rgb[1]};{color_rgb[2]}m"
    
    # Concatenate the strings and print them with the specified color
    print(color_code + " ".join(strings) + "\033[0m")

class PID:
    def __init__(self, kp, ki, kd):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.previous_error = 0
        self.integral = 0

    def compute(self, error, dt):
        self.integral += error * dt
        derivative = (error - self.previous_error) / dt
        output = self.kp * error + self.ki * self.integral + self.kd * derivative
        self.previous_error = error
        return output
    
def update_formater(robotID, logger):
    # Create a formatter with your desired format
    formatter = logging.Formatter(f'[{robotID} %(levelname)s %(name)s] %(message)s')

    # Create a StreamHandler and set the formatter
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # Add the StreamHandler to the logger
    logger.handlers.clear()
    logger.addHandler(stream_handler)
    
def mapping_id_keys(directory_path, limit=None):
    id_to_key = {}
    key_to_id = {}
    count = 0

    for i in range(limit):
        folder_name = str(i)
        file_path = os.path.join(directory_path, folder_name, folder_name)

        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
                key = "0x"+data["address"]
                id_to_key[folder_name] = key
                key_to_id[key] = folder_name
                count += 1
                if count == limit:
                    break

    return id_to_key, key_to_id

def rgb_to_ansi(rgb):
    r, g, b = rgb
    return f"\033[38;2;{r};{g};{b}m"

def print_table(data, indent = 0, header = True):
    if not data:
        return

    # Get the field names from the first dictionary in the list
    field_names = list(data[0].keys())

    # Calculate the maximum width of each column
    column_widths = {}
    for name in field_names:
        column_widths[name] = max(len(str(row.get(name, ""))) for row in data) + 2

    # Print the table header
    if header:
        for name, width in column_widths.items():
            print(indent*"  " + name + '  ', end="")
        print()

    # Print the table rows
    for row in data:
        ansi_code = rgb_to_ansi(row['position'])
        print("\n" + indent*"  " + bool(indent)*"*", end="")
        for name, width in column_widths.items():
            if isinstance(row.get(name, ""), list) and all(isinstance(item, dict) for item in row.get(name, "")):
                print_table(row.get(name, ""), indent=1, header=False)
            else:
                value = str(row.get(name, ""))
                print(ansi_code + value.ljust(width) + "\033[0m", end="")
