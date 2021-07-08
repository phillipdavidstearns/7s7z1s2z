#!/usr/bin/python3

from math import log, pow, sin, tanh, pi
from dual_g2_hpmd_rpi import motors, MAX_SPEED
import RPi.GPIO as GPIO
import signal
import sys
import random
from time import sleep, time

# https://pinout.xyz/
M1_ENC1_PIN=4
M1_ENC2_PIN=17
M2_ENC1_PIN=18
M2_ENC2_PIN=27

STARTUP = 0
OPEN = 1
OPEN_HOLD = 2
CLOSE =  3
CLOSE_HOLD = 4

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
	GPIO.setwarnings(True)
	GPIO.setmode(GPIO.BCM) # use BCM GPIO pin numbers
	GPIO.setup(pins, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.add_event_detect(M1_ENC1_PIN, GPIO.BOTH, callback=m1Enc)
	GPIO.add_event_detect(M2_ENC1_PIN, GPIO.BOTH, callback=m2Enc)
	motors.enable()
	motors.setSpeeds( 0, 0 )

# motor 1 encoder pin 1 callback
def m1Enc(value):
	global m1Pos
	if (GPIO.input(M1_ENC1_PIN) != GPIO.input(M1_ENC2_PIN)):
		m1Pos += 1
	else:
		m1Pos -= 1

# motor 2 encoder pin 1 callback
def m2Enc(value):
	global m2Pos
	if (GPIO.input(M2_ENC1_PIN) != GPIO.input(M2_ENC2_PIN)):
		m2Pos +=1
	else:
		m2Pos -=1

#------------------------------------------------------------------------
# shutdown procedure

def shutdown():
	# motors.setSpeeds(0,0)
	# motors.disable()
	GPIO.cleanup()

#------------------------------------------------------------------------
# helper functions

def constrain( _val, _min, _max):
	return min(_max, max(_min,_val))

def sigmoid(_value, _function=-1):
	_value = constrain(_value, 0.0, 1.0)
	if _function == 0: # natural log
		return 1 / ( 1 + pow(-(12 * _value - 6)))
	elif _function == 1: # hyperbolic tan
		return 0.5 * tanh((2 * pi * _value) - pi) + 0.5
	elif _function == 2: # sine squared
		return pow(sin(0.5 * pi * _value), 2)
	else: # default to linear
		return _value

#------------------------------------------------------------------------
# main()

def main():

	def interruptHandler(signal, frame):
		print()
		print("Interrupt (ID: {}) has been caught. Cleaning up...".format(signal))
		sys.exit()

	signal.signal(signal.SIGINT, interruptHandler)
	signal.signal(signal.SIGTERM, interruptHandler)

	speed = 0
	mult = 2
	sigmoidFunction=2
	targetOpen = 2500
	targetClose = 0
	target = 0
	targetLast = 0 
	tDuration = 10
	tEnd = 0
	tCurrent = 0
	tLast = 0
	progress = 0
	state = STARTUP # 0 = startup

	while True:
		tCurrent = time()

		if state == STARTUP:
			if tCurrent > tEnd:
				tEnd = tCurrent + tDuration
				state = OPEN
		elif state == OPEN:
			if tCurrent > tEnd:
				tEnd = tCurrent + tDuration
				state = OPEN_HOLD
				target = targetOpen
			else:
				progress = constrain(1-((tEnd - tCurrent) / (tDuration)),0,1)
				target = (sigmoid(progress,sigmoidFunction) * (targetOpen - targetClose)) + targetClose
		elif state == OPEN_HOLD:
			if tCurrent > tEnd:
				tEnd = tCurrent + tDuration
				state = CLOSE
		elif state == CLOSE:
			if tCurrent > tEnd:
				tEnd = tCurrent + tDuration
				state = CLOSE_HOLD
				target=targetClose
			else:
				progress = (tEnd - tCurrent) / tDuration
				target = (sigmoid(progress,sigmoidFunction) * (targetOpen - targetClose)) + targetClose
		elif state == CLOSE_HOLD:
			if tCurrent > tEnd:
				tEnd = tCurrent + tDuration
				state = OPEN

		
		speed = mult * (target - m1Pos)

		motors.setSpeeds(speed,0)
		if motors.getFaults():
			break

		if (tCurrent - tLast > 1):
			print ("state: ", state," | speed: ",speed, " | target: ", target,"left encoder count: ",m1Pos," | right encoder count: ",m2Pos)
			tLast=tCurrent

if __name__ == "__main__":
	try:
		setup()
		main()
	except Exception as e:
		print("Exception: ",e)
	finally:
		shutdown()
		sys.exit()

