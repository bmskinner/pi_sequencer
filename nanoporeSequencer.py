# Camera reading without matplotlib
# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import collections
import numpy as np
import os
import time
import cv2
import math
import sys

# constants
CAMERA_FPS = 10
IMAGE_WIDTH = 640
IMAGE_HEIGHT = 480
CENTER_RECT_SIZE = 50
CENTER_RECT_HALF = CENTER_RECT_SIZE // 2
COL_HEIGHT = 20 # height of a chart column
CHART_WIDTH = 100 # width of chart

# Define the ideal HSV levels for each colour
RED = [170, 250, 250]
YELLOW = [30, 90, 250]
BLUE = [100, 250, 250]
BLACK = [128, 70, 40]
COLOURS = {"red":RED, "yellow":YELLOW, "blue":BLUE, "black":BLACK}

# Map colour to DNA base
BASES = {"red":"A", "blue":"T", "yellow":"C", "black":"G", "?":"N"}

# Define the chart buffer
CHART_BUFFER = collections.deque([0]*CHART_WIDTH, maxlen=CHART_WIDTH)
SEQUENCE_BUFFER = "" # store the sequence of interest

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (IMAGE_WIDTH, IMAGE_HEIGHT)
camera.framerate = CAMERA_FPS
rawCapture = PiRGBArray(camera, size=(IMAGE_WIDTH, IMAGE_HEIGHT))

# allow the camera to warmup
time.sleep(1)

# Given hsv, transform to a single number that
# is different-ish for each colour and can mimic
# the nanopore wiggle trace
def transform_hsv(h, s, v):
	h = h+1
	s = s+1
	v = v+1
	return(math.log(h*s) + math.log(s*v) + math.log(h*v) * math.log(h*s*v))

# Create a string for the current values
def make_display_string(hue, saturation, value):
	f = transform_hsv(hue, saturation, value)
	f_length = math.floor((f/255)*COL_HEIGHT)
	CHART_BUFFER.append(f_length)
	return("Current: "+"{:5.0f}".format(f)+
		"\tHue: "+"{:5.0f}".format(hue)+
		"\tSat: "+"{:5.0f}".format(saturation)+
		"\tVal: "+ "{:5.0f}".format(value))

# Estimate colour names from HSV distance to ideal
def estimate_colour(hue, saturation, value):
	colour_name = "?"

	# given a colour, calculate the distance from the current values
	def calc_distance(colour):
		return(abs(hue-colour[0])+abs(saturation-colour[1])+abs(value-colour[2]))

	dd = 1e4
	threshold = 40

	for colour in COLOURS:
		d = calc_distance(COLOURS[colour])
		dd = d if d<threshold else dd
		colour_name = colour if d<threshold else colour_name

	return({"name":colour_name, "dist":dd})

# Draw the current chart buffer
def update_chart(base):
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
	
# Clear screen
os.system("clear")

# capture frames from the camera
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


	# Update chart
	update_chart(base)
	chart_string = make_display_string(hue, saturation, value)
	print(chart_string, "\tDist: ","{:5.1f}".format(colour_dist), 
		"\tCol: ", colour_name.ljust(7))

	# show the image frame
	cv2.imshow("Frame", center_rect)

	key = cv2.waitKey(1) & 0xFF
	
	# clear the stream in preparation for the next frame
	rawCapture.truncate(0)

	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break