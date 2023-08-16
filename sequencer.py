# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import numpy as np
import matplotlib.pyplot as plt
import time
import cv2

# constants
IMAGE_WIDTH = 640
IMAGE_HEIGHT = 480
CENTER_RECT_SIZE = 100
CENTER_RECT_HALF = CENTER_RECT_SIZE // 2

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (IMAGE_WIDTH, IMAGE_HEIGHT)
camera.framerate = 2
rawCapture = PiRGBArray(camera, size=(IMAGE_WIDTH, IMAGE_HEIGHT))

# allow the camera to warmup
time.sleep(0.1)

# Given an image frame from the camera, detect hue and display
def process_camera_image(frame):
	# grab the raw NumPy array representing the image
	image = frame.array

	#image = image.reshape((IMAGE_HEIGHT, IMAGE_WIDTH, 3))

	# Crop the center rectangle
	center_x = IMAGE_WIDTH // 2
	center_y = IMAGE_HEIGHT // 2
	center_rect = image[center_y - CENTER_RECT_HALF:center_y + CENTER_RECT_HALF,
						center_x - CENTER_RECT_HALF:center_x + CENTER_RECT_HALF]


	# Convert to HSV for processing
	center_rect_hsv = cv2.cvtColor(center_rect, cv2.COLOR_BGR2HSV)
	
	# Calculate the average HSV values
	avg_hsv = np.mean(center_rect_hsv, axis=(0, 1))
	hue, saturation, value = avg_hsv
	
	print(f"Average HSV color: Hue = {hue:.2f}, Saturation = {saturation:.2f}, Value = {value:.2f}")

	# show the frame
	cv2.imshow("Frame", center_rect)
	return hue

# capture frames from the camera
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
	# grab the raw NumPy array representing the image
	# image = frame.array
	process_camera_image(frame)

	key = cv2.waitKey(1) & 0xFF
	
	# clear the stream in preparation for the next frame
	rawCapture.truncate(0)

	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break
