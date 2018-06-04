import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scipy.misc import imread
import log_parser as parser
import os


def get_direction_patch_location(center, radius, angle):
    return center[0] + radius * np.cos(angle), center[1] + radius * np.sin(angle)


def update_line(num, pos, orient, line, r):
    pos_data = pos[..., num]
    ori_data = orient[num]
    avatar.center = pos_data
    avatar_direction_marker.center = get_direction_patch_location(pos_data, r, ori_data)
    fig.canvas.draw()
    line.set_data(pos[..., :num])
    return line,

# Set Properties
avatar_size = 1
direction_marker_propotion_size = 0.25
padding_size = 0.3
frame_interval_ms = 0
bounds = (-20, 20, -40, 40)

# Set data
directory = r'Z:\Kelsey\2017 Summer RetLu\Virtual_Navigation_Task\v5_2\NavigationTask_Data\Logged_Data\2RoomTestAnonymous\124\\'
raw_filepath = directory + 'RawLog_Sub124_Trial1_13_15_57_30-05-2017.csv'
summary_filepath = directory + 'SummaryLog_Sub124_Trial1_13_15_57_30-05-2017.csv'
print parser.get_filename_meta_data(os.path.basename(raw_filepath), os.path.abspath(raw_filepath))

raw_iterations, raw_events = parser.read_raw_file(raw_filepath)
summary_events = parser.read_summary_file(summary_filepath)
position_data = parser.get_simple_path_from_raw_iterations(raw_iterations)
orientation_data = parser.get_simple_orientation_path_from_raw_iterations(raw_iterations)
position_data, orientation_data = parser.compress(position_data, orientation_data)
position_data = np.transpose(position_data)
orientation_data = np.transpose(orientation_data)
data_length = len(raw_iterations)

# Set up figure
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)

# Set up markers and lines
l, = plt.plot([], [], 'r-')
avatar = plt.Circle((0, 0), avatar_size, fc='y')
avatar_direction_marker_true_size = direction_marker_propotion_size * avatar_size
r_adj = avatar_size - avatar_direction_marker_true_size
avatar_direction_marker = plt.Circle((0, 0), avatar_direction_marker_true_size, fc='b')
ax.add_patch(avatar)
ax.add_patch(avatar_direction_marker)

for event in summary_events:
    col = 'k'
    if event['eventType'] == 'placed':
        col = 'b'
    elif event['eventType'] == 'picked':
        col = 'r'
    elif event['eventType'] == 'identified':
        col = 'y'
    elif event['eventType'] == 'deidentified':
        col = 'g'
    try:
        ax.add_patch(plt.Circle((event['location'][0], event['location'][2]), 1, fc=col, alpha=0.25, label=event['objectName']))
    except KeyError:
        continue
# Set up plot bounds
# bounds = (min(position_data[0, ...]), max(position_data[0, ...]),
#           min(position_data[1, ...]), max(position_data[1, ...]))
padded_bounds = np.array(bounds) * (padding_size + 1.)
print bounds
plt.xlim(padded_bounds[0], padded_bounds[1])
plt.ylim(padded_bounds[2], padded_bounds[3])

# Set up plot labels
plt.title('Holodeck Spatial Navigation Animation')

# Animate Line
line_ani = animation.FuncAnimation(fig, update_line, data_length, fargs=(position_data, orientation_data, l, r_adj),
                                   interval=frame_interval_ms, blit=True)

# Show Background Image
img = imread('background.png')
plt.imshow(img, zorder=0, extent=bounds)

plt.show()
