#!/usr/bin/env python3
import math, random, time
import logging
import json
from types import SimpleNamespace


class IMUSensor(object):
    """ Set up a ground-sensor data acquisition loop on a background thread
    The __sensing() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self, robot, freq=20):
        """ Constructor
        :type freq: str
        :param freq: frequency of measurements in Hz (tip: 20Hz)
        """
        self.freq = freq
        self.imuValues = [0 for x in range(3)]
        self.imuCumsum = [0 for x in range(3)]
        self.count = 0
        self.robot = robot

        logging.basicConfig(format='[%(levelname)s %(name)s %(relativeCreated)d] %(message)s')
        logger = logging.getLogger(__name__)

    def step(self):
        """ This method runs in the background until program is closed
        """

        # Initialize variables
        self.imuValues = self.robot.epuck_imu.get_readings()

        # Compute cumulative sum
        self.imuCumsum[0] += self.imuValues[0]
        self.imuCumsum[1] += self.imuValues[1]
        self.imuCumsum[2] += self.imuValues[2]
        self.count += 1

    def getAvg(self):
        """ This method returns the average ground value since last call """

        # Compute average
        try:
            imuAverage = [round(x / self.count) for x in self.imuCumsum]
        except:
            imuAverage = None

        self.count = 0
        self.imuCumsum = [0 for x in range(3)]
        return imuAverage

    def getNew(self):
        """ This method returns the instant ground value """

        return self.imuValues

    def start(self):
        pass

    def stop(self):
        pass