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
from statistics import mean, stdev

# Chart constants
COL_HEIGHT = 20 # height of a chart column
CHART_WIDTH = 100 # width of chart
TERMINAL_WIDTH = 110 # max characters in the terminal

# Define the buffers
# Rolling image hsv
IMAGE_BUFFER = collections.deque([], maxlen=1)

# Rolling distances from nearest ideal colour
DIST_BUFFER = collections.deque([], maxlen=1)

# Chart values
CHART_BUFFER = collections.deque([0]*CHART_WIDTH, maxlen=CHART_WIDTH)
MAX_F = 0

# Current sequence and quality
SEQUENCE_BUFFER = "" # store the sequence of interest
QUALITY_BUFFER = ""
SEQUENCE_NUMBER = 1

# Control whether timer is running
IS_TIMER_RUNNING = False

# Given hsv, transform to a single number that
# is different-ish for each colour and can mimic
# the nanopore wiggle trace
def transform_hsv(h, s, v):
	h = h+1
	s = s+1
	v = v+1
	wiggle = math.log(h*s) + math.log(s*v) + math.log(h*v) * math.log(h*s*v) # pseudo current wiggle value
	return(wiggle - 50) # clip the constant region for more dynamic chart

# Create a string for the current values
def make_info_string(hue, saturation, value, colour_dist, colour_name):
	global MAX_F
	f = transform_hsv(hue, saturation, value) # raw value
	if(f>MAX_F):
		MAX_F = f

	f_length = math.floor((f/150)*COL_HEIGHT) # how many terminal rows chart fills
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
	print("")
	print("\t\t\t\t\tLEGO NANOPORE SEQUENCER")
	print("")
	print("┌" + "─"*CHART_WIDTH + "┐")

	for i in range(1, COL_HEIGHT): # terminal rows in chart
		print("│", end="") # begin line
		for b in CHART_BUFFER: # columns
			s = "█" if b >= COL_HEIGHT-i else " "
			print(s, end="")
		print("│", end="") # end line
		if i == math.floor(COL_HEIGHT / 4):
			print("\tBase: "+base) #+"\t"+"Max F: "+str(MAX_F)
		else:
			print("")

	print("└" + "─"*CHART_WIDTH + "┘")
	print(chart_string.ljust(TERMINAL_WIDTH))

	# Ensure we overwrite any existing info with spaces
	# by ljust
	print("".ljust(TERMINAL_WIDTH))
	capture_string = "Capturing..." if IS_TIMER_RUNNING else "Paused"
	print(f'\t{capture_string}'.ljust(TERMINAL_WIDTH))
	print("\tCurrent sequence:".ljust(TERMINAL_WIDTH))
	print(f'\t@SEQUENCE_{SEQUENCE_NUMBER}'.ljust(TERMINAL_WIDTH))
	print("\t"+SEQUENCE_BUFFER.ljust(TERMINAL_WIDTH))
	print("\t+".ljust(TERMINAL_WIDTH))
	print("\t"+QUALITY_BUFFER.ljust(TERMINAL_WIDTH))
	print("".ljust(TERMINAL_WIDTH))
	print("Controls:\t[s]tart/stop\t[r]eset\t[q]uit".ljust(TERMINAL_WIDTH))



# Timer thread. Every n seconds, get
# the most common base seen recently, clear the 
# image buffer, update the sequence buffer
def run_timer():
	global SEQUENCE_BUFFER
	global QUALITY_BUFFER
	global IMAGE_BUFFER
	global DIST_BUFFER
	clear_buffers()

	while(IS_TIMER_RUNNING):
		time.sleep(0.5)
		if len(IMAGE_BUFFER)==0:
			continue

		a_h = []
		a_s = []
		a_v = []
		for avg_hsv in IMAGE_BUFFER:
			h, s, v = avg_hsv
			a_h.append(h)
			a_s.append(s)
			a_v.append(v)

		m_h = mean(a_h)
		m_s = mean(a_s)
		m_v = mean(a_v)

		base_estimate = estimate_colour(m_h, m_s, m_v)
		colour_name = base_estimate["name"]
		colour_dist = base_estimate["dist"]
		base = BASES[colour_name]


		IMAGE_BUFFER.clear()
		DIST_BUFFER.clear()
		SEQUENCE_BUFFER += base
		QUALITY_BUFFER += dist_to_fastq(colour_dist)

# Clear the buffers ready for a new 
# sequence capture
def clear_buffers():
	global SEQUENCE_BUFFER
	global QUALITY_BUFFER
	global IMAGE_BUFFER
	global DIST_BUFFER
	IMAGE_BUFFER.clear()
	DIST_BUFFER.clear()
	SEQUENCE_BUFFER = ""
	QUALITY_BUFFER = ""


# Clear screen
os.system("clear")
sys.stdout.write("\033[?25l") #  turn off cursor blinking

# Direct errors to log file
original_stderr = sys.stderr
file_err = open('nanopore.log', 'w')
sys.stderr = file_err

# Set up the camera
camera, rawCapture = init_camera()
calibrate_camera(camera, rawCapture)

# Handle user input
def wait_for_user():
	global IS_TIMER_RUNNING
	global file_err
	key = cv2.waitKey(2) & 0xFF

	# if the `q` key was pressed, exit the script
	if key == ord("q"):
		file_err.close()
		cv2.destroyAllWindows()
		sys.exit()

	# If 'r' pressed, reset buffers
	if key == ord("r"):
		global SEQUENCE_NUMBER
		clear_buffers()
		SEQUENCE_NUMBER += 1

	# If 's' pressed, start or stop capture
	if key == ord("s"):
		IS_TIMER_RUNNING = not IS_TIMER_RUNNING
		if IS_TIMER_RUNNING:
			timer_thread = threading.Thread(target=run_timer)
			timer_thread.start()
	

# capture frames from the camera
def run_camera():
	for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):

		center_rect = get_centre_rectangle(frame)

		avg_hsv = get_mean_hsv(center_rect)

		hue, saturation, value = avg_hsv

		# Estimate colour
		colour_estimate = estimate_colour(hue, saturation, value)

		colour_name = colour_estimate["name"]
		colour_dist = colour_estimate["dist"]
		# Get base
		base = BASES[colour_name]
		if(base!="N"): # ignore poor base calls for now
			IMAGE_BUFFER.append(avg_hsv)
			DIST_BUFFER.append(colour_dist)

		chart_string = make_info_string(hue, saturation, value, colour_dist, colour_name)

		# Update chart
		update_display(base, chart_string)

		# show the image frame
		cv2.imshow("Frame", center_rect)

		rawCapture.truncate(0)

		wait_for_user()


# Create a thread that continuously polls the camera and 
# adds the image values to a rolling buffer. Also updates
# the display
cam_thread = threading.Thread(target=run_camera)
cam_thread.start()


