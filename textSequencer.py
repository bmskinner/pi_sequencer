# Camera reading without matplotlib
# import the necessary packages
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
COL_WIDTH = 50 # width of chart column
DISPLAY_WIDTH = 55 # width of chart column plus trimmings

# Convert colour into DNA base
BASES = {"red":"A", "blue":"T", "yellow":"C", "black":"G", "?":"N"}

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (IMAGE_WIDTH, IMAGE_HEIGHT)
camera.framerate = CAMERA_FPS
rawCapture = PiRGBArray(camera, size=(IMAGE_WIDTH, IMAGE_HEIGHT))

# allow the camera to warmup
time.sleep(1)

# Create a text chart element
def make_col_string(val, width, total_width):
	s = "|" + f'{int(val)}'.rjust(3) + " "
	for i in range(1, width):
		s += "█"
	return(s.ljust(DISPLAY_WIDTH))

# Create a string for the current values
def make_display_string(hue, saturation, value):
	h_length =  math.floor(((hue/180)*COL_WIDTH))
	s_length =  math.floor(((saturation/255)*COL_WIDTH))
	v_length =  math.floor(((value/255)*COL_WIDTH))
	h_string = make_col_string( hue, h_length, COL_WIDTH ) 
	s_string = make_col_string(saturation, s_length, COL_WIDTH ) 
	v_string = make_col_string(value, v_length, COL_WIDTH ) 
	return("Hue: "+h_string+"Sat: "+s_string+"Val: "+ v_string)

# Lookup colour names from HSV
def estimate_colour(hue, saturation, value):
	colour_name = "?"
	colour_name = "red" if hue > 150 and saturation > 200 else colour_name
	colour_name = "blue" if hue < 150 and saturation > 120 and value < 128 else colour_name
	colour_name = "yellow" if hue < 80 and saturation > 200 else colour_name
	colour_name = "black" if hue < 50 and saturation > 128 and value < 80 else colour_name
	return(colour_name)




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
	colour_name = estimate_colour(hue, saturation, value)

	# Get base
	base = BASES[colour_name]

	# Update chart
	chart_string = make_display_string(hue, saturation, value)
	print(chart_string, "Col: ", colour_name.ljust(7), "Base:", base)

	# show the image frame
	cv2.imshow("Frame", center_rect)

	key = cv2.waitKey(1) & 0xFF
	
	# clear the stream in preparation for the next frame
	rawCapture.truncate(0)

	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break