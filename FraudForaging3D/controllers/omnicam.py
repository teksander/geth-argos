#!/usr/bin/env python3
import math, random, time
import logging
import colorsys

def bgr_to_hsv(bgr):
    h,s,v = colorsys.rgb_to_hsv(*bgr[::-1])
    return (int(h * 180), int(s * 255), int(v))

class omnicam_reading(object):
    def __init__(self, color, angle, distance, util):
        self.color     = color
        self.color_rgb = color
        self.color_bgr = color[::-1]
        self.color_hsv = bgr_to_hsv(self.color_bgr)
        self.distance  = distance
        self.angle     = angle
        self.angle_d   = math.degrees(angle)
        self.util = util

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

        # Hard coded colors
        self.colors = ['red', 'blue', 'green']
        self.init_simulated_readings()


        logging.basicConfig(format='[%(levelname)s %(name)s %(relativeCreated)d] %(message)s')
        logger = logging.getLogger(__name__)

    def step(self):
        """ Execute at every timestep
        """  
        # Read data from the colored_blob_omnidirectional_camera
        self.read_simulated_sensor()


    def init_simulated_readings(self):
        self.rgb_samples = dict()
        for color in self.colors:
            file = open(f"controllers/color_data/{color}.csv")
            self.rgb_samples[color] = []
            for line in file:
                self.rgb_samples[color].append([float(a) for a in line.split(",")])
            file.close()
    
    def read_simulated_sensor(self):
        readings = self.robot.colored_blob_omnidirectional_camera.get_readings()
        this_util = 0
        for i, _ in enumerate(readings):
            if readings[i][0] == [255, 0, 0]:
                readings[i][0] = random.sample(self.rgb_samples['red'], k = 1)[0]
                this_util = 2
            if readings[i][0] == [0, 255, 0]:
                readings[i][0] = random.sample(self.rgb_samples['green'], k = 1)[0]
                this_util = 1
            if readings[i][0] == [0, 0, 255]:
                readings[i][0] = random.sample(self.rgb_samples['blue'], k = 1)[0]
                this_util = 1
            readings[i][0] = [round(a) for a in readings[i][0]]
            readings[i] += [this_util]
        self.readings = [omnicam_reading(*r) for r in readings]
        # if self.readings:
        #     print(self.readings[0])

    def read_argos_sensor(self):
        readings = self.robot.colored_blob_omnidirectional_camera.get_readings()
        self.readings = [omnicam_reading(*r) for r in readings]

    def getNew(self):
        """ This method returns the current readings """
        return self.readings
    
    def get_reading(self):
        """ This method returns the current reading (just one) """
        if self.readings:
            return self.readings[0]
        else:
            return None
    
    def start(self):
        pass

    def stop(self):
        pass
