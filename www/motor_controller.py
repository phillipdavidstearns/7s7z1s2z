#!/usr/bin/python3

import pigpio
from dual_g2_hpmd_rpi import motors, MAX_SPEED
from rotary_encoder import Decoder
from threading import Thread
from math import log, pow, sin, tanh, pi
from time import time, sleep
import sys

class MotorController(Thread):
	def __init__(self):
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
		self.m1Pos = 0
		self.m2Pos = 0
		self.m1Decoder = Decoder(self.GPIO, self.M1_ENC1_PIN, self.M1_ENC2_PIN, self.m1Callback)
		self.m2Decoder = Decoder(self.GPIO, self.M2_ENC1_PIN, self.M2_ENC2_PIN, self.m2Callback)
		self.message = ""
		self.cpr = 131*64
		self.powerEasing=1
		self.power = 0
		self.powerLimit = 400
		self.powerScalar = 1
		self.sigmoidFunction=2
		self.targetOpen = self.cpr*2/3
		self.targetClose = 0
		self.target = 0
		self.openDuration = 10
		self.openHoldDuration = 10
		self.closeDuration = 10
		self.closeHoldDuration = 10
		self.tEnd = self.openDuration
		self.tCurrent = 0
		self.tLast = 0
		self.progress = 0
		self.state = self.STARTUP # 0 = startup
		Thread.__init__(self)
		self.daemon = True

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

	def pause(self):
		return

	def resume(self):
		return

	def startup(self):
		motors.enable()
		motors.setSpeeds(0,0)
		
#------------------------------------------------------------------------
# helper functions
	
	def send(self, message):
		self.message = message
		print("message: ", message)

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
		
	def motionControl(self):
		while True:
			self.tCurrent = time()
			# State Machine
			if self.state == self.STARTUP:
				if self.tCurrent > self.tEnd:
					self.tEnd = self.tCurrent + self.openDuration
					self.state = self.OPEN
					self.target = self.targetClose
			elif self.state == self.OPEN:
				if self.tCurrent > self.tEnd:
					self.tEnd = self.tCurrent + self.openHoldDuration
					self.state = self.OPEN_HOLD
					self.target = self.targetOpen
				else:
					self.progress = 1-((self.tEnd - self.tCurrent) / (self.openDuration))
					self.target = (self.sigmoid(self.progress,self.sigmoidFunction) * (self.targetOpen - self.targetClose)) + self.targetClose
			elif self.state == self.OPEN_HOLD:
				if self.tCurrent > self.tEnd:
					self.tEnd = self.tCurrent + self.closeDuration
					self.state = self.CLOSE
			elif self.state == self.CLOSE:
				if self.tCurrent > self.tEnd:
					self.tEnd = self.tCurrent + self.closeHoldDuration
					self.state = self.CLOSE_HOLD
					self.target = self.targetClose
				else:
					self.progress = (self.tEnd - self.tCurrent) / self.closeDuration
					self.target = (self.sigmoid(self.progress,self.sigmoidFunction) * (self.targetOpen - self.targetClose)) + self.targetClose
			elif self.state == self.CLOSE_HOLD:
				if self.tCurrent > self.tEnd:
					self.tEnd = self.tCurrent + self.openDuration
					self.state = self.OPEN
			
			# Calculate and apply speeds
			force = self.powerScalar*(self.target - self.m1Pos)
			self.power += self.ease(self.power, force, self.powerEasing)
			self.power = self.constrain(self.power, -self.powerLimit, self.powerLimit)
			motors.setSpeeds(self.power,0)
			if motors.getFaults():
				raise Exception("Motor Fault Detected")
		
		# if (tCurrent - tLast > 1):
		# 	print ("state: ", state," | power: ",power, " | target: ", target,"left encoder count: ",m1Pos," | right encoder count: ",m2Pos)
		# 	tLast=tCurrent

	def run(self):
		self.startup()
		self.motionControl()

if __name__ == "__main__":
	mc = MotorController()
	try:
		mc.start()
		while True:
			mc.send("Future JSON data")
			sleep(1)
	except Exception as e:
		print("Exception: ",e)
	finally:
		mc.stop()
		sys.exit()
