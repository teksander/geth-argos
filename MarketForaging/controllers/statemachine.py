#!/usr/bin/env python3
from aenum import Enum, auto

class State(Enum):
    class Idle(Enum):
        IDLE = 1
    class Explorer(Enum):
        EXPLORE = 2
        GO_TO_MARKET = 3
        GO_TO_RESOURCE = 4
    class Recruit(Enum):
        WAIT = 5
        GO_TO_MARKET = 6
        GO_TO_RESOURCE = 7

class FiniteStateMachine(object):
    def __init__(self, robot = None):
        self._currState = State.Idle.IDLE
        self.transitions = dict()
    
    def getState(self):
        return self._currState

    def setState(self, state):
        self._currState = state

    def set_transitions(self):
        self.transitions[State.Idle.IDLE] = [{to: State.Explorer.EXPLORE, cond: self.trans1}, 
                                             {to: state.Recruit.WAIT, cond: self.trans2}]
        self.transitions[State.Explorer.EXPLORE] = [{to: State.Explorer.GO_TO_MARKET, cond: self.trans3}]
        self.transitions[State.Explorer.GO_TO_MARKET] = [{to: State.Idle.IDLE, cond: trans4},]

    def trans1(self):
        # If has enough money: Idle -> EXPLORE
        return 5 > 1
    def trans2(self):
        return not self.trans1()

    def trans3(self):
        return 5 == 5

    def step(self):
        transitions = self.transitions[_currState]

        for transition in transitions:
            if transition['cond']:
                self._currState = transition['to']
                print(transition['to'])


class Explorer(object):

    def EXPLORE():

        # Exploration scheme
        rw.random()

        # Collection of new resources
        resource_js = rs.getLatest()
        if resource_js:
            # mainlogger.debug('Got resources from sensor:'+resource_js)
            rb.addResource(resource_js)

            # Logic to define the price to sell resource for
            cost = rw.get_distance() * fuel_cost
            value = rb.getValue()
            price = 111111
            profit = cost - price

            # FSM transition to GO_TO_MARKET
            # To sell new resource
            if profit > 0:
                fsm.setState(fsm.Explorer.GO_TO_MARKET)

            if clocks['balance_check'].query():
                balance = w3.getBalance()

            # To be recruited
            if balance < 2 * nav.get_distance(0,0) * fuel_cost
                fsm.setState(fsm.Explorer.GO_TO_MARKET)

    def GO_TO_MARKET():
        nav.navigate_with_obstacle_avoidance((market_xn,market_yn))

        if nav.hasArrived():
            fsm.setState(fsm.Idle.IDLE)

    def GO_TO_RESOURCE():
        nav.navigate_with_obstacle_avoidance((resource_xn, resource_yn))

        if nav.hasArrived():
            fsm.setState(fsm.Idle.IDLE)


if __name__== '__main__':
    fsm = FiniteStateMachine()