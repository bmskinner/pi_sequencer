# Camera reading without matplotlib
# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import threading
import collections
import queue
import numpy as np
import os
import time
import cv2
import math
import sys
from sequencing import *

# constants
COL_HEIGHT = 20 # height of a chart column
CHART_WIDTH = 100 # width of chart

# Define the buffers
IMAGE_BUFFER = collections.deque([], maxlen=8)
CHART_BUFFER = collections.deque([0]*CHART_WIDTH, maxlen=CHART_WIDTH)
SEQUENCE_BUFFER = collections.deque([]) # store the sequence of interest



# find the most common element of a collection
def most_common(lst):
    data = collections.Counter(lst)
    return data.most_common(1)[0][0]

# Given hsv, transform to a single number that
# is different-ish for each colour and can mimic
# the nanopore wiggle trace
def transform_hsv(h, s, v):
	h = h+1
	s = s+1
	v = v+1
	return(math.log(h*s) + math.log(s*v) + math.log(h*v) * math.log(h*s*v))

# Create a string for the current values
def make_display_string(hue, saturation, value, colour_dist, colour_name):
	f = transform_hsv(hue, saturation, value)
	f_length = math.floor((f/255)*COL_HEIGHT)
	CHART_BUFFER.append(f_length)
	return("Current: "+"{:5.0f}".format(f)+
		"\tHue: "+"{:5.0f}".format(hue)+
		"\tSat: "+"{:5.0f}".format(saturation)+
		"\tVal: "+ "{:5.0f}".format(value)+
		"\tDist: "+"{:5.1f}".format(colour_dist)+
		"\tCol: "+colour_name.ljust(7))

# Draw the current chart buffer
def update_display(base, chart_string):
	print("\033[1;1H") # move cursor to top left
	print("┌" + "─"*CHART_WIDTH + "┐")

	for i in range(1, COL_HEIGHT): # rows
		print("│", end="") # begin line
		for b in CHART_BUFFER: # columns
			s = "█" if b >= COL_HEIGHT-i else " "
			print(s, end="")
		print("│", end="") # end line
		if i == math.floor(COL_HEIGHT / 4):
			print("\tBase: "+base)
		else:
			print("")

	print("└" + "─"*CHART_WIDTH + "┘")
	print(chart_string)
	print("")
	print("".join(SEQUENCE_BUFFER))
	
# Clear screen
os.system("clear")

camera, rawCapture = init_camera()

# capture frames from the camera
def run_camera():
	for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
		# grab the raw NumPy array representing the image
		image = frame.array

		# Crop the center rectangle
		center_x = IMAGE_WIDTH // 2
		center_y = IMAGE_HEIGHT // 2
		center_rect = image[center_y - CENTER_RECT_HALF:center_y + CENTER_RECT_HALF,
							center_x - CENTER_RECT_HALF:center_x + CENTER_RECT_HALF]


		# Convert to HSV for processing
		center_rect_hsv = cv2.cvtColor(center_rect, cv2.COLOR_BGR2HSV)
		
		# Calculate the mean HSV values
		avg_hsv = np.mean(center_rect_hsv, axis=(0, 1))
		hue, saturation, value = avg_hsv

		# Estimate colour
		colour_estimate = estimate_colour(hue, saturation, value)

		colour_name = colour_estimate["name"]
		colour_dist = colour_estimate["dist"]
		# Get base
		base = BASES[colour_name]

		IMAGE_BUFFER.append(base)

		chart_string = make_display_string(hue, saturation, value, colour_dist, colour_name)

		# Update chart
		update_display(base, chart_string)

		# show the image frame
		cv2.imshow("Frame", center_rect)

		key = cv2.waitKey(1) & 0xFF
		
		# clear the stream in preparation for the next frame
		rawCapture.truncate(0)

		# if the `q` key was pressed, break from the loop
		if key == ord("q"):
			break

# Timer thread. Every n seconds, get
# the most common base seen recently, clear the 
# image buffer, update the sequence buffer
def run_timer():
	while(True):
		time.sleep(1)
		if len(IMAGE_BUFFER)>0:
			base = most_common(IMAGE_BUFFER)
			IMAGE_BUFFER.clear()
			global SEQUENCE_BUFFER
			SEQUENCE_BUFFER.append(base)

# Create a thread that continuously polls the camera and 
# adds the found base to a rolling buffer and updates the chart
cam_thread = threading.Thread(target=run_camera)
cam_thread.start()

timer_thread = threading.Thread(target=run_timer)
timer_thread.start()