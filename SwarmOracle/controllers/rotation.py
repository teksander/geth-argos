#!/usr/bin/env python3
import random, math
import time
import logging

logging.basicConfig(format='[%(levelname)s %(name)s %(relativeCreated)d] %(message)s')
logger = logging.getLogger(__name__)


class Rotation(object):
    """ Set up a rotation movement class
    """

    def __init__(self, robot, MAX_SPEED):
        """ Constructor
        :param MAX_SPEED: Random-Walk speed (tip: 500)
        :type MAX_SPEED: int
        """
        self.MAX_SPEED = MAX_SPEED
        self.robot     = robot
        self.__stop = True
        self.__walk = True
        self.__pattern = "s"
        self.duration = -1 #if duration == -1: run forever
        self.mode = "pattern" #pattern or speed
        self.left = 0
        self.right = 0 
        self.irDist = 200

        logger.info('Random-Walk OK')

    def step(self):
        """ This method runs in the background until program is closed """
        
        if self.__stop:
            self.stop()

        else:

            this_left = 0
            this_right = 0

            if self.mode == "pattern":
                if self.duration > 0 and self.duration != -1:
                    self.duration -= 1
                elif self.duration == 0:
                    self.__walk = False

                # Find Wheel Speed for Random-Walk
                if (self.__pattern == "cw"):
                    this_left = self.MAX_SPEED / 2
                    this_right = -self.MAX_SPEED / 2
                elif (self.__pattern == "ccw"):
                    this_left = -self.MAX_SPEED / 2
                    this_right  = self.MAX_SPEED / 2
                elif (self.__pattern == "s"):
                    this_left = self.MAX_SPEED / 2
                    this_right = self.MAX_SPEED / 2
                #print(self.__pattern, " set wheel speed to: ", this_left, this_right)

            elif self.mode == "speed":
                self.__walk = True
                this_left = self.left
                this_right = self.right

            # Avoid Obstacles
            this_left, this_right = self.avoid_argos3_example(this_left, this_right)

            # Saturate Speeds greater than MAX_SPEED
            if this_left > self.MAX_SPEED:
                this_left  = self.MAX_SPEED
            elif this_left  < -self.MAX_SPEED:
                this_left  = -self.MAX_SPEED

            if this_right > self.MAX_SPEED:
                this_right = self.MAX_SPEED
            elif this_right < -self.MAX_SPEED:
                this_right = -self.MAX_SPEED
            #print(self.__pattern, " final wheel speed: ", this_left, this_right)

            if self.__walk:
                self.setWheels(this_left, this_right)
            else:
                self.setWheels(0, 0)

    def start(self):
        """ This method is called to start movement controller"""
        if self.__stop:
            self.__stop = False
        else:
            logger.warning('Already Walking')

    def stop(self):
        """ This method is called before a clean exit """
        self.setWheels(0,0)
        logger.info('Random-Walk OFF')

    def setWalk(self, state):
        """ This method is called set the random-walk to on without disabling I2C"""
        self.__walk = state

    def isWalking(self):
        return self.__walk
    
    def setPattern(self, pattern, duration):
        self.__pattern = pattern
        self.duration  = duration
        if self.__walk == False:
            self.__walk = True

    def setPattern_duration(self, pattern, duration):
        if self.duration <= 0:
            self.__pattern=pattern
            self.duration=duration
            if self.__walk == False:
                self.__walk = True

    def setDrivingSpeed(self, left, right):
        self.left = left
        self.right = right

    def setDrivingMode(self, mode):
        self.mode=mode

    def setWheels(self, left, right):
        """ This method is called set each wheel speed """
        self.robot.epuck_wheels.set_speed(int(left), int(right))

    def setLEDs(self, state):
        """ This method is called set the outer LEDs to an 8-bit state """
        if self.__LEDState != state:
            self.__isLEDset = False
            self.__LEDState = state

    def getIr(self):
        """ This method returns the IR readings """
        return self.ir

    def avoid(self, left = 0, right = 0, move = False):

        obstacle = avoid_left = avoid_right = 0

        # Obstacle avoidance
        readings = self.robot.epuck_proximity.get_readings()
        self.ir = [reading.value for reading in readings]
                
        # Find Wheel Speed for Obstacle Avoidance
        for i, reading in enumerate(self.ir):
            if reading > self.thresh_ir:
                obstacle = True
                avoid_left  += self.weights[i] * reading
                avoid_right -= self.weights[i] * reading

        if obstacle:
            left  = self.MAX_SPEED/2 + avoid_left
            right = self.MAX_SPEED/2 + avoid_right

        if move:
            self.robot.epuck_wheels.set_speed(left, right)

        return left, right
    
    def avoid_argos3_example(self, left, right):
        # Obstacle avoidance; translated from C++
        # Source: https://github.com/ilpincy/argos3-examples/blob/master/controllers/epuck_obstacleavoidance/epuck_obstacleavoidance.cpp
        
        readings = self.robot.epuck_proximity.get_readings()
        self.ir = [reading.value for reading in readings]

        fMaxReadVal = self.ir[0]
        unMaxReadIdx = 0

        if(fMaxReadVal < self.ir[1]): 
            fMaxReadVal = self.ir[1]
            unMaxReadIdx = 1

        if(fMaxReadVal < self.ir[7]): 
            fMaxReadVal = self.ir[7]
            unMaxReadIdx = 7

        if(fMaxReadVal < self.ir[6]): 
            fMaxReadVal = self.ir[6]
            unMaxReadIdx = 6

        # Do we have an obstacle in front?
        if(fMaxReadVal > 0):
            # Yes, we do: avoid it 
            if(unMaxReadIdx == 0 or unMaxReadIdx == 1): 
                # The obstacle is on the left, turn right 
                left, right = -self.MAX_SPEED/2, self.MAX_SPEED/2
            else: 
                # The obstacle is on the left, turn right 
                left, right = -self.MAX_SPEED/2, self.MAX_SPEED/2       

        return left, right
    
if __name__ == "__main__":
    rot = Rotation(500)
    rot.start()
    input("any key to straight")
    rot.setPattern("s",100)
    input("any key to turn cw")
    rot.setPattern("cw", 100)
    input("any key to turn ccw")
    rot.setPattern("ccw", 100)
    input("any key to stop")
    rot.setWalk(False)
    input("any key to disconnect")
    rot.stop()




