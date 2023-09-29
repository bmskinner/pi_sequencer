# Illumina style sequencing
import os
from picamera.array import PiRGBArray
from picamera import PiCamera
import collections
import numpy as np
import time
import cv2
import math
import sys
from sequencing import *

# constants
LEFT_PANEL_WIDTH = 90

# Global variables for sequencing
fasta = ""
fastq = ""
sequence_number = 1

sequence_history = collections.deque([], maxlen=10)

# Blast a given sequence
def blast(dna):
	print("Searching for matching DNA...")
	time.sleep(1)
	if len(dna)<10:
		print("Sequence is too short!")
		return
	print("Found matching species: MALLARD DUCK")

def wait_for_user(base, qual):
	global fasta
	global fastq
	key = cv2.waitKey(-1) & 0xFF
	# if the `q` key was pressed, exit the script
	if key == ord("q"):
		cv2.destroyAllWindows()
		sys.exit()
	if key == ord("r"):
		global sequence_number
		global sequence_history
		sequence_history.append(fasta)
		fasta = ""
		fastq = ""
		sequence_number+=1

	if(key == ord("c")):
		fasta += base
		fastq += qual

	if key == ord('b'):
		blast(fasta)
		wait_for_user(base, qual)


def make_sequence_history_line(index):
	seq_num = index if len(sequence_history)<10 else sequence_number-(10-index)
	seq_line = sequence_history[index] if len(sequence_history)>index else ""
	return(f'{seq_num}:'.ljust(6)+seq_line.ljust(20) )

# right pad a line of text for display
def make_display_line(text):
	return(text.ljust(LEFT_PANEL_WIDTH))

def update_display():
	print("\033[1;1H") # move cursor to top left
	print(make_display_line(""))
	print(make_display_line("\t\t\t\t\tLEGO ILLUMINA SEQUENCER"))
	print(make_display_line(""))
	print(make_display_line(f'Measured colour: {colour_name}'))
	print(make_display_line(f'Detected base  : {base}'))
	print(make_display_line(""))
	print(make_display_line("Sequence so far:"))
	print(make_display_line(""))
	print(make_display_line(f'@SEQUENCE_{sequence_number}'))
	print(make_display_line(fasta))
	print(make_display_line("+"))
	print(make_display_line(fastq))
	print(make_display_line(""))
	print(make_display_line("Press 'c' to capture this base, 'n' to take a new image, 'r' to reset, or 'b' to BLAST"))
	print(make_display_line(""))
	print(make_display_line(""))
	print(make_display_line("Sequence history:"))
	for i in range(0, 9):
		print(make_sequence_history_line(i))
	print(make_display_line(""))
	print(make_display_line(""))


# initialize the camera and grab a reference to the raw camera capture
camera, rawCapture = init_camera()

calibrate_camera(camera, rawCapture)

os.system("clear")

while(True):

	# Snap an image
	camera.capture(rawCapture, format="bgr", use_video_port=True)

	center_rect = get_centre_rectangle(rawCapture)

	avg_hsv = get_mean_hsv(center_rect)
	hue, saturation, value = avg_hsv

	# Estimate colour
	colour_estimate = estimate_colour(hue, saturation, value)
	colour_name = colour_estimate["name"]
	colour_dist = colour_estimate["dist"]

	# Get base and quality
	base = BASES[colour_name]
	qual = dist_to_fastq(colour_dist)

	# show the image frame
	cv2.imshow("Frame", center_rect)

	# clear the stream in preparation for the next frame
	rawCapture.truncate(0)

	# Update display
	update_display()

	# wait for key press - do we add this base to the sequence?
	wait_for_user(base, qual)
