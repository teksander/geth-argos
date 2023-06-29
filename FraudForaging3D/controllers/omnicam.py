#!/usr/bin/env python3
import math, random, time
import logging
import colorsys

def bgr_to_hsv(bgr):
    h,s,v = colorsys.rgb_to_hsv(*bgr[::-1])
    return (h*180, s*255, v)

class omnicam_reading(object):
    def __init__(self, color, angle, distance):
        self.color     = color
        self.color_rgb = color
        self.color_bgr = color[::-1]
        self.color_hsv = bgr_to_hsv(self.color_bgr)
        self.distance  = distance
        self.angle     = angle
        self.angle_d   = math.degrees(angle)

    def __repr__(self):
        return repr(self.__dict__)

class OmniCam(object):
    """ Set up ARGoS3 colored_blob_omnidirectional_camera

    """
    def __init__(self, robot, fov = 360):
        """ Constructor
        :type fov: str
        :param fov: field of view in degrees (tip: 45)
        """
        self.robot = robot
        self.readings  = []
        

        self.robot.colored_blob_omnidirectional_camera.enable()
        self.robot.colored_blob_omnidirectional_camera.set_fov(math.radians(fov))

        logging.basicConfig(format='[%(levelname)s %(name)s %(relativeCreated)d] %(message)s')
        logger = logging.getLogger(__name__)

    def step(self):
        """ Execute at every timestep
        """  
        # Read data from the colored_blob_omnidirectional_camera
        self.readSensor()

        # Add noise model
        self.addNoise()

    def readSensor(self):
        readings = self.robot.colored_blob_omnidirectional_camera.get_readings()
        self.readings = [omnicam_reading(*r) for r in readings]

    def addNoise(self):
        pass

    def getNew(self):
        """ This method returns the current readings """
        return self.readings
    
    def get_reading(self):
        """ This method returns the current readings """
        if self.readings:
            return self.readings[0]
        else:
            return None
    
    def start(self):
        pass

    def stop(self):
        pass
