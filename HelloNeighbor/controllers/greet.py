
# /* Logging Levels for Console and File */
#######################################################################
loglevel = 10

tcpPort = 5000 

# /* Import Packages */
#######################################################################
import random, math
import sys
import os
experimentFolder = os.environ["EXPERIMENTFOLDER"]
sys.path.insert(1, experimentFolder+'/controllers')
sys.path.insert(1, experimentFolder)
import json
import time
import rpyc
import copy
import logging
from aux import *

# #####################################################
# ## ERROR METHOD: import w3 multiple times; 
# from console import init_web3, registerSC
# w3 = init_web3(ip)

#####################################################

#### #### #### #### #### #### #### #### #### #### #### #### #### 
#### ALL CHEAP CHEAPSI SOLUTIONS; USE TCP VIA LOCALHOST?
def identifersExtract(robotID, query = 'IP'):
    namePrefix = 'ethereum_eth.'+str(robotID)
    containersFile = open('identifiers.txt', 'r')
    for line in containersFile.readlines():
        if line.__contains__(namePrefix):
            if query == 'IP':
                return line.split()[-1]
            if query == 'ENODE':
                return line.split()[1]

def enodesExtract(robotID, query = 'IP'):
    namePrefix = str(robotID)
    enodesFile = open('enodes.txt', 'r')
    for line in enodesFile.readlines():
        if line.__contains__(namePrefix):
                temp = line.split()[-1]
                return temp[1:-1]
#### #### #### #### #### #### #### #### #### #### #### #### #### 

# Some parameters
isbyz = False
robot_speed = 15


# Some estimation variables
global estimate, totalWhite, totalBlack
estimate = 0
totalWhite = 0
totalBlack = 0

global peered
peered = set()

global greeted, actual_greets
greeted = set()
actual_greets = 0


def init_w3():

    # Connect to the RPYC which hosts web3.py (port 400xx where xx is robot ID)
    conn = rpyc.connect("localhost", 4000+int(robotID), config = {"allow_all_attrs" : True})
    w3 = conn.root

    # Do stuff over RPYC
    print(w3.getBalance())
    print(w3.getKey())
    print(w3.isMining())
    
    return w3

def init():
    global w3, rw, gs, rb, tcp, tcp, mainlogger, robotID

    # Get ID from argos
    robotID = int(robot.variables.get_id()[2:])+1    

    w3 = init_w3()
    rw = RandomWalk(robot_speed)
    gs = GroundSensor()
    rb = ERANDB()

    # /* Init an instance of peer for this Pi-Puck */
    me = Peer(str(robotID), w3.getEnode(), w3.getKey())

    #mainlogger.info('Initialising TCP server...')
    tcp = TCP_server(me.enode, 'localhost', tcpPort+int(me.id), unlocked = True)    

    tcp.start()

    w3.start()
    w3.transact('setGreeting')
    w3.call('greetingCount')

    logFile = experimentFolder+'/logs/robot'+str(robotID)+'.log'
    logging.basicConfig(filename=logFile, filemode='w+', format='[%(levelname)s %(name)s %(relativeCreated)d] %(message)s')
    mainlogger = logging.getLogger('main')
    logging.getLogger('main').setLevel(loglevel)

def controlstep():
    global greeted, actual_greets

    rw.walking()
    gs.sensing()
    rb.listening()

    peers = Buffer()

    for peer in peers:
        if peer not in greeted:
            Greet(peer)  
            greeted.add(peer)

    temp = copy.copy(greeted)
    for peer in temp:
        if peer not in peers:
            greeted.remove(peer)

    newBlocks = w3.blockFilter()
    if newBlocks:
        bn = w3.blockNumber()
        bal = w3.getBalance()
        greets = w3.call('greetingCount')

        if robotID == 1:
            print('ID; #Block; Balance; #Greets; #MyGreets')
            print(robotID, bn, bal, greets, actual_greets)

def Greet(neighbor):
    global actual_greets
    try:
        w3.transact('greet')
        robot.epuck_leds.set_all_colors("red")
        actual_greets += 1
        print("Hello Neighbor", neighbor)
    except ValueError:
        print("Greet Failed. No Balance: ", getBalance())
    except:
        print("Greet Failed. Unknown") 

def Buffer():

    peers = rb.getNew()

    if peers: 
        robot.epuck_leds.set_all_colors("red")
    else:
        robot.epuck_leds.set_all_colors("black")

    for peer in peers:
        if peer not in peered:
            enode = tcp.request('localhost', tcpPort+int(peer))                 
            #enode = enodesExtract(peer, query = 'ENODE')
            w3.addPeer(enode)
            peered.add(peer)
            mainlogger.info('Added peer: %s', peer)

    temp = copy.copy(peered)
    for peer in temp:
        if peer not in peers:
            enode = tcp.request('localhost', tcpPort+int(peer)) 
            #enode = enodesExtract(peer, query = 'ENODE')
            w3.removePeer(enode)
            peered.remove(peer)
            mainlogger.info('Removed peer: %s', peer)

    return peers

def Estimate():
    """ Control routine to update the local estimate of the robot """
    global estimate, totalWhite, totalBlack
    # Set counters for grid colors
    newValues = gs.getNew()
    # print([newValue for newValue in newValues])

    for value in newValues:
        if value != 0:
            totalWhite += 1
        else:
            totalBlack += 1
    if isbyz:
        estimate = 0
    else:
        estimate = (0.5+totalWhite)/(totalWhite+totalBlack+1)

class ERANDB(object):
    """ Set up erandb transmitter on a background thread
    The __listen() method will be started and it will run in the background
    until the application exits.
    """
    def __init__(self, dist = 200, tFreq = 0):
        """ Constructor
        :type dist: int
        :param dist: E-randb communication range (0=1meter; 255=0m)
        :type freq: int
        :param freq: E-randb transmit frequency (tip: 0 = no transmission; 4 = 4 per second)
        """

         # This robot ID
        self.id = robotID
        self.newIds = set()
        self.tData = self.id
        self.setData()

    def listening(self):
        """ This method runs in the background until program is closed """

        # /* Get a new peer ID */
        for reading in robot.epuck_range_and_bearing.get_readings():
            newId=reading[0]

            if newId != self.id: 
                self.newIds.add(newId)

    def setData(self, tData = None):

        if tData:
            self.tData = int(tData)

        robot.epuck_range_and_bearing.set_data([self.tData,0,0,0])

    def getNew(self):

        temp = self.newIds
        self.newIds = set()
        return temp

class GroundSensor(object):
    """ Set up a ground-sensor data acquisition loop on a background thread
    The __sensing() method will be started and it will run in the background
    until the application exits.
    """
    def __init__(self, freq = 20):
        """ Constructor
        :type freq: str
        :param freq: frequency of measurements in Hz (tip: 20Hz)
        """
        self.freq = freq
        self.groundValues = [0 for x in range(3)]
        self.groundCumsum = [0 for x in range(3)]
        self.count = 0


    def sensing(self):
        """ This method runs in the background until program is closed 
        """  

        # Initialize variables
        self.groundValues = robot.epuck_ground.get_readings()

        # Compute cumulative sum
        self.groundCumsum[0] += self.groundValues[0] 
        self.groundCumsum[1] += self.groundValues[1]
        self.groundCumsum[2] += self.groundValues[2]
        self.count += 1


    def getAvg(self):
        """ This method returns the average ground value since last call """

        # Compute average
        try:
            groundAverage =  [round(x/self.count) for x in self.groundCumsum]
        except:
            groundAverage = None

        self.count = 0
        self.groundCumsum = [0 for x in range(3)]
        return groundAverage

    def getNew(self):
        """ This method returns the instant ground value """

        return self.groundValues;



class RandomWalk(object):
    """ Set up a Random-Walk loop on a background thread
    The __walking() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self, MAX_SPEED):
        """ Constructor
        :type range: int
        :param enode: Random-Walk speed (tip: 500)
        """
        self.MAX_SPEED = MAX_SPEED                          
        self.__stop = 1
        self.__walk = True
     
        # Random walk parameters
        self.remaining_walk_time = 3
        self.my_lambda = 10 # Parameter for straight movement
        self.turn = 4
        self.possible_directions = ["straight", "cw", "ccw"]
        self.actual_direction = "straight"

        # Obstacle Avoidance parameters
        self.weights_left  = 50*[-10, -10, -5, 0, 0, 5, 10, 10]
        self.weights_right = 50*[-1 * x for x in self.weights_left]

    def walking(self):
        """ This method runs in the background until program is closed """
        # robot.epuck_leds.set_all_colors("black")
        
        # Random Walk
        if (self.remaining_walk_time == 0):
            if self.actual_direction == "straight":
                self.actual_direction = random.choice(self.possible_directions)
                self.remaining_walk_time = math.floor(random.uniform(0, 1) * self.turn)
            else:
                self.remaining_walk_time = math.ceil(random.expovariate(1/(self.my_lambda * 4)))
                self.actual_direction = "straight"
        else:
            self.remaining_walk_time -= 1

        # Find Wheel Speed for Random-Walk
        if (self.actual_direction == "straight"):
            left = right = self.MAX_SPEED/2
        elif (self.actual_direction == "cw"):
            left  = self.MAX_SPEED/2
            right = -self.MAX_SPEED/2
        elif (self.actual_direction == "ccw"):
            left  = -self.MAX_SPEED/2
            right = self.MAX_SPEED/2

        # Obstacle avoidance
        readings = robot.epuck_proximity.get_readings()
        self.ir = [reading.value for reading in readings]
                
        # Find Wheel Speed for Obstacle Avoidance
        for i, reading in enumerate(self.ir):
            if(reading != 0 ):
                left  = self.MAX_SPEED/2 + self.weights_left[i] * reading
                right = self.MAX_SPEED/2 + self.weights_right[i] * reading
                # robot.epuck_leds.set_all_colors("red")                

        # Saturate Speeds greater than MAX_SPEED
        if left > self.MAX_SPEED:
            left = self.MAX_SPEED
        elif left < -self.MAX_SPEED:
            left = -self.MAX_SPEED

        if right > self.MAX_SPEED:
            right = self.MAX_SPEED
        elif right < -self.MAX_SPEED:
            right = -self.MAX_SPEED

        if self.__walk:
            # Set wheel speeds
            robot.epuck_wheels.set_speed(right, left)
        else:
            # Set wheel speeds
            robot.epuck_wheels.set_speed(0, 0)
        

    def setWalk(self, state):
        """ This method is called set the random-walk to on without disabling I2C"""
        self.__walk = state

    def setLEDs(self, state):
        """ This method is called set the outer LEDs to an 8-bit state """
        if self.__LEDState != state:
            self.__isLEDset = False
            self.__LEDState = state
        
    def getIr(self):
        """ This method returns the IR readings """
        return self.ir



def reset():
    robot.logprint("reset")

def destroy():
    robot.logprint("destroy")

