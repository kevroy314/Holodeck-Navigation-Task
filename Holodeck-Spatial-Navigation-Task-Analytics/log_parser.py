import datetime
import logging

import pytz
from tzlocal import get_localzone
import numpy as np
import copy


# This helper function extracts the meta-data from the filename
# Ex: RawLog_Sub999_Trial1_19_22_02_10-04-2017.csv
def get_filename_meta_data(fn, path):
    parts = fn.split('_')
    file_type = parts[0]
    sub_id = parts[1].replace('Sub', '').replace('sub', '')
    trial_num = int(parts[2].replace('Trial', '').replace('trial', ''))
    date_time_string = '_'.join(parts[3:]).replace('.csv', '')
    dt = datetime.datetime.strptime(date_time_string, '%H_%M_%S_%d-%m-%Y')
    phase = 'unknown'
    if 'Practice' in path:
        phase = 'practice'
    elif 'Study' in path:
        phase = 'study'
    elif 'Test' in path:
        phase = 'test'
    return {"fileType": file_type, "subID": sub_id, "trial": trial_num, "phase": phase, "datetime": dt}


# From http://stackoverflow.com/questions/15919598/serialize-datetime-as-binary
# This function is used in reading the binary files to parse the binary .NET DateTime into a Python datetime
def datetime_from_dot_net_binary(data):
    kind = (data % 2 ** 64) >> 62  # This says about UTC and stuff...
    ticks = data & 0x3FFFFFFFFFFFFFFF
    seconds = ticks / 10000000
    tz = pytz.utc
    if kind == 0:
        tz = get_localzone()
    return datetime.datetime(1, 1, 1, tzinfo=tz) + datetime.timedelta(seconds=seconds)


def get_object_info_from_string(info_string):
    vals = info_string.split(':')[1].split(',')
    pos = (float(vals[0].strip()), float(vals[1].strip()), float(vals[2].strip()))
    rot = (float(vals[3].strip()), float(vals[4].strip()), float(vals[5].strip()), float(vals[6].strip()))
    sca = (float(vals[7].strip()), float(vals[8].strip()), float(vals[9].strip()))
    return pos, rot, sca


def get_object_info_from_summary_string(summary_info_string):
    split_line = summary_info_string.split(':')
    name = split_line[0].split(',')[1]
    pos_list = split_line[1].replace('(', '').replace(')', '').split(',')
    pos = (float(pos_list[0]), float(pos_list[1]), float(pos_list[2]))
    return name, pos


def read_summary_file(path):
    events = []
    with open(path, 'rb') as f:
        f.readline()  # Remove header
        file_string = f.readlines()
    current_dt = None
    for line in file_string:
        if line[0] == '-':
            current_dt = datetime_from_dot_net_binary(int(line.replace(',', '').strip()))
        if line.startswith("ChangeTextureEvent_ObjectClicked"):
            events.append({'time': current_dt, 'eventType': 'clicked', 'objectName': line.split(',')[1].strip()})
        if line.startswith("Object_Placed"):
            name, pos = get_object_info_from_summary_string(line)
            events.append({'time': current_dt, 'eventType': 'placed', 'objectName': name, "location": pos})
        if line.startswith("Object_Picked_Up"):
            name, pos = get_object_info_from_summary_string(line)
            events.append({'time': current_dt, 'eventType': 'picked', 'objectName': name, "location": pos})
        if line.startswith("Object_Identity_Set"):
            name, pos = get_object_info_from_summary_string(line)
            events.append({'time': current_dt, 'eventType': 'identified', 'objectName': name, "location": pos})
        if line.startswith("Object_Identity_Removed"):
            name, pos = get_object_info_from_summary_string(line)
            events.append({'time': current_dt, 'eventType': 'deidentified', 'objectName': name, "location": pos})
    return events


def read_raw_file(path):
    iterations = []
    with open(path, 'rb') as f:
        file_string = f.readlines()
    current_dt = None
    current_state = {"Main Camera": None, "First Person Controller": None}
    events = []
    for line in file_string:
        if line[0] == '-':
            if current_dt is not None:
                iterations.append({"time": current_dt, "state": current_state})
                current_state = copy.deepcopy(current_state)
            current_dt = datetime_from_dot_net_binary(int(line.strip()))
        if line.startswith('Main Camera'):
            pos, rot, sca = get_object_info_from_string(line.strip())
            current_state["Main Camera"] = {"position": pos, "rotation": rot, "scale": sca}
        if line.startswith('First Person Controller'):
            pos, rot, sca = get_object_info_from_string(line.strip())
            current_state["First Person Controller"] = {"position": pos, "rotation": rot, "scale": sca}
        if line.startswith("ChangeTextureEvent_ObjectClicked"):
            events.append({'time': current_dt, 'eventType': 'clicked', 'objectName': line.split(',')[1].strip()})
        if line.strip() == 'End of File':
            logging.debug('End of File')
    return iterations, events


def get_simple_path_from_raw_iterations(raw_iterations, make_2d=True):
    points = []
    for i in raw_iterations:
        p = i['state']['First Person Controller']['position']
        if make_2d:
            points.append((p[0], p[2]))
        else:
            points.append(p)
    return np.array(points)


def quat2euler(q):
    roll = np.arctan2(2*(q[1]*q[3] + q[0]*q[2]), 1-2*(q[1]*q[1]+q[2]*q[2]))
    yaw = np.arcsin(2*(q[0]*q[1]-q[2]*q[3]))
    pitch = np.arctan2(2*(q[0]*q[3]+q[1]*q[2]), 1-2*(q[0]*q[0]+q[2]*q[2]))
    return roll, pitch, yaw


def get_simple_orientation_path_from_raw_iterations(raw_iterations):
    angles = []
    for i in raw_iterations:
        p = i['state']['First Person Controller']['rotation']
        x, y, z = quat2euler(p)
        angles.append(np.pi - x - np.pi/2.)
    return angles


def compress(pos, orient):
    new_pos = [pos[0]]
    new_orient = [orient[0]]
    for p, o in zip(pos, orient)[1:]:
        # noinspection PyTypeChecker
        if all(new_pos[-1] == p) and new_orient[-1] == o:
            continue
        else:
            new_pos.append(p)
            new_orient.append(o)
    return np.array(new_pos), new_orient


def get_final_state_from_summary_events():  # summary_events):
    raise NotImplemented


def validate_summary_events_are_complete():  # summary_events):
    raise NotImplemented


def compare_summary_and_raw_events():  # raw_events, summary_events):
    raise NotImplemented
