#!/usr/bin/env python3
import time
from aenum import Enum, auto
from aux import Timer

class Idle(Enum):
    IDLE    = 1

class Scout(Enum):
    SELL    = 2
    EXPLORE = 3
    HOMING  = 4

class Recruit(Enum):
    BUY    = 5
    FORAGE = 6
    HOMING = 7
    PLAN   = 8
    DROP   = 9

class States(Enum):
    INIT   = 1
    PLAN   = 2
    SCOUT  = 3
    FORAGE = 4
    SELL   = 5
    BUY    = 6
    DROP   = 7 
    QUEUE  = 8

stateList = list(Idle)+list(Scout)+list(Recruit)

class FiniteStateMachine(object):

    def __init__(self, robot, start = None):
        self.robot     = robot
        self.prevState = start
        self.currState = start
        self.accumTime = dict()
        self.startTime = time.time()

    def getPreviousState(self):
        return self.prevState

    def getState(self, ):
        return self.currState

    def getTimers(self):
        return self.accumTime

    def setState(self, state, message = ""):

        self.onTransition(state, message)

        if self.currState not in self.accumTime:
            self.accumTime[self.currState] = 0

        self.accumTime[self.currState] += time.time() - self.startTime
        self.prevState = self.currState
        self.currState = state
        self.startTime = time.time()
    
    def query(self, state, previous = False):
        if previous:
            return self.prevState == state
        else:
            return self.currState == state

    def onTransition(self, state, message):
        # Robot actions to perform on every transition

        if message != None:
            self.robot.log.info("%s -> %s%s", self.currState, state, ' | '+message)
        
        self.robot.variables.set_attribute("dropResource", "")
        self.robot.variables.set_attribute("state", str(state))



