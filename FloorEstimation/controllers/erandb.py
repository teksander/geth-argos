#!/usr/bin/env python3
import sys
import time
import logging

class ERANDB(object):
    """ Set up erandb transmitter on a background thread
    The __listen() method will be started and it will run in the background
    until the application exits.
    """
    def __init__(self, robot, dist = 200, tFreq = 0):
        """ Constructor
        :type dist: int
        :param dist: E-randb communication range (0=1meter; 255=0m)
        :type freq: int
        :param freq: E-randb transmit frequency (tip: 0 = no transmission; 4 = 4 per second)
        """

         # This robot ID
        self.robot = robot
        self.id = str(int(robot.variables.get_id()[2:])+1)
        self.newIds = set()
        self.setData(self.id)

    def step(self):
        """ This method runs in the background until program is closed """

        # /* Get a new peer ID */
        for reading in self.robot.epuck_range_and_bearing.get_readings():
            newId=reading[0]

            if newId != self.id: 
                self.newIds.add(newId)

    def setData(self, tData = None):
        if tData:
            self.tData = int(tData)
        self.robot.epuck_range_and_bearing.set_data([self.tData,0,0,0])

    def getNew(self):
        temp = self.newIds
        self.newIds = set()
        
        return temp

    def start(self):
        pass

    def stop(self):
        pass
