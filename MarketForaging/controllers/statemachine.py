#!/usr/bin/env python3
from aenum import Enum, auto


class State(Enum):

    class Explorer(Enum):
        EXPLORE = auto()
        GO_TO_MARKET = auto()
        GO_TO_RESOURCE = auto()
    class Recruit(Enum):
        GO_TO_MARKET = auto()
        GO_TO_RESOURCE = auto()

class Transition(Enum):

    class Explorer(Enum):
        EXPLORE = auto()
        GO_TO_MARKET = auto()
        GO_TO_RESOURCE = auto()
    class Recruit(Enum):
        GO_TO_MARKET = auto()
        GO_TO_RESOURCE = auto()

class FiniteStateMachine(object):
    """ Establish the FMS class 
    """
    def __init__(self, robot = None):
        self.state = None

    def transition(self, _to, _from = None ):
        if _from:
            if self.state != _from:



    def step(self):
        """ Logic for state transitions. Lots of if statements
        """

        # Do I have enough money to explore? YES -> Become Explorer
        if robot.w3.getBalance() > explorationThresh:
            self.transition(State.Explorer.EXPLORE)

        # # Do I have food? YES -> Go to market
        # if robot.variables.get_attribute("hasResource"):
        #     self.state = States.GO_TO_MARKET

        # # Do I know location? NO -> Explore
        # elif robot.variables.get_attribute("currentResource"):
        #     self.state = States.EXPLORE




    def getState(self):
        return self.state


if __name__== '__main__':
    fsm = FiniteStateMachine()