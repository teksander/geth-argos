#!/usr/bin/env python3
import random, math
import time
import logging

class RandomWalk(object):
    """ Set up a Random-Walk loop on a background thread
    The __walking() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self, robot, MAX_SPEED):
        """ Constructor
        :type range: int
        :param enode: Random-Walk speed (tip: 500)
        """
        self.__stop = 1
        self.__walk = True

        # General Parameters
        self.robot = robot
        self.MAX_SPEED = MAX_SPEED/50                          

        # Random walk parameters
        self.remaining_walk_time = 3
        self.my_lambda = 10              # Parameter for straight movement
        self.turn = 4
        self.possible_directions = ["straight", "cw", "ccw"]
        self.actual_direction = "straight"

        # Navigation parameters
        self.L = 0.053                    # Distance between wheels
        self.R = 0.0205                   # Wheel radius
        self.Kp = 5                       # Proportional gain
        self.thresh = math.radians(15)    # Wait before moving

        # Obstacle avoidance parameters
        self.ir_tresh = 0.05
        self.weights_left  = 25*[-10, -10, -5, 0, 0, 5, 10, 10]
        self.weights_right = 25*[-1 * x for x in self.weights_left]

    def step(self):
        """ This method runs in the background until program is closed """

        left, right = 0, 0

        if self.__walk:
            left, right = self.random(left, right)

        left, right = self.avoid(left, right)

        left, right = self.saturate(left, right)
        
        # Set wheel speeds
        self.robot.epuck_wheels.set_speed(right, left)


    def random(self, left, right):   
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

        return left, right

    def navigate(self, location = [0,0]):

        position_current = self.robot.position.get_position()[0:2]
        position_desired = location
        position_error = ((position_desired[0]-position_current[0]),(position_desired[1]-position_current[1]))

        orientation_current = self.robot.position.get_orientation()
        orientation_desired = math.atan2(position_error[1], position_error[0])
        orientation_error = math.atan2(math.sin(orientation_desired-orientation_current), math.cos(orientation_desired-orientation_current))
        
        # Tune controller rules here
        orientation_error_dot = -self.Kp * orientation_error

        # Find Wheel Speed for navigation
        v = 0
        if abs(orientation_error) < self.thresh:
            v = math.sqrt(position_error[0]**2 + position_error[1]**2)
            
        right = (2*v + self.L*orientation_error_dot) / (2*self.R)
        left = (2*v - self.L*orientation_error_dot) / (2*self.R)


        left, right = self.saturate(left, right, 2)

        left, right = self.avoid(left, right)

        left, right = self.saturate(left, right, 1)

        self.robot.epuck_wheels.set_speed(right, left)

        self.__hasArrived = math.sqrt(position_error[0]**2 + position_error[1]**2) < 0.05


    def avoid(self, left, right):

        # Obstacle avoidance
        readings = self.robot.epuck_proximity.get_readings()
        self.ir = [reading.value for reading in readings]
                
        # Find Wheel Speed for Obstacle Avoidance
        for i, reading in enumerate(self.ir):
            if(reading > self.ir_tresh):
                left  = self.MAX_SPEED/2 + self.weights_left[i] * reading
                right = self.MAX_SPEED/2 + self.weights_right[i] * reading

        return left, right

    def saturate(self, left, right, style = 1):
        # Saturate Speeds greater than MAX_SPEED

        if style == 1:

            if left > self.MAX_SPEED:
                left = self.MAX_SPEED
            elif left < -self.MAX_SPEED:
                left = -self.MAX_SPEED

            if right > self.MAX_SPEED:
                right = self.MAX_SPEED
            elif right < -self.MAX_SPEED:
                right = -self.MAX_SPEED

        else:

            if abs(left) > self.MAX_SPEED or abs(right) > self.MAX_SPEED:
                left = left/max(abs(left),abs(right))*self.MAX_SPEED
                right = right/max(abs(left),abs(right))*self.MAX_SPEED

        return left, right


    def hasArrived(self):
        return self.__hasArrived

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

    def start(self):
        pass

    def stop(self):
        pass




	
