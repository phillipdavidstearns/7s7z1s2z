#!/usr/bin/python3

import pigpio
from rotary_encoder import decoder
from math import log, pow, sin, tanh, pi
from dual_g2_hpmd_rpi import motors, MAX_SPEED
from time import sleep, time
import sys

class motorController:
	def __init__(self):
		self.m1Pos = 0
		self.m2Pos = 0

	# https://pinout.xyz/
		self.M1_ENC1_PIN=4
		self.M1_ENC2_PIN=17
		self.M2_ENC1_PIN=18
		self.M2_ENC2_PIN=27

		self.STARTUP = 0
		self.OPEN = 1
		self.OPEN_HOLD = 2
		self.CLOSE =  3
		self.CLOSE_HOLD = 4

		self.GPIO = pigpio.pi()
		self.m1Decoder = decoder(self.GPIO, self.M1_ENC1_PIN, self.M1_ENC2_PIN, self.m1Callback)
		self.m2Decoder = decoder(self.GPIO, self.M2_ENC1_PIN, self.M2_ENC2_PIN, self.m2Callback)

	def m1Callback(self, value):
		self.m1Pos -= value

	def m2Callback(self, value):
		self.m2Pos -= value

#------------------------------------------------------------------------
# shutdown procedure

	def stop(self):
		motors.setSpeeds(0,0)
		motors.disable()
		self.m1Decoder.cancel()
		self.m2Decoder.cancel()
		self.GPIO.stop()

#------------------------------------------------------------------------
# helper functions

	def constrain(self, _val, _min, _max):
		return min(_max, max(_min,_val))


	def ease(self,_val, _target, _ease):
  		return _ease * (_target - _val)

	def sigmoid(self,_value, _function=-1):
		_value = self.constrain(_value, 0.0, 1.0)
		if _function == 0: # natural log
			return 1 / ( 1 + pow(-(12 * _value - 6)))
		elif _function == 1: # hyperbolic tan
			return 0.5 * tanh((2 * pi * _value) - pi) + 0.5
		elif _function == 2: # sine squared
			return pow(sin(0.5 * pi * _value), 2)
		else: # default to linear
			return _value

	def start(self):
		
		motors.enable()
		motors.setSpeeds( 0, 0 )

		cpr = 131*64
		powerEasing=1
		power = 0
		powerLimit = 400
		powerScalar = 1
		sigmoidFunction=2
		targetOpen = cpr*2/3
		targetClose = 0
		target = 0
		tDuration = 10
		tEnd = tDuration
		tCurrent = 0
		tLast = 0
		progress = 0
		state = self.STARTUP # 0 = startup

		while True:
			tCurrent = time()
			if state == self.STARTUP:
				if tCurrent > tEnd:
					tEnd = tCurrent + tDuration
					state = self.OPEN
			elif state == self.OPEN:
				if tCurrent > tEnd:
					tEnd = tCurrent + tDuration
					state = self.OPEN_HOLD
					target = targetOpen
				else:
					progress = 1-((tEnd - tCurrent) / (tDuration))
					target = (self.sigmoid(progress,sigmoidFunction) * (targetOpen - targetClose)) + targetClose
			elif state == self.OPEN_HOLD:
				if tCurrent > tEnd:
					tEnd = tCurrent + tDuration
					state = self.CLOSE
			elif state == self.CLOSE:
				if tCurrent > tEnd:
					tEnd = tCurrent + tDuration
					state = self.CLOSE_HOLD
					target=targetClose
				else:
					progress = (tEnd - tCurrent) / tDuration
					target = (self.sigmoid(progress,sigmoidFunction) * (targetOpen - targetClose)) + targetClose
			elif state == self.CLOSE_HOLD:
				if tCurrent > tEnd:
					tEnd = tCurrent + tDuration
					state = self.OPEN

			force = powerScalar*(target - self.m1Pos)
			power += self.ease(power, force, powerEasing)
			power = self.constrain(power, -powerLimit, powerLimit)

			motors.setSpeeds(power,0)
			if motors.getFaults():
				break

		# if (tCurrent - tLast > 1):
		# 	print ("state: ", state," | power: ",power, " | target: ", target,"left encoder count: ",m1Pos," | right encoder count: ",m2Pos)
		# 	tLast=tCurrent

if __name__ == "__main__":
	mc = motorController()
	try:
		mc.start()
	except Exception as e:
		print("Exception: ",e)
	finally:
		mc.stop()
		sys.exit()

