# common functions
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
from statistics import mean 

# Camera constants
CAMERA_FPS = 10
IMAGE_WIDTH = 640
IMAGE_HEIGHT = 480
CENTER_RECT_SIZE = 50
CENTER_RECT_HALF = CENTER_RECT_SIZE // 2

# Define the ideal HSV levels for each colour
# TODO - calibrate on startup
COLOURS = {
	"red":[170, 250, 250], 
	"yellow":[30, 90, 250], 
	"blue":[100, 250, 250], 
	"grey":[115, 15, 160]
}

# Map colour to DNA bases
BASES = {"red":"A", "blue":"C", "yellow":"G", "grey":"T", "?":"N"}


# Define pseudo-FASTQ levels. The canonical scale is:
# !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~
def dist_to_fastq(dist):
	if dist < 5:
		return("8")
	if dist < 10:
		return("6")
	if dist < 20:
		return("4")
	if dist < 30: 
		return("2")
	if dist < 40:
		return(".")
	return("!")

# Estimate colour names from HSV distance to ideal
# Returns the colour and the distance from the ideal colour
def estimate_colour(hue, saturation, value):
	colour_name = "?"

	# given a colour, calculate the distance from the current values
	def calc_distance(colour):
		return(abs(hue-colour[0])+abs(saturation-colour[1])+abs(value-colour[2]))

	dd = 1e3
	threshold = 60

	for colour in COLOURS:
		d = calc_distance(COLOURS[colour])
		dd = d if d<dd else dd
		colour_name = colour if d<threshold else colour_name

	return({"name":colour_name, "dist":dd})


# initialize the camera and grab a reference to the raw camera capture
def init_camera():
	camera = PiCamera()
	camera.resolution = (IMAGE_WIDTH, IMAGE_HEIGHT)
	camera.framerate = CAMERA_FPS
	rawCapture = PiRGBArray(camera, size=(IMAGE_WIDTH, IMAGE_HEIGHT))
	
	# allow the camera to warmup
	time.sleep(1)
	return camera, rawCapture


def get_centre_rectangle(frame):
	# grab the raw NumPy array representing the image
	image = frame.array

	# Crop the center rectangle
	center_x = IMAGE_WIDTH // 2
	center_y = IMAGE_HEIGHT // 2
	center_rect = image[center_y - CENTER_RECT_HALF:center_y + CENTER_RECT_HALF,
						center_x - CENTER_RECT_HALF:center_x + CENTER_RECT_HALF]
	return(center_rect)

def get_mean_hsv(center_rect):
	# Convert to HSV for processing
	center_rect_hsv = cv2.cvtColor(center_rect, cv2.COLOR_BGR2HSV)
	avg_hsv = np.mean(center_rect_hsv, axis=(0, 1))
	return(avg_hsv)

# Play the video until 'n' is pressed
def play_camera_video(camera, rawCapture):
	for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
		center_rect = get_centre_rectangle(frame)
		cv2.imshow("Frame", center_rect)
		rawCapture.truncate(0)
		key = cv2.waitKey(2) & 0xFF
		if key == ord('n'):
			return()


# Get a reading of the HSV values for each brick to
# protect against lighting changes
def calibrate_camera(camera, rawCapture):
	global COLOURS
	print("Calibrating...")

	def calibrate_colour(colour):
		print(f'Show me a {colour} and press n')
		play_camera_video(camera, rawCapture)

		camera.capture(rawCapture, format="bgr", use_video_port=True)
		center_rect = get_centre_rectangle(rawCapture)
		avg_hsv = get_mean_hsv(center_rect)
		cv2.imshow("Frame", center_rect)
		COLOURS[colour] = avg_hsv
		rawCapture.truncate(0)
		print(COLOURS[colour])

	for col in COLOURS:
		calibrate_colour(col)

	print("Calibration complete!")
	time.sleep(1)
	os.system("clear")
