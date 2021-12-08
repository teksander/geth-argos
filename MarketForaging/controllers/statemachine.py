#!/usr/bin/env python3
from aenum import Enum, auto

class Idle(Enum):
    IDLE = 1

class Explorer(Enum):
    EXPLORE = 2
    GO_TO_MARKET = 3
    GO_TO_RESOURCE = 4

class Recruit(Enum):
    WAIT = 5
    FORAGE = 6
    GO_TO_MARKET = 7
    GO_TO_RESOURCE = 8

class FiniteStateMachine(object):

    def __init__(self, robot = None):

        self.Idle = Idle
        self.Explorer = Explorer
        self.Recruit = Recruit

        self._currState = self.Idle.IDLE
    
    def getState(self):
        return self._currState

    def setState(self, state):
        self._currState = state
        mainlogger.info("Robot state is " + str(self._currState) )


if __name__== '__main__':
    fsm = FiniteStateMachine()