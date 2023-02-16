#!/usr/bin/env python3
import sys, time
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
        self.tData = [0,0,0,0]
        self.setData(self.id)

    def step(self):
        """ This method runs in the background until program is closed """

        # /* Get a new peer ID */
        for data in self.getData():
            newId=data[0]

            if newId != self.id: 
                self.newIds.add(newId)


    def getData(self):
        readings = self.robot.epuck_range_and_bearing.get_readings()
        return [reading[0] for reading in readings]

    def getRanges(self):
        readings = self.robot.epuck_range_and_bearing.get_readings()
        return [reading[1] for reading in readings]

    def getBearings(self):
        readings = self.robot.epuck_range_and_bearing.get_readings()
        return [reading[2] for reading in readings]

    def setData(self, data, index = 0):

        self.tData[index] = int(data)

        self.robot.epuck_range_and_bearing.set_data(self.tData)


    def getNew(self):
        temp = self.newIds
        self.newIds = set()
        return temp

    def start(self):
        pass

    def stop(self):
        pass
