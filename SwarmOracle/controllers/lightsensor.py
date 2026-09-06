#!/usr/bin/env python3
import math, random, time
import logging

class omnicam_reading(object):
    def __init__(self, color, angle, distance):
        self.color    = color
        self.distance = distance
        self.angle    = angle
        self.angle_d  = math.degrees(angle)

    def __repr__(self):
        return repr(self.__dict__)

class OmniCam(object):
    """ Set up ARGoS3 colored_blob_omnidirectional_camera

    """
    def __init__(self, robot, freq = 10, fov = 360):
        """ Constructor
        :type freq: str
        :param freq: frequency of measurements in Hz (tip: 10Hz)
        """
        self.freq      = freq
        self.fov       = fov
        self.readings  = []
        self.robot = robot

        logging.basicConfig(format='[%(levelname)s %(name)s %(relativeCreated)d] %(message)s')
        logger = logging.getLogger(__name__)

    def step(self):
        """ Execute at every timestep
        """  
        # Read data from the colored_blob_omnidirectional_camera
        readings = self.robot.colored_blob_omnidirectional_camera.get_readings()
        self.readings  = [omnicam_reading(*r) for r in readings]

        # Filter angle according to FOV limit
        if self.fov != 360:
            temp = [r for r in self.readings if abs(r.angle_d) < self.fov]
            self.readings = temp

        # Add noise model
        self.noise()

    def noise(self):
        pass

    def getNew(self):
        """ This method returns the current readings """

        return self.readings
        
    def start(self):
        self.robot.colored_blob_omnidirectional_camera.enable()

    def stop(self):
        pass
