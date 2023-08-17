# Illumina style sequencing
import os
from picamera.array import PiRGBArray
from picamera import PiCamera
import collections
import numpy as np
import time
import cv2
import math

# constants
CAMERA_FPS = 10
IMAGE_WIDTH = 640
IMAGE_HEIGHT = 480
CENTER_RECT_SIZE = 50
CENTER_RECT_HALF = CENTER_RECT_SIZE // 2

# Convert colour into DNA base
BASES = {"red":"A", "blue":"T", "yellow":"C", "black":"G", "?":"N"}
QUALITIES = {"!":"Could not identify base", "~":"Very confident"}

# Global variables for sequencing
fasta = ""
fastq = ""
sequence_number = 1

# Blast a given sequence
def blast(dna):
	print("Searching for matching DNA...")
	time.sleep(1)
	if len(dna)<10:
		print("Sequence is too short!")
		return
	print("Found matching species: MALLARD DUCK")

# Estimate the colour under the sensor
def estimate_colour(hue, saturation, value):
	colour_name = "?"
	colour_name = "red" if hue > 150 and saturation > 200 else colour_name
	colour_name = "blue" if hue < 150 and saturation > 120 and value < 128 else colour_name
	colour_name = "yellow" if hue < 80 and saturation > 200 else colour_name
	colour_name = "black" if hue < 50 and saturation > 128 and value < 80 else colour_name
	return(colour_name)

def wait_for_user():
	key = cv2.waitKey(-1) & 0xFF
	# if the `q` key was pressed, exit the script
	if key == ord("q"):
		exit()
	if key == ord("r"):
		fasta = ""
		fastq = ""
		sequence_number+=1
		os.system("clear")
		print("Resetting sequencer")

	if key == ord('b'):
		blast(fasta)
		wait_for_user()



# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (IMAGE_WIDTH, IMAGE_HEIGHT)
camera.framerate = CAMERA_FPS
rawCapture = PiRGBArray(camera, size=(IMAGE_WIDTH, IMAGE_HEIGHT))

# allow the camera to warmup
time.sleep(1)

while(True):

	# Snap an image
	camera.capture(rawCapture, format="bgr", use_video_port=True)

	# grab the raw NumPy array representing the image
	image = rawCapture.array

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

	sd_hsv = np.std(center_rect_hsv, axis=(0, 1))
	hue_sd, sat_sd, val_sd = sd_hsv

	# Estimate colour
	colour_name = estimate_colour(hue, saturation, value)

	# Get base
	base = BASES[colour_name]
	qual = "!" if base=="N" else "~"

	fasta += base
	fastq += qual

	# Update display
	os.system("clear")
	print("Measured colour: ", colour_name)
	print("Detected base  : ", base)
	print("Base quality   : ", qual, "(", QUALITIES[qual], ")")
	print("")
	print("Sequence so far:")
	print("")
	print("@SEQUENCE_"+f'{sequence_number}')
	print(fasta)
	print("+")
	print(fastq)
	print("")
	print("Add new base to DNA and press 'n' to capture, 'r' to reset, or 'b' to BLAST")

	# show the image frame
	cv2.imshow("Frame", center_rect)

	# clear the stream in preparation for the next frame
	rawCapture.truncate(0)

	# wait for key press
	wait_for_user()
