from erandb import ERANDB
from aux import Logger

class Trajectory(object):
    def __init__(self, robot_id, tracked_robot, start_time, prev_time, waypoints) -> None:
        self.robot_id = robot_id
        self.tracked_robot = tracked_robot
        self.start_time = start_time
        self.prev_time = prev_time
        self.waypoints = [waypoints]

    def add_waypoint(self, waypoint):
        self.waypoints.append(waypoint)

    def update_Prev_Time(self, current_clock):
        self.prev_time = current_clock

    def get_Start_Time(self):
        return self.start_time

    def get_Prev_Time(self):
        return self.prev_time

    def get_Tracked_Robot(self):
        return self.tracked_robot

    def get_waypoints(self):
        return self.waypoints


class RecordedData(object):
    def __init__(self, erb: ERANDB, logger: Logger) -> None:
        self.erb = erb
        self.logger = logger
        self.potential_data = {}#dict.fromkeys([i + 1 for i in range(len(allrobots))])
        self.saved_data = []

    def add_saved_data(self, trajectory: Trajectory):
        self.saved_data.append(trajectory)

    def add_potential_data(self, trajectory: Trajectory):
        self.potential_data[trajectory.tracked_robot] = trajectory

    def send_data(self, line):
        self.logger.log(line)

    def change_log_file(self, file):
        self.logger.change_file(file)

    def get_erb(self):
        return self.erb

    def get_Logger(self):
        return self.logger

    def get_saved_data(self):
        return self.saved_data

    def get_potential_data(self):
        return self.potential_data

    def set_potential_data(self, value, nID):
        self.potential_data[nID] = value

    def set_saved_data(self, value):
        self.saved_data = value

def sortExpiredData(data: list, threshold: int) -> list:
    """
    Splits the list given in argument in 2 lists, the valid and expired one.
    If the time of the first sample of a sequence (remember each sequence is of length 100) is 
    below the threshold time, then the whole 100 samples (or less if it is the end and the whole
    sequence has not been uploaded in the file) are set in the expiredData list.
    args :
        data (list): The data that should be sorted. is of the format [[time (int/float), ...]].
        threshold (int): The threshold after which a data is still valid.
    return :
        list, list :The samples that are expired and the samples that are still valid for training.
    """
    expiredData=[]
    validData=[]
    for i in range(0, len(data), 100):
        if data[i][2]<threshold:
            expiredData.extend(data[i:i+100])
        else:
            validData.extend(data[i:i+100])
    return expiredData, validData

def filterExpiredData(currentFilename: str, expiredFilename: str, threshold: int):
    with open(currentFilename, 'r+') as f:
        next(f)
        myData = []
        for line in f:
            line = line.split(",")
            myData.append([float(elem) for elem in line])
        oldData, notExpiredData = sortExpiredData(myData, threshold)
        f.seek(0)
        header = ['robotID', 'neighborID', 'time', 'x', 'y'] 
        myHeader = ','.join(header)+'\n'
        f.write(myHeader)
        for line in notExpiredData:
            myLine = ','.join([str(elem) for elem in line])+'\n'
            f.write(myLine)
        f.truncate()
    
    with open(expiredFilename, 'a') as o:
        for line in oldData:
            myLine = ','.join([str(elem) for elem in line])+'\n'
            o.write(myLine)
    print("done")