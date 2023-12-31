# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
from datetime import datetime
import collections
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as anim
import time
import cv2

# constants
MAX_X_POINTS = 20
UPDATE_INTERVAL_MS = 50
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

	# Crop the center rectangle
	center_x = IMAGE_WIDTH // 2
	center_y = IMAGE_HEIGHT // 2
	center_rect = image[center_y - CENTER_RECT_HALF:center_y + CENTER_RECT_HALF,
						center_x - CENTER_RECT_HALF:center_x + CENTER_RECT_HALF]


	# Convert to HSV for processing
	center_rect_hsv = cv2.cvtColor(center_rect, cv2.COLOR_BGR2HSV)
	
	# Calculate the average HSV values
	avg_hsv = np.mean(center_rect_hsv, axis=(0, 1))

	rawCapture.truncate(0)

	# show the frame
	# cv2.imshow("Frame", center_rect)
	return avg_hsv

# capture frames from the camera
def animate(i):

	# capture camera image
	camera.capture(rawCapture, format="bgr", use_video_port=True)

	# grab the raw NumPy array representing the image
	# image = frame.array	
	avg_hsv = process_camera_image(rawCapture)

	hue, saturation, value = avg_hsv

	data.append((datetime.now(), hue))
	print(f"Average HSV color: Hue = {hue:.2f}, Saturation = {saturation:.2f}, Value = {value:.2f}")

	ax.set_xlim(data[0][0], data[-1][0])
	line.set_data(*zip(*data))
	# clear the stream in preparation for the next frame


# Create the empty figure
fig, ax = plt.subplots()
ax.set_ylim(0, 360)
x = datetime.now()
y = 0
data = collections.deque([(x, y)], maxlen=MAX_X_POINTS)
line, = plt.plot(*zip(*data), c='black')

ani = anim.FuncAnimation(fig, animate, interval=UPDATE_INTERVAL_MS)
plt.show()

