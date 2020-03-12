#!/usr/bin/python3

from math import pow, sin, pi
from dual_g2_hpmd_rpi import motors, MAX_SPEED
import signal
import os
import random
import time

# TEST CODE

fps = 120.0
frameCount = 0
period=[10,7.5]
peakSpeed=100

#------------------------------------------------------------------------
#	verbose or debug mode

def debug(message):
	if verbose:
		print(message)

#------------------------------------------------------------------------
#

def setup():
	motors.enable()
	motors.setSpeed( 0, 0 )

#------------------------------------------------------------------------
# shutdown procedure

def shutdown(signal, frame):
	motors.setSpeed( 0, 0 )
	motors.disable()
	os._exit(0)

#------------------------------------------------------------------------
# main()

def main():
	global frameCount
	while True:
		frameCount
		speed1=peakSpeed*sin(2*pi*frameCount/(fps * period[0]))
		speed2=peakSpeed*sin(2*pi*frameCount/(fps * period[1]))
		motors.setSpeed(speed1,speed2)	
		time.sleep(1/fps)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGHUP, shutdown)

setup()
main()