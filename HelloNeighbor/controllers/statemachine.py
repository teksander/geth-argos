#!/usr/bin/env python3
import time
from aenum import Enum, auto
from aux import Timer

class States(Enum):
    START = 1
    WALK  = 2
    GREET = 3

class FiniteStateMachine(object):

    def __init__(self, robot, start = None):
        self.robot     = robot
        self.storage   = None
        self.prevState = start
        self.currState = start
        self.accumTime = dict()
        self.startTime = time.time()
        self.pass_along = None
        
    def setStorage(self,storage = None):
        self.storage = storage

    def getStorage(self):
        return self.storage

    def getPreviousState(self):
        return self.prevState

    def getState(self):
        return self.currState

    def getTimers(self):
        return self.accumTime

    def setState(self, state, message = "", pass_along = None):

        self.onTransition(state, message)

        if self.currState not in self.accumTime:
            self.accumTime[self.currState] = 0

        self.accumTime[self.currState] += time.time() - self.startTime
        self.prevState = self.currState
        self.currState = state
        self.startTime = time.time()
        self.pass_along = pass_along
    
    def query(self, state, previous = False):
        if previous:
            return self.prevState == state
        else:
            return self.currState == state

    def getAllStates(self):
        return list(States)

    def onTransition(self, state, message):
        # Robot actions to perform on every transition

        if message != None:
            self.robot.log.info("%s -> %s%s", self.currState, state, ' | '+message)
        
        self.robot.variables.set_attribute("dropResource", "")
        self.robot.variables.set_attribute("state", str(state))



