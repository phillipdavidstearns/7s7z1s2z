#!/usr/bin/python3

from math import pow, sin, pi
from dual_g2_hpmd_rpi import motors, MAX_SPEED
import RPi.GPIO as GPIO
import signal
import os
import random
import time

fps = 120.0
frameCount = 0
lastTime = 0.0
period=[10,7.5]
peakSpeed=250

# https://pinout.xyz/
M1_ENC1_PIN=17
M1_ENC2_PIN=18
M2_ENC1_PIN=26
M2_ENC2_PIN=27

m1Pos = 0
m2Pos = 0

pins = [ M1_ENC1_PIN,
		 M1_ENC2_PIN,
		 M2_ENC1_PIN,
		 M2_ENC2_PIN ]

#------------------------------------------------------------------------
#	verbose or debug mode

def debug(message):
	if verbose:
		print(message)

#------------------------------------------------------------------------
#

def setup():
	initGPIO()
	motors.enable()
	motors.setSpeeds( 0, 0 )

def initGPIO()
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM) # use BCM GPIO pin numbers
	GPIO.setup(pins, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.add_event_detect(M1_ENC1_PIN, GPIO.BOTH, callback=m1Enc)
	GPIO.add_event_detect(M2_ENC1_PIN, GPIO.BOTH, callback=m2Enc)

# motor 1 encoder pin 1 callback
def m1Enc():
	if (GPIO.input(M1_ENC1_PIN) != GPIO.input(M1_ENC2_PIN))
    	m1Pos -= 1
    else:
    	m1Pos += 1

# motor 2 encoder pin 1 callback
def m2Enc():
	if (GPIO.input(M2_ENC1_PIN) != GPIO.input(M2_ENC2_PIN))
    	m2Pos+=1
	else:
    	m2Pos-=1

#------------------------------------------------------------------------
# shutdown procedure

def shutdown(signal, frame):
	GPIO.cleanup()
	motors.setSpeeds( 0, 0 )
	motors.disable()
	os._exit(0)

#------------------------------------------------------------------------
# main()

def main():
	global frameCount
	global lastTime
	while True:
		currentTime=time.time()
		frameCount
		speed1=peakSpeed*sin(2*pi*frameCount/(fps * period[0]))
		speed2=peakSpeed*sin(2*pi*frameCount/(fps * period[1]))
		motors.setSpeeds(speed1,speed2)
		frameCount+=1

		if (currentTime - lastTime > 1):
			print ("left encoder count: " + str(m1Pos))
			print ("right encoder count: " + str(m2Pos))
			lastTime=currentTime
		time.sleep(1/fps)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGHUP, shutdown)

setup()
main()

#------------------------------------------------------------------------



