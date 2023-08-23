# common functions
from picamera.array import PiRGBArray
from picamera import PiCamera
import collections
import math
import time

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

# Map colour to DNA base
BASES = {"red":"A", "blue":"C", "yellow":"T", "grey":"G", "?":"N"}


# !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~
def dist_to_fastq(dist):
	if dist < 5:
		return("~")
	if dist < 10:
		return("u")
	if dist < 20:
		return("^")
	if dist < 30: 
		return("9")
	if dist < 40:
		return("*")
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