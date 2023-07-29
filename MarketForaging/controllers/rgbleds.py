#!/usr/bin/env python3
import time

class RGBLEDs(object):
    """ Request a measurement from the Ground Sensors
    GroundSensor.getNew() returns the measurement of each sensor
    """
    def __init__(self, robot):
        """ Constructor
        """
        self.robot = robot

        self.led1 = 0x00
        self.led2 = 0x01
        self.led3 = 0x02
        self.all = [self.led1, self.led2, self.led3]

        self.red = 'red'
        self.green = 'green'
        self.blue = 'blue'
        self.off = 'black'
        self.white = 'white'

        self.presets = {
                        0: ['black', 'black', 'black'],
                        1: ['red', 'black', 'black'],
                        2: ['red', 'black', 'red']
                        }
        
        self.frozen = False

    def setLED(self, LED, RGB):
        if not self.frozen:
            for i in range(len(LED)):
                self.robot.epuck_leds.set_single_color(LED[i], RGB[i])

    def flashRed(self, delay=1):
        if not self.frozen:
            self.setLED(self.all, 3*[self.red])
            time.sleep(delay)
            self.setLED(self.all, 3*[self.off])

    def flashGreen(self, delay=1):
        if not self.frozen:
            self.setLED(self.all, 3*[self.green])
            time.sleep(delay)
            self.setLED(self.all, 3*[self.off])

    def flashBlue(self, delay=1):
        if not self.frozen:
            self.setLED(self.all, 3*[self.blue])
            time.sleep(delay)
            self.setLED(self.all, 3*[self.off])

    def flashWhite(self, delay=1):
        if not self.frozen:
            self.setLED(self.all, 3*[self.white])
            time.sleep(delay)
            self.setLED(self.all, 3*[self.off])

    def freeze(self):
        self.frozen = True

    def unfreeze(self):
        self.frozen = False

    def stop(self):
        self.unfreeze()
        self.setLED(self.all, 3* [self.off])