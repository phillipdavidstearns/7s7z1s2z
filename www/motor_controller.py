#!/usr/bin/python3
import dual_g2_hpmd_rpi
from rotary_encoder import Decoder
from threading import Thread
from math import log, pow, sin, tanh, pi
from time import time, sleep
import sys

# global constants

# encoder pins
M1_ENC1_PIN=4
M1_ENC2_PIN=17
M2_ENC1_PIN=18
M2_ENC2_PIN=27

# state machine definitions
STARTUP = 0
OPEN = 1
OPEN_HOLD = 2
CLOSE =  3
CLOSE_HOLD = 4

class MotorController(Thread):
	def __init__(self, callback=None):
		# https://pinout.xyz/
		self.callback = callback
		self.GPIO = dual_g2_hpmd_rpi._pi
		self.m1Pos = 0
		self.m2Pos = 0
		self.m1Decoder = Decoder(self.GPIO, M1_ENC1_PIN, M1_ENC2_PIN, self.m1Callback)
		self.m2Decoder = Decoder(self.GPIO, M2_ENC1_PIN, M2_ENC2_PIN, self.m2Callback)
		self.message = ""
		self.powerEasing=1
		self.power = 0
		self.powerLimit = 400
		self.powerScalar = 1
		self.sigmoidFunction=2
		self.targetOpen = 6000
		self.targetClose = 0
		self.target = 0
		self.startupDuration = 5
		self.openDuration = 15
		self.openHoldDuration = 5
		self.closeDuration = 12.5
		self.closeHoldDuration = 5
		self.tCurrent = 0
		self.tEnd = 0
		self.tLast = 0
		self.progress = 0
		self.state = STARTUP
		Thread.__init__(self)
		self.daemon = True

	def m1Callback(self, value):
		self.m1Pos -= value

	def m2Callback(self, value):
		self.m2Pos -= value

#------------------------------------------------------------------------
# shutdown procedure

	def stop(self):
		dual_g2_hpmd_rpi.motors.forceStop()

	def pause(self):
		return

	def resume(self):
		return

	def startup(self):
		# dual_g2_hpmd_rpi.motors.enable()
		# dual_g2_hpmd_rpi.motors.setSpeeds(0,0)
		self.tCurrent = time()
		self.tEnd = self.tCurrent + self.startupDuration
		
#------------------------------------------------------------------------
# helper functions
	
	def send(self, message, object=None):
		self.message = message
		response={}
		response['message']=message
		if object:
			try:
				object.write_message(response)
			except Exception as e:
				print("Exception: ",e)
		elif self.callback:
			self.callback(message)
		else:
			pass

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
			if self.state == STARTUP:
				if self.tCurrent > self.tEnd:
					self.tEnd = self.tCurrent + self.openDuration
					self.state = OPEN
					self.target = self.targetClose
			elif self.state == OPEN:
				if self.tCurrent > self.tEnd:
					self.tEnd = self.tCurrent + self.openHoldDuration
					self.state = OPEN_HOLD
					self.target = self.targetOpen
				else:
					self.progress = 1-((self.tEnd - self.tCurrent) / (self.openDuration))
					self.target = (self.sigmoid(self.progress,self.sigmoidFunction) * (self.targetOpen - self.targetClose)) + self.targetClose
			elif self.state == OPEN_HOLD:
				if self.tCurrent > self.tEnd:
					self.tEnd = self.tCurrent + self.closeDuration
					self.state = CLOSE
			elif self.state == CLOSE:
				if self.tCurrent > self.tEnd:
					self.tEnd = self.tCurrent + self.closeHoldDuration
					self.state = CLOSE_HOLD
					self.target = self.targetClose
				else:
					self.progress = (self.tEnd - self.tCurrent) / self.closeDuration
					self.target = (self.sigmoid(self.progress,self.sigmoidFunction) * (self.targetOpen - self.targetClose)) + self.targetClose
			elif self.state == CLOSE_HOLD:
				if self.tCurrent > self.tEnd:
					self.tEnd = self.tCurrent + self.openDuration
					self.state = OPEN
			
			# Calculate and apply speeds
			force = self.powerScalar*(self.target - self.m1Pos)
			self.power += self.ease(self.power, force, self.powerEasing)
			self.power = self.constrain(self.power, -self.powerLimit, self.powerLimit)
			dual_g2_hpmd_rpi.motors.setSpeeds(self.power,0)
			if dual_g2_hpmd_rpi.motors.getFaults():
				self.stop()
				raise Exception("Motor Fault Detected")
			# sleep(.05)

	def run(self):
		self.startup()
		self.motionControl()

if __name__ == "__main__":
	def callback(message):
		print("message: ", message)
	mc = MotorController(callback)
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
