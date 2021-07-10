#!/usr/bin/python3
import dual_g2_hpmd_rpi
from rotary_encoder import Decoder
from threading import Thread, Timer
from math import log, pow, sin, tanh, pi
from time import time, sleep
import sys
import asyncio
import json

# global constants

# encoder pins
M1_ENC1_PIN=4
M1_ENC2_PIN=17
M2_ENC1_PIN=18
M2_ENC2_PIN=27

# machineState machine definitions
STARTUP = 0
OPEN = 1
OPEN_HOLD = 2
CLOSE =  3
CLOSE_HOLD = 4

class MotorController(Thread):
	def __init__(self, callback=None):
		self.loopDelay = 0.025
		self.timer=None
		self.callback = callback
		self.GPIO = dual_g2_hpmd_rpi._pi
		self.m1Position = 0
		self.m2Position = 0
		self.m1Decoder = Decoder(self.GPIO, M1_ENC1_PIN, M1_ENC2_PIN, self.m1Callback)
		self.m2Decoder = Decoder(self.GPIO, M2_ENC1_PIN, M2_ENC2_PIN, self.m2Callback)
		self.message = ""
		self.powerEasing=1.0
		self.m1Power = 0
		self.m2Power = 0
		self.powerLimit = 400
		self.powerScalar = 2.0
		self.sigmoidFunction=2
		self.targetOpen = 6000
		self.targetClose = 0
		self.target = 0
		self.m1Offset=0
		self.m2Offset=0
		self.startupDuration = 5
		self.openDuration = 15
		self.openHoldDuration = 5
		self.closeDuration = 12.5
		self.closeHoldDuration = 5
		self.tCurrent = 0
		self.tFinal = 0
		self.tLast = 0
		self.progress = 0
		self.machineState = STARTUP
		Thread.__init__(self)
		self.daemon = True

	def m1Callback(self, value):
		self.m1Position -= value

	def m2Callback(self, value):
		self.m2Position -= value

#------------------------------------------------------------------------
# shutdown procedure

	def stop(self):
		self.timer.cancel()
		dual_g2_hpmd_rpi.motors.forceStop()
		self.join(0.0)

	def pause(self):
		self.timer.cancel()
		dual_g2_hpmd_rpi.motors.forceStop()
		return

	def resume(self):
		self.tCurrent = time()
		self.tFinal = self.tCurrent + 5
		self.motionControl()
		return

	def startup(self):
		self.tCurrent = time()
		self.tFinal = self.tCurrent + self.startupDuration
		self.motionControl()
		
#------------------------------------------------------------------------
# helper functions
	
	def send(self, message, object=None):
		self.message = message
		parsed={}
		response={}
		try:
			parsed = json.loads(self.message)
		except Exception as e:
			print("Exception: ",e)

		if 'get' in parsed and parsed['get'] == "all":
			response=self.getParams()
		if 'set' in parsed:
			try:
				self.setParams(parsed['set'])
				response['message']="Settings applied"
			except Exception as e:
				print("Exception: ",e)

		if object:
			try:
				object.write_message(response)
			except Exception as e:
				print("Exception: ",e)
		elif self.callback:
			self.callback(message)
		else:
			pass

	def setParams(self,params):
		for param in params:
			value = params[param]
			if param == 'startupDuration':
				self.startupDuration = float(value)
			if param == 'openDuration':
				self.openDuration = float(value)
			if param == 'openHoldDuration':
				self.openHoldDuration = float(value)
			if param == 'closeDuration':
				self.closeDuration = float(value)
			if param == 'closeHoldDuration':
				self.closeHoldDuration = float(value)
			if param == 'targetOpen':
				self.targetOpen = float(value)
			if param == 'targetClose':
				self.targetClose = float(value)
			if param == 'm1Offset':
				self.m1Offset = float(value)
			if param == 'm2Offset':
				self.m2Offset = float(value)
			if param == 'sigmoidFunction':
				self.sigmoidFunction = int(value)
			if param == 'powerScalar':
				self.powerScalar = float(value)
			if param == 'powerEasing':
				self.powerEasing = float(value)
			if param == 'powerLimit':
				self.powerLimit = float(value)


	def getParams(self):
		data = {}
		data['loopDelay']=self.loopDelay
		data['m1Position']=self.m1Position
		data['m2Position']=self.m2Position
		data['powerEasing']=self.powerEasing
		data['m1Power']=self.m1Power
		data['m2Power']=self.m2Power
		data['powerLimit']=self.powerLimit
		data['powerScalar']=self.powerScalar
		data['sigmoidFunction']=self.sigmoidFunction
		data['targetOpen']=self.targetOpen
		data['targetClose']=self.targetClose
		data['target']=self.target
		data['startupDuration']=self.startupDuration
		data['openDuration']=self.openDuration
		data['openHoldDuration']=self.openHoldDuration
		data['closeDuration']=self.closeDuration
		data['closeHoldDuration']=self.closeHoldDuration
		data['tCurrent']=self.tCurrent
		data['tFinal']=self.tFinal
		data['progress']=self.progress
		data['machineState']=self.machineState
		return data

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
		dual_g2_hpmd_rpi.motors.setSpeeds(self.m1Power/2.0, self.m2Power/2.0)
		self.tCurrent = time()
		# State Machine
		if self.machineState == STARTUP:
			if self.tCurrent > self.tFinal:
				self.tFinal = self.tCurrent + self.openDuration
				self.machineState = OPEN
			else:
				self.target = self.targetClose
		elif self.machineState == OPEN:
			if self.tCurrent > self.tFinal:
				self.tFinal = self.tCurrent + self.openHoldDuration
				self.machineState = OPEN_HOLD
				self.target = self.targetOpen
			else:
				self.progress = 1-((self.tFinal - self.tCurrent) / (self.openDuration))
				self.target = (self.sigmoid(self.progress,self.sigmoidFunction) * (self.targetOpen - self.targetClose)) + self.targetClose
		elif self.machineState == OPEN_HOLD:
			if self.tCurrent > self.tFinal:
				self.tFinal = self.tCurrent + self.closeDuration
				self.machineState = CLOSE
			else:
				self.target = self.targetOpen
		elif self.machineState == CLOSE:
			if self.tCurrent > self.tFinal:
				self.tFinal = self.tCurrent + self.closeHoldDuration
				self.machineState = CLOSE_HOLD
				self.target = self.targetClose
			else:
				self.progress = (self.tFinal - self.tCurrent) / self.closeDuration
				self.target = (self.sigmoid(self.progress,self.sigmoidFunction) * (self.targetOpen - self.targetClose)) + self.targetClose
		elif self.machineState == CLOSE_HOLD:
			if self.tCurrent > self.tFinal:
				self.tFinal = self.tCurrent + self.openDuration
				self.machineState = OPEN
			else:
				self.target=self.targetClose
		
		# Calculate and apply speeds
		force = self.powerScalar*(self.target - self.m1Position)
		self.m1Power += self.ease(self.m1Power, force, self.powerEasing)
		self.m1Power = self.constrain(self.m1Power, -self.powerLimit, self.powerLimit)

		force = self.powerScalar*(self.target - self.m2Position)
		self.m2Power += self.ease(self.m2Power, force, self.powerEasing)
		self.m2Power = self.constrain(self.m2Power, -self.powerLimit, self.powerLimit)

		dual_g2_hpmd_rpi.motors.setSpeeds(self.m1Power,self.m2Power)
		if dual_g2_hpmd_rpi.motors.getFaults():
			self.stop()
			raise Exception("Motor Fault Detected")
		else:
			self.timer=Timer(self.loopDelay, self.motionControl)
			self.timer.start()

	def run(self):
		self.startup()
		

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
