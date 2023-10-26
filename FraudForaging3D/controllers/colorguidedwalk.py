#!/usr/bin/env python3
import random, math

from os.path import exists

from controllers.omnicam import OmniCam, bgr_to_hsv
from controllers.movement import RandomWalk
from controllers.rotation import Rotation
from controllers.aux import Vector3D as v3d, PID, Timer, update_formater
import logging

logger = logging.getLogger('cwe')

# cam_int_reg_h = 200
# cam_int_reg_offest = 50
# cam_rot = True
hsv_threshold = [300, 300, 300]

def get_contours(cam_reading, ground_truth_hsv, hsv_threshold, name=None):

    if cam_reading:
        feature_dist = cam_reading.distance
        feature_cen  = cam_reading.angle_d
        feature_hsv  = v3d(cam_reading.color_hsv)

        # Obtain the low bound and high bound in h, s and v
        lb = v3d(ground_truth_hsv) - v3d(hsv_threshold)
        hb = v3d(ground_truth_hsv) + v3d(hsv_threshold)

        # Saturate h, s and v to their respective ranges
        lb  = lb.maximums(v3d(0, 0, 0)).minimums(v3d(180, 255, 255))
        hb = hb.maximums(v3d(0, 0, 0)).minimums(v3d(180, 255, 255))

        if lb <= feature_hsv <= hb:
            return feature_dist, feature_cen

    return 0, -1

class ColorWalkEngine(object):

    def __init__(self, robot, MAX_SPEED, bias_bgr = [1,1,1]):
        """ Constructor
        """
        update_formater(robot.variables.get_attribute("id"), logger)
        
        # Color inits
        self.colors = ["red", "blue", "green"]
        self.ground_truth_bgr = []  # bgr
        self.ground_truth_hsv = []  # bgr

        # Navigation inits
        self.max_speed= MAX_SPEED
        self.actual_rw_dir = "s"

        # Submodules
        self.robot = robot
        self.id  = int(robot.variables.get_attribute("id"))
        self.cam = OmniCam(robot, 45)
        self.rot = Rotation(robot, MAX_SPEED)
        self.cam.start()
        self.rot.start()
        
        # Timers
        self.timers = dict()
        self.timers['discover'] = Timer()
        self.drive = None

        # Calibration
        for idx, name in enumerate(self.colors):
            calibFile = f'controllers/color_data/{name}_calibration.csv'

            if exists(calibFile):
                with open(calibFile) as file:
                    line = file.readlines()[self.id]
                    elements = line.strip().split(',')
                    color_bgr  = [  int(bias_bgr[0]*float(elements[2])), 
                                    int(bias_bgr[1]*float(elements[1])), 
                                    int(bias_bgr[2]*float(elements[0]))]
                    color_hsv  = bgr_to_hsv(color_bgr)
                    self.ground_truth_bgr.append(color_bgr)
                    self.ground_truth_hsv.append(color_hsv)
            else:
                print(f"color calibration file not found, use hard coded colors")
                self.colors = ["red", "blue", "green"]
                self.ground_truth_bgr = [[0, 0, 255], [255, 0, 0], [0, 255, 0]] 
                self.ground_truth_hsv = [[0, 255, 255], [120, 255, 255], [60, 255, 255]]
                break
            
        print(f"{self.id} calibrated colors:")
        print(self.colors)
        print(self.ground_truth_bgr)
        print(self.ground_truth_hsv)

        #     with open(calibFile) as file:
        #         for line in file:
        #             elements = line.strip().split(' ')
        #             color_name = elements[0]
        #             color_bgr  = [int(bias_bgr[0]*int(elements[1])), 
        #                           int(bias_bgr[1]*int(elements[2])), 
        #                           int(bias_bgr[2]*int(elements[3]))]
        #             color_hsv  = bgr_to_hsv(color_bgr)
                    
        #             self.colors.append(color_name)
        #             self.ground_truth_bgr.append(color_bgr)
        #             self.ground_truth_hsv.append(color_hsv)

        # else:
        #     print("color calibration file not found, use hard coded colors")
        #     self.colors = ["red", "blue", "green"]
        #     self.ground_truth_bgr = [[0, 0, 255], [255, 0, 0], [0, 255, 0]] 
        #     self.ground_truth_hsv = [[0, 255, 255], [120, 255, 255], [60, 255, 255]]

        logger.info('Color walk OK')
    
    def random_walk_engine(self, mylambda= 15, turn = 7):
        self.rot.setDrivingMode("pattern")
        if self.rot.duration <= 0:
            if self.actual_rw_dir == "s":
                self.actual_rw_dir = random.choice(["s", "cw", "ccw"])
                time_to_walk = math.ceil(random.uniform(0, 1) * turn)
            else:
                time_to_walk = math.ceil(random.expovariate(1 / mylambda))
                self.actual_rw_dir = "s"
            self.rot.setPattern(self.actual_rw_dir, time_to_walk)

    def discover_color(self, duration = 10):

        if self.rot.duration <= 0:

            color_idx, color_name, color_bgr, _ = self.check_all_color()

            if color_idx != -1 and self.check_free_zone():
                self.rot.setWalk(False)
                return color_idx, color_name, color_bgr
            
            self.random_walk_engine()

        return -1, -1, -1

    def check_all_color(self, max_dist = 200):

        angle = -1
        
        for color_idx, color_name in enumerate(self.colors):

            color_hsv   = self.ground_truth_hsv[color_idx]
            reading     = self.cam.get_reading()
            dist, angle = get_contours(reading, color_hsv, hsv_threshold, name = color_name)

            if angle != -1:
                logger.debug(f"found {color_idx} {color_name} {dist}")
                return color_idx, color_name, reading.color_bgr, angle
            
        return -1, -1, [-1,-1,-1], -1

    def check_free_zone(self):
        readings = self.cam.getNew()
        if readings:
            reading = readings[0]
            if reading.distance>10:
                return True #in free ground
            else:
                    return False
        else:
            return False

    def repeat_sampling(self, color_name, repeat_times = 5):
        # measure_list = []
        # for idx in range(repeat_times):
        #     found_color_idx, found_color_name, found_color_rgb, found_color_center = self.check_all_color()
        #     if color_name == found_color_name:
        #         measure_list.append(found_color_rgb)
        #     if (480 // 2 - found_color_center)>0: #if target on your right
        #         walk_dir = ["cw", "ccw"][idx % 2]
        #     else:
        #         walk_dir = ["ccw", "cw"][idx % 2]
        #     self.rot.setPattern(walk_dir, 1)
        reading = self.cam.get_reading()
        if reading:
            return reading.color_bgr
        else:
            return [-1,-1,-1]

    def check_apriltag(self):
        reading = self.cam.get_reading()

        tag_dt = 0
        tag_id = 0
        if reading:
            tag_dt = reading.distance
            tag_id = reading.util
        return tag_id, tag_dt
        
    def get_closest_color(self, bgr_feature):
        hsv_feature = bgr_to_hsv(bgr_feature)

        closest_color_dist = hue_distance(self.ground_truth_hsv[0][0], hsv_feature[0])
        closest_color = self.colors[0]
        closest_color_idx = 0
        for idx, this_color in enumerate(self.colors):
            if hue_distance(self.ground_truth_hsv[idx][0], hsv_feature[0]) < closest_color_dist:
                closest_color_dist = hue_distance(self.ground_truth_hsv[idx][0], hsv_feature[0])
                closest_color =  this_color
                closest_color_idx = idx
        return closest_color, closest_color_idx
    
    def drive_to_closest_color(self, bgr_feature, duration=30):
        hsv_feature = bgr_to_hsv(bgr_feature)

        closest_color_dist = hue_distance(self.ground_truth_hsv[0][0], hsv_feature[0])
        closest_color_name = self.colors[0]
        closest_color_idx  = 0
        for idx, name in enumerate(self.colors):
            if hue_distance(self.ground_truth_hsv[idx][0], hsv_feature[0]) < closest_color_dist:
                closest_color_dist = hue_distance(self.ground_truth_hsv[idx][0], hsv_feature[0])
                closest_color_name = name
                closest_color_idx  = idx
        isArrived = self.drive_to_color(closest_color_name, duration)
        return isArrived, closest_color_name, closest_color_idx

    def drive_to_color(self, color_name, duration=30):
        if color_name not in self.colors:
            logger.debug("Unknown color")
            return False
        else:
            # logger.debug(f"Driving to color: {color_name}")
            # logger.debug(f"Driving to BGR: {self.ground_truth_bgr[self.colors.index(color_name)]}")
            # logger.debug(f"Driving to HSV: {self.ground_truth_hsv[self.colors.index(color_name)]}")
            hsv_feature = self.ground_truth_hsv[self.colors.index(color_name)]
            is_arrived = self.drive_to_hsv(hsv_feature, duration)
            return is_arrived

    class Drive():
        pid_controller = PID(0.1, 0, 0)
        detect_color = False
        arrived_count = 0
        in_free_zone = 0
        lose_track_count = 0
        last_speed = [0,0]

        timer = Timer()
        arrived = False

    def drive_to_hsv(self, target_hsv, duration=30):

        # for the first time, create a drive object
        if not self.drive:
            self.rot.setWalk(False)
            self.actual_rw_dir = "s"
            self.drive = self.Drive()
            self.drive.timer.set(duration)

        arrived = self.drive.arrived_count >= 2

        # check if the robot is in free zone
        if self.drive.in_free_zone < 3:
            _, tag_dist = self.check_apriltag()
            logger.debug(f"In free zone #{self.drive.in_free_zone} (tag dist={tag_dist})")

            if tag_dist > 0:
                if tag_dist > 100:
                    self.drive.in_free_zone += 1
                else:
                    self.drive.in_free_zone = 0
                    self.random_walk_engine(10, 7)
            else:
                self.random_walk_engine(10, 7)
                self.drive.in_free_zone += 1

        elif not arrived:

            _, tag_dist = self.check_apriltag()
            if tag_dist>0:
                if tag_dist < 50 and self.drive.detect_color:  # see color and white board at once
                    self.rot.setDrivingMode("pattern")
                    self.rot.setWalk(False)
                    self.drive.arrived_count += 1
                else:
                    self.drive.arrived_count = 0

            cam_reading = self.cam.get_reading()
            tracking_color_threshold = hsv_threshold.copy()
            # tracking_color_threshold[0]=20
            dist, cen = get_contours(cam_reading, target_hsv, tracking_color_threshold)

            if cen != -1:
                self.drive.detect_color = True
            else:
                self.drive.detect_color = False

            if self.drive.detect_color:
                self.drive.lose_track_count=0
                self.rot.setDrivingMode("speed")
                error = -cen
                dt = 1  # You can calculate the actual time difference between the frames for a more accurate control
                speed_adjustment = self.drive.pid_controller.compute(error, dt)

                base_speed = self.max_speed*0.8

                left_speed = base_speed + speed_adjustment
                right_speed = base_speed - speed_adjustment
                self.drive.last_speed = [left_speed, right_speed]
                logger.debug(f"speeds: {left_speed},{right_speed} | error: {error} ")
                self.rot.setDrivingSpeed(left_speed, right_speed)
           
            elif self.drive.arrived_count == 0 and self.drive.lose_track_count<5:
                self.drive.lose_track_count+=1
                self.rot.setDrivingSpeed(0.5*self.drive.last_speed[1], 0.5*self.drive.last_speed[0]) #reverse last PID action, try to recover the color
           
            elif self.drive.arrived_count == 0 and self.drive.lose_track_count>=5:
                self.rot.setDrivingMode("pattern")
                self.drive.pid_controller = PID(0.1, 0, 0) #reset controller
                self.random_walk_engine()

        
        if arrived or self.drive.timer.query():
            self.rot.setDrivingMode("pattern")
            self.rot.setWalk(False)
            self.drive = None
            logger.debug(f"Arrived at color: {target_hsv}")
            return arrived
        
    def drive_to_rgb(self, bgr_feature, duration=30):
        hsv_feature = bgr_to_hsv(bgr_feature)
        return self.drive_to_hsv(hsv_feature, duration)
    
    def get_color_list(self):
        return self.colors

    def set_leds(self, state):
        self.rot.setLEDs(state)

    def stop(self):
        self.rot.setWheels(0,0)
        self.rot.setWalk(False)
        #self.gs.stop()

# Some helper functions
def hue_distance(h0, h1):
    h0 = int(h0)
    h1 = int(h1)
    return min(abs(h1 - h0), 180 - abs(h1 - h0)) / 90.0

if __name__ == "__main__":

    cwe = ColorWalkEngine(500)
    
    cwe.check_all_color()
