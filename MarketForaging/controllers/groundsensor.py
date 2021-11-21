#!/usr/bin/env python3
import time
import logging
import json
from types import SimpleNamespace

class GroundSensor(object):
    """ Set up a ground-sensor data acquisition loop on a background thread
    The __sensing() method will be started and it will run in the background
    until the application exits.
    """
    def __init__(self, robot, freq = 20):
        """ Constructor
        :type freq: str
        :param freq: frequency of measurements in Hz (tip: 20Hz)
        """
        self.freq = freq
        self.groundValues = [0 for x in range(3)]
        self.groundCumsum = [0 for x in range(3)]
        self.count = 0
        self.robot = robot

        logging.basicConfig(format='[%(levelname)s %(name)s %(relativeCreated)d] %(message)s')
        logger = logging.getLogger(__name__)

    def step(self):
        """ This method runs in the background until program is closed 
        """  

        # Initialize variables
        self.groundValues = self.robot.epuck_ground.get_readings()

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
        
    def start(self):
        pass

    def stop(self):
        pass

class ResourceVirtualSensor(object):
    """ Set up a ground-sensor data acquisition loop on a background thread
    The __sensing() method will be started and it will run in the background
    until the application exits.
    """
    def __init__(self, robot, freq = 1):
        """ Constructor
        :type freq: str
        :param freq: frequency of measurements in Hz (tip: 20Hz)
        """
        self.freq = freq
        self.rate = 1/freq
        self.robot = robot
        self.timer = time.time()
        self.resource = None

        logging.basicConfig(format='[%(levelname)s %(name)s %(relativeCreated)d] %(message)s')
        logger = logging.getLogger(__name__)

    def step(self):
        # Read frequency @ self.freq (Hz).
        if time.time() - self.timer > (self.rate):
            self.timer = time.time()
            resource = self.robot.variables.get_attribute("newResource")

            if resource:
                self.resource = resource
            else:
                self.resource = None

    def getNew(self):
        """ This method returns the instant ground value """
        temp = self.resource
        self.resource = None
        return temp
        
    def start(self):
        pass

    def stop(self):
        pass