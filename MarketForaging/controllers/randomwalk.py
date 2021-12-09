#!/usr/bin/env python3
import random, math
import time
import logging
from aux import Vector2D


rays_file = 'rays.txt'


class Navigate(object):
    """ Set up a Navigation loop on a background thread
    The __navigating() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self, robot, MAX_SPEED):
        """ Constructor
        :type range: int
        :param enode: Random-Walk speed (tip: 500)
        """
        self.__stop = 1
        self.__walk = True
        self.__id = str(int(robot.variables.get_id()[2:])+1)
        self.__distance_to_target = None
        self.__window = []
        self.robot = robot
        
       
        # Navigation parameters
        self.MAX_SPEED = MAX_SPEED/50 
        self.window_size = 10  
        self.L = 0.053                    # Distance between wheels
        self.R = 0.0205                   # Wheel radius
        self.Kp = 5                       # Proportional gain
        self.thresh = math.radians(70)    # Wait before moving
        self.thresh_front_collision = math.radians(45)    # Wait before moving

        # Obstacle avoidance parameters
        self.ir_tresh = 0.05
        self.weights_left  = 10*[-10, -10, 0, 0, 0, 0, 10, 10]
        self.weights_right = 10*[-1 * x for x in self.weights_left]

        self.old_vec  = 0
        self.old_time = 0
        self.accumulator_I = 0
        self.__distance_traveled = 0

    def navigate_with_obstacle_avoidance(self, location = [0,0]):

        # Get the current positions and orientation of the robot
        position = self.robot.position.get_position()[0:2]
        orientation = self.robot.position.get_orientation()

        # Calculate the local frame vector to the desired target
        vec_target = Vector2D(location)-Vector2D(position)
        vec_target = vec_target.rotate(-orientation)

        # Calculate the local frame vector to the avoid objects
        acc = Vector2D()
        prox_readings = self.robot.epuck_proximity.get_readings()

        for reading in prox_readings:
            acc += Vector2D(reading.value, reading.angle.value(), polar = True)

        # Generate a time window to have smoother variations on the avoid vector
        self.__window.append(acc)

        if len(self.__window) > self.window_size:
            self.__window.pop(0)
        
        vec_avoid = Vector2D()
        for i in self.__window:
            vec_avoid = vec_avoid+i
        vec_avoid = 1/self.window_size * vec_avoid

        if abs(vec_avoid) < 0.01:
            self.__window = []

        # vec_target and vec_avoid are now weighted to obtain desired control behavior
        T = 0.2 * vec_target.normalize()
        A = 0.3 * vec_avoid#.normalize()


        # Integral action on the avoid could make sense
        def trapz(new_time, new_vec):

            trap = 0.5 * (new_vec+self.old_vec)
            self.accumulator_I += 0.1*trap
            self.old_vec = new_vec
            self.old_time = new_time

        trapz(time.time(), A.length)
        # print(self.accumulator_I)

        if abs(A) < 0.01:
            self.accumulator_I = 0

        elif self.accumulator_I > 1:
            self.accumulator_I = 1

        # Calculate the local frame vector to the desired motion (target + avoid)
        A = A + self.accumulator_I*A


        # The desired vector (we only care about direction)
        D =  (T - A) #.normalize()

        # Change to global coordinates for the plotting
        self.robot.variables.set_attribute("rays", self.__id + ', ' + repr(position) + ', ' + repr(vec_target.rotate(orientation)) + ', ' + repr(-A.rotate(orientation))+ ', ' + repr(D.rotate(orientation)) +'\n')

        dotProduct = 0
        Kp = 50

        # The target angle is behind the robot, we just rotate, no forward motion
        if D.angle > self.thresh or D.angle < -self.thresh:
            dotProduct = 0

        # Compute the projection of the forward motion vector with the desired angle
        else:
            
            dotProduct = Vector2D(1,0).dot(D.normalize())

        # The angular velocity component is the desired angle scaled linearly
        angularVelocity = Kp * D.angle

        # The final wheel speeds are computed combining the forward and angular velocities, with different signs for the left and right wheel.
        right = dotProduct * self.MAX_SPEED/2 - angularVelocity * self.L
        left = dotProduct * self.MAX_SPEED/2 + angularVelocity * self.L

        # # Saturate wheel speeds
        # left, right = self.saturate(left, right)

        # if  0.01< abs(vec_avoid.angle) < self.thresh_front_collision:
        #     print(math.degrees(vec_avoid.angle), "Front Collision")
        #     left, right = self.avoid(left, right)


        # Set wheel speeds
        self.robot.epuck_wheels.set_speed(right, left)

        # Accumulate the costs of movement
        self.__distance_traveled += (right + left)/2 

        # Store the distance to arrive at target
        self.__distance_to_target = abs(vec_target)

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

    def get_distance_to_target(self):
        return self.__distance_to_target

    def get_distance_traveled(self, reset = False):
        temp = self.__distance_traveled

        if reset:
            self.__distance_traveled = 0

        return temp

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
        self.__id = str(int(robot.variables.get_id()[2:])+1)
        self.__distance_to_target = None

        # General Parameters
        self.robot = robot
        self.MAX_SPEED = MAX_SPEED/50                          

        # Random walk parameters
        self.remaining_walk_time = 3
        self.my_lambda = 10              # Parameter for straight movement
        self.turn = 4
        self.possible_directions = ["straight"]#, "cw", "ccw"]
        self.actual_direction = "straight"

        # Navigation parameters
        self.L = 0.053                    # Distance between wheels
        self.R = 0.0205                   # Wheel radius
        self.Kp = 5                       # Proportional gain
        self.thresh = math.radians(70)    # Wait before moving

        # Obstacle avoidance parameters
        self.ir_tresh = 0.05
        self.weights_left  = 25*[-10, -10, 0, 0, 0, 0, 10, 10]
        self.weights_right = 25*[-1 * x for x in self.weights_left]


        self.vec_avoid = []
        self.old_time = time.time()
        self.old_vec = 0
        self.accumulator_I = 0
        self.__distance_traveled = 0

    def step(self):
        """ This method runs in the background until program is closed """

        if self.__walk:
            self.random()

        # self.avoid_vec_lua_erb(0,0)

    def random(self):   
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

        # Avoid Obstacles
        left, right = self.avoid(left, right)
        left, right = self.saturate(left, right)

        # Set wheel speeds
        self.robot.epuck_wheels.set_speed(right, left)

        # Accumulate the costs of movement
        self.__distance_traveled += (right + left)/2 

        self.robot.variables.set_attribute("rays", "")
        
    def get_distance_traveled(self, reset = False):
        temp = self.__distance_traveled

        if reset:
            self.__distance_traveled = 0

        return temp


    def navigate(self, location = [0,0]):

        position_error = Vector2D(location)-Vector2D(self.robot.position.get_position()[0:2])

        orientation_current = self.robot.position.get_orientation()
        _, orientation_desired = position_error.to_polar()
        orientation_error = math.atan2(math.sin(orientation_desired-orientation_current), math.cos(orientation_desired-orientation_current))
        
        # Tune controller rules here
        orientation_error_dot = -self.Kp * orientation_error

        # Find Wheel Speed for navigation
        v = 0
        if abs(orientation_error) < self.thresh:
            # v = math.sqrt(position_error[0]**2 + position_error[1]**2)
            v = self.MAX_SPEED/2
            
        right = (2*v + self.L*orientation_error_dot) / (2*self.R)
        left = (2*v - self.L*orientation_error_dot) / (2*self.R)

        left, right = self.saturate(left, right, 2)

        # Avoid Obstacles
        left, right = self.avoid_vec_lua(left, right)
        left, right = self.saturate(left, right, 1)

        # Set wheel speeds
        self.robot.epuck_wheels.set_speed(right, left)
        self.__hasArrived = abs(position_error) < 0.05

    

    def avoid_vec_lua(self, left, right):
        # Obstacle avoidance; translated from LUA
        # Source: swarm intelligence ULB course

        accumul = Vector2D(0,0)

        readings = self.robot.epuck_proximity.get_readings()
        
        for reading in readings:

            # We calculate the x and y components given length and angle
            vec = Vector2D(reading.value, reading.angle.value(), polar = True)

            # We sum the vectors into a variable called accumul
            accumul += vec

        # We get length and angle of the final sum vector
        length, angle = accumul.to_polar()

        if length > 0.01:
            # print(length)
            # If the angle is greater than 0 the resulting obstacle is on the left. 
            # Otherwise it is on the right
            # We turn with a speed that depends on the angle. 
            # The closer the obstacle to the x axis of the robot, the quicker the turn
            speed = max(0.5, math.cos(angle)) * self.MAX_SPEED

            if angle > 0:
                right = speed
                left = 0
            else:
                right = 0
                left = speed

        return left, right

    def flocking_argos_python_example(self):
        NO_TURN = 0
        SOFT_TURN = 1
        HARD_TURN = 2

        turning_mechanism = NO_TURN

        hard_turn_angle_threshold = 90 * math.pi / 180
        soft_turn_angle_threshold = 70 * math.pi / 180
        no_turn_angle_threshold = 10 * math.pi / 180

        max_speed = 10

        target_distance = 0.2
        gain = 1000
        exponent = 2

        def lennard_jones(distance):
            return -(4*gain/distance * (math.pow(target_distance/distance,exponent*exponent) - math.pow(target_distance/distance,exponent)))

        def vector_to_light():

            position_current = Vector2D(self.robot.position.get_position()[0], self.robot.position.get_position()[1])
            position_desired = Vector2D(0,0)
            position_error = position_desired-position_current

            tot_length, tot_angle = position_error.to_polar()

            if tot_length > 0:
                tot_length = 0.25 * max_speed

            return {"length": tot_length, "angle": tot_angle}

        def flocking_vector():

            erb_readings = self.robot.epuck_range_and_bearing.get_packets()
            accumulator = {"x": 0, "y": 0}
            flj = 0
            num_blobs_seen = 0.1

            if erb_readings:
                for reading in erb_readings:
                    if reading.range/100 < target_distance * 1.8:

                        flj = lennard_jones(reading.range/100)

                        ori = self.robot.position.get_orientation()

                        accumulator["x"] += flj * math.cos(reading.bearing.value()+ori) 
                        accumulator["y"] += flj * math.sin(reading.bearing.value()+ori)
                        num_blobs_seen += 1

                tot_angle = math.atan2(accumulator["y"], accumulator["x"])
                tot_length = math.sqrt(accumulator["x"] * accumulator["x"] + accumulator["y"] * accumulator["y"]) / num_blobs_seen

                if tot_length > max_speed:
                    tot_length = max_speed

                return {"length": tot_length, "angle": tot_angle}
            else:
                return {"length": 0, "angle": 0}

        vector_light = vector_to_light()

        vector_flocking = flocking_vector()

        tot_speed = vector_light["length"] + vector_flocking["length"]
        tot_angle = vector_light["angle"] + vector_flocking["angle"]

        if tot_speed > max_speed:
            tot_speed = max_speed
        
        if math.fabs(tot_angle) <= no_turn_angle_threshold:
            turning_mechanism = NO_TURN
        elif math.fabs(tot_angle) > hard_turn_angle_threshold:
            turning_mechanism = HARD_TURN
        elif turning_mechanism == NO_TURN and math.fabs(tot_angle) > soft_turn_angle_threshold:
            turning_mechanism = SOFT_TURN

        speed1 = 0
        speed2 = 0
        if turning_mechanism == NO_TURN:
            speed1 = tot_speed
            speed2 = tot_speed
        elif turning_mechanism == SOFT_TURN:
            speed_factor = (hard_turn_angle_threshold - math.fabs(tot_angle))/hard_turn_angle_threshold
            speed1 = tot_speed - tot_speed * (1 - speed_factor)
            speed2 = tot_speed + tot_speed + (1 - speed_factor)
        elif turning_mechanism == HARD_TURN:
            speed1 = -max_speed
            speed2 = max_speed

        if tot_angle > 0:
            self.robot.epuck_wheels.set_speed(speed1, speed2)
            # left, right = speed1, speed2
        else:
            self.robot.epuck_wheels.set_speed(speed2, speed1)

    def pattern_formation_swarm_intelligence(self, target = None):
        TARGET_DIST = 10 # -- the target distance between robots, in cm
        EPSILON = 50 # -- a coefficient to increase the force of the repulsion/attraction function
        WHEEL_SPEED = 5 # -- max wheel speed

        #---------------------------------------------------------------------------

        # ---------------------------------------------------------------------------
        # --This function computes the necessary wheel speed to go in the direction of the desired angle.
        def ComputeSpeedFromAngle(angle):
            dotProduct = 0
            KProp = 20
            wheelsDistance = 0.053

            # -- if the target angle is behind the robot, we just rotate, no forward motion
            if angle > math.pi/2 or angle < -math.pi/2:
                dotProduct = 0
            else:
            # -- else, we compute the projection of the forward motion vector with the desired angle
                forwardVector = [math.cos(0), math.sin(0)]
                targetVector = [math.cos(angle), math.sin(angle)]
                dotProduct = forwardVector[0]*targetVector[0]+forwardVector[1]*targetVector[1]

             # -- the angular velocity component is the desired angle scaled linearly
            angularVelocity = KProp * angle;
            # -- the final wheel speeds are compute combining the forward and angular velocities, with different signs for the left and right wheel.
            speeds = [dotProduct * WHEEL_SPEED - angularVelocity * wheelsDistance, dotProduct * WHEEL_SPEED + angularVelocity * wheelsDistance]

            return speeds
        # ---------------------------------------------------------------------------

        # ---------------------------------------------------------------------------
        # -- In this function, we take all distances of the other robots and apply the lennard-jones potential.
        # -- We then sum all these vectors to obtain the final angle to follow in order to go to the place with the minimal potential
        def ProcessRAB_LJ(target):

            sum_vector = [0,0]
            erb_readings = self.robot.epuck_range_and_bearing.get_packets()

            for reading in erb_readings: #do -- for each robot seen
                lj_value = 0.1*ComputeLennardJonesRep(reading.range) # -- compute the lennard-jones value
                sum_vector[0] = sum_vector[0] + math.cos(reading.bearing.value())*lj_value # -- sum the x components of the vectors
                sum_vector[1] = sum_vector[1] + math.sin(reading.bearing.value())*lj_value # -- sum the y components of the vectors

            if target:
                x, y = self.robot.position.get_position()[0], self.robot.position.get_position()[1]
                theta = self.robot.position.get_orientation()

                position = Vector2D(x,y)
                target = Vector2D(target[0],target[1])
                vec_to_target = target-position
                mag, ang = vec_to_target.to_polar()


                lj_value = 10*ComputeLennardJones(mag*100)
                sum_vector[0] = sum_vector[0] + math.cos(ang-theta)*lj_value # -- sum the x components of the vectors
                sum_vector[1] = sum_vector[1] + math.sin(ang-theta)*lj_value # -- sum the y components of the vectors

            desired_angle = math.atan2(sum_vector[1],sum_vector[0]) # -- compute the angle from the vector
            # --log( "angle: "..desired_angle.." length^2: "..(math.pow(sum_vector[1],2)+math.pow(sum_vector[2],2)) )
            return desired_angle

        # ---------------------------------------------------------------------------

        # ---------------------------------------------------------------------------
        # -- This function take the distance and compute the lennard-jones potential.
        # -- The parameters are defined at the top of the script
        def ComputeLennardJones(distance):
           return -(4*EPSILON/distance * (math.pow(TARGET_DIST/distance,4) - math.pow(TARGET_DIST/distance,2)))

        def ComputeLennardJonesRep(distance):
           return -(4*EPSILON/distance * (math.pow(TARGET_DIST/distance,4)))

        #---------------------------------------------------------------------------

        target_angle = ProcessRAB_LJ(target) #-- then we compute the angle to follow, using the other robots as input, see function code for details
        speeds = ComputeSpeedFromAngle(target_angle) #-- we now compute the wheel speed necessary to go in the direction of the target angle
        # self.robot.wheels.set_velocity(speeds[1],speeds[2]) #-- actuate wheels to move
        self.robot.epuck_wheels.set_speed(speeds[0],speeds[1])

        self.__hasArrived = 0

        # robot.range_and_bearing.clear_data() #-- forget about all received messages for next step
        # ---------------------------------------------------------------------------

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
        
    def avoid_vec_lua_erb(self, left, right):
        # Obstacle avoidance; translated from LUA
        # Source: swarm intelligence ULB course

        accumul = Vector2D(0,0)

        pos = tuple(self.robot.position.get_position()[0:2])
        ori = self.robot.position.get_orientation()

        readings = self.robot.epuck_range_and_bearing.get_readings()
        
        for reading in readings:

            # if reading[2] < math.radians(15):
            #     continue

            # else:
            # We calculate the x and y components given length and angle
            vec = Vector2D(reading[1]/100, reading[2]+ori, polar=True)

            # We sum the vectors into a variable called accumul
            accumul += vec

        # We get length and angle of the final sum vector
        length, angle = accumul.to_polar()
        # print(length, angle)

        if 0.05 < length < 0.1:
            # If the angle is greater than 0 the resulting obstacle is on the left. 
            # Otherwise it is on the right
            # We turn with a speed that depends on the angle. 
            # The closer the obstacle to the x axis of the robot, the quicker the turn
            speed = max(0.5, math.cos(angle)) * self.MAX_SPEED
            if angle > 0:
                right = speed
                left = 0
            else:
                right = 0
                left = speed

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




	
