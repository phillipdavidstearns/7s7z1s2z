#!/usr/bin/python3

import dual_g2_hpmd_rpi
from rotary_encoder import Decoder
from threading import Thread, Timer
from math import log, exp, sin, tanh, pi
from time import time, sleep
import sys
import os
import json

# global constants

# encoder pins
M1_ENC1_PIN=4
M1_ENC2_PIN=17
M2_ENC1_PIN=18
M2_ENC2_PIN=27
PUMP_PWM_PIN=21

# machineState machine definitions
PAUSED = -1
STARTUP = 0
OPEN = 1
OPEN_HOLD = 2
CLOSE =  3
CLOSE_HOLD = 4

class MotorController(Thread):
	def __init__(self, callback=None):
		self.defaultsFile="default_settings.json"
		self.defaultsPath=os.path.dirname(os.path.abspath(__file__))
		self.settings = {}
		self.loopDelay = 0.01
		self.timer=None
		self.GPIO = dual_g2_hpmd_rpi._pi
		self.m1Position = 0
		self.m2Position = 0
		self.m1Flipped = False
		self.m2Flipped = True
		self.m1Decoder = Decoder(self.GPIO, M1_ENC1_PIN, M1_ENC2_PIN, self.m1Callback)
		self.m2Decoder = Decoder(self.GPIO, M2_ENC1_PIN, M2_ENC2_PIN, self.m2Callback)
		self.powerEasing=0.75
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
		self.startupDuration = 60
		self.openDuration = 15
		self.openHoldDuration = 15
		self.closeDuration = 12.5
		self.closeHoldDuration = 17.5
		self.tCurrent = 0
		self.tFinal = 0
		self.tLast = 0
		self.progress = 0
		self.lastProgress = 0
		self.machineState = None
		self.lastMachineState = None
		Thread.__init__(self)
		self.daemon = True
		self.applySettings(self.loadDefaults())

	def m1Callback(self, value):
		if self.m1Flipped:
			self.m1Position += value
		else:
			self.m1Position -= value

	def m2Callback(self, value):
		if self.m2Flipped:
			self.m2Position += value
		else:
			self.m2Position -= value

#------------------------------------------------------------------------
# shutdown procedure

	def startup(self):
		self.machineState=STARTUP
		self.progress=0
		self.tCurrent = time()
		self.tFinal = self.tCurrent + self.startupDuration
		self.motionControl()

	def stop(self):
		if not self.timer == None:
			self.timer.cancel()
		dual_g2_hpmd_rpi.motors.setSpeeds(0.0,0.0)


	def pause(self):
		if not self.machineState == PAUSED:
			if not self.timer == None:
				self.timer.cancel()
			dual_g2_hpmd_rpi.motors.setSpeeds(0.0,0.0)
			self.lastMachineState = self.machineState
			self.lastProgress = self.progress
			self.machineState = PAUSED
			
	def resume(self):
		if self.machineState == PAUSED:
			self.machineState = self.lastMachineState
			tDuration=0
			if self.lastMachineState == STARTUP:
				tDuration = self.startupDuration
			elif self.lastMachineState == OPEN:
				tDuration = self.openDuration
			elif self.lastMachineState == OPEN_HOLD:
				tDuration = self.openHoldDuration
			elif self.lastMachineState == CLOSE:
				tDuration = self.closeDuration
			elif self.lastMachineState == CLOSE_HOLD:
				tDuration = self.closeHoldDuration
			else:
				pass
			self.tCurrent = time()
			if self.machineState == OPEN:
				self.tFinal = self.tCurrent + tDuration * (1-self.progress)
			else:
				self.tFinal = self.tCurrent + tDuration * self.progress
			self.lastMachineState = None
			self.motionControl()

	def goto(self, position):
		if self.machineState == PAUSED:
			self.motionControl()
		self.tCurrent = time()
		if int(position) == OPEN:
			self.machineState = OPEN
			self.tFinal = self.tCurrent + self.openDuration * (1-self.progress)
		elif int(position) == CLOSE:
			self.machineState = CLOSE
			self.tFinal = self.tCurrent + self.closeDuration * self.progress
		
#------------------------------------------------------------------------
# helper functions
	
	def send(self, request, object=None):
		parsed={}
		response={}

		try:
			parsed = json.loads(request)
		except Exception as e:
			print("JSON parsing Exception: ",e)

		if 'get' in parsed:
			if parsed['get'] == "status":
				response = {'status':self.getStatus()}
			elif parsed['get'] == "loadSettings":
				response = {'load':self.loadSettings()}
			elif parsed['get'] == "loadDefaults":
				response = {'load':self.loadDefaults()}
			else:
				raise Exception("Unrecognized request: ", request)
		elif 'goto' in parsed:
			self.goto(parsed['goto'])
		elif 'set' in parsed:
			if parsed['set'] == "pause":
				self.pause()
			elif parsed['set'] == "resume": 
				self.resume()
			elif parsed['set'] == "saveSettings":
				self.saveSettings()
			elif parsed['set'] == "saveDefaults":
				self.saveDefaults()
			elif 'set' in parsed:
				response = self.applySettings(parsed['set'])
			else:
				raise Exception("Unrecognized request: ", request)
		else:
			raise Exception("Unrecognized request: ", request)

		if object and response:
			try:
				object.write_message(json.dumps(response))
			except Exception as e:
				print("WebSoket Write Exception: ",e)
		else:
			pass

	def getStatus(self):
		status = {}
		status['m1Flipped']=self.m1Flipped
		status['m2Flipped']=self.m2Flipped
		status['loopDelay']=self.loopDelay
		status['m1Position']=self.m1Position
		status['m2Position']=self.m2Position
		status['m1Offset']=self.m1Offset
		status['m2Offset']=self.m2Offset
		status['powerEasing']=self.powerEasing
		status['m1Power']=self.m1Power
		status['m2Power']=self.m2Power
		status['powerLimit']=self.powerLimit
		status['powerScalar']=self.powerScalar
		status['sigmoidFunction']=self.sigmoidFunction
		status['targetOpen']=self.targetOpen
		status['targetClose']=self.targetClose
		status['target']=self.target
		status['startupDuration']=self.startupDuration
		status['openDuration']=self.openDuration
		status['openHoldDuration']=self.openHoldDuration
		status['closeDuration']=self.closeDuration
		status['closeHoldDuration']=self.closeHoldDuration
		status['tCurrent']=self.tCurrent
		status['tFinal']=self.tFinal
		status['progress']=self.progress
		status['lastProgress']=self.lastProgress
		status['machineState']=self.machineState
		status['lastMachineState']=self.lastMachineState
		return status

	def getSettings(self):
		settings={}
		settings['loopDelay']=self.loopDelay
		settings['m1Flipped']=self.m1Flipped
		settings['m2Flipped']=self.m2Flipped
		settings['powerEasing']=self.powerEasing
		settings['powerLimit']=self.powerLimit
		settings['powerScalar']=self.powerScalar
		settings['sigmoidFunction']=self.sigmoidFunction
		settings['targetOpen']=self.targetOpen
		settings['targetClose']=self.targetClose
		settings['m1Offset']=self.m1Offset
		settings['m2Offset']=self.m2Offset
		settings['startupDuration']=self.startupDuration
		settings['openDuration']=self.openDuration
		settings['openHoldDuration']=self.openHoldDuration
		settings['closeDuration']=self.closeDuration
		settings['closeHoldDuration']=self.closeHoldDuration
		return settings

	def applySettings(self,params):
		errors = { 'errors':{}}
		for param in params:
			value = params[param]
			if param == 'loopDelay':
				self.loopDelay = float(value)
			elif param == 'm1Flipped':
				self.m1Flipped = value
			elif param == 'm2Flipped':
				self.m2Flipped = value
			elif param == 'startupDuration':
				self.startupDuration = float(value)
			elif param == 'openDuration':
				self.openDuration = float(value)
			elif param == 'openHoldDuration':
				self.openHoldDuration = float(value)
			elif param == 'closeDuration':
				self.closeDuration = float(value)
			elif param == 'closeHoldDuration':
				self.closeHoldDuration = float(value)
			elif param == 'targetOpen':
				self.targetOpen = float(value)
			elif param == 'targetClose':
				self.targetClose = float(value)
			elif param == 'm1Offset':
				self.m1Offset = float(value)
			elif param == 'm2Offset':
				self.m2Offset = float(value)
			elif param == 'sigmoidFunction':
				self.sigmoidFunction = int(value)
			elif param == 'powerScalar':
				self.powerScalar = float(value)
			elif param == 'powerEasing':
				self.powerEasing = float(value)
			elif param == 'powerLimit':
				self.powerLimit = float(value)
			else:
				errors['errors']={param,value}

		if errors['errors']:
			return errors
		else:
			return {'settings':"applied"}
	
	def saveSettings(self):
		self.settings=self.getSettings()

	def loadSettings(self):
		return self.settings

	def saveDefaults(self):
		try:
			with open(os.path.join(self.defaultsPath, self.defaultsFile), "w") as outfile:
				outfile.write(json.dumps(self.getSettings(), indent = 4))
		except IOError as e:
			print("While Saving Defaults: ",e)

	def loadDefaults(self):
		try:
			with open(os.path.join(self.defaultsPath, self.defaultsFile), "r") as outfile:
				return json.load(outfile)
		except IOError as e:
			print("While Loading Defaults: ",e)

	def constrain(self, _val, _min, _max):
		return min(_max, max(_min,_val))

	def ease(self,_val, _target, _ease):
		return _ease * (_target - _val)

	def sigmoid(self,_value, _function=-1):
		_value = self.constrain(_value, 0.0, 1.0)
		if _function == 0: # natural log
			return 1 / ( 1 + exp(-(12 * _value - 6)))
		elif _function == 1: # hyperbolic tan
			return 0.5 * tanh((2 * pi * _value) - pi) + 0.5
		elif _function == 2: # sine squared
			return pow(sin(0.5 * pi * _value), 2)
		else: # default to linear
			return _value

	def setPumpSpeed(self, value):
		self._pi.hardware_PWM(PUMP_PWM_PIN, 20000, contraint(value,0.0,1.0)*1000000)
		
	def motionControl(self):
		# retrigger motioncontrol loop
		self.timer=Timer(self.loopDelay, self.motionControl)
		self.timer.start()
		self.tCurrent = time()
		# State Machine
		if self.machineState == STARTUP:
			if self.tCurrent > self.tFinal:
				self.tFinal = self.tCurrent + self.openDuration
				self.machineState = OPEN
			else:
				self.progress = 0.0
		elif self.machineState == OPEN:
			if self.tCurrent >= self.tFinal:
				self.tFinal = self.tCurrent + self.openHoldDuration
				self.machineState = OPEN_HOLD
			else:
				self.progress = 1 - ((self.tFinal - self.tCurrent) / (self.openDuration))
		elif self.machineState == OPEN_HOLD:
			if self.tCurrent >= self.tFinal:
				self.tFinal = self.tCurrent + self.closeDuration
				self.machineState = CLOSE
			else:
				self.progress = 1.0
		elif self.machineState == CLOSE:
			if self.tCurrent >= self.tFinal:
				self.tFinal = self.tCurrent + self.closeHoldDuration
				self.machineState = CLOSE_HOLD
			else:
				self.progress = (self.tFinal - self.tCurrent) / self.closeDuration
		elif self.machineState == CLOSE_HOLD:
			if self.tCurrent >= self.tFinal:
				self.tFinal = self.tCurrent + self.openDuration
				self.machineState = OPEN
			else:
				self.progress = 0.0

		self.target = (self.sigmoid(self.progress,self.sigmoidFunction) * (self.targetOpen - self.targetClose)) + self.targetClose
		
		# Calculate and apply speeds
		force = self.powerScalar*(self.target - (self.m1Position + self.m1Offset))
		self.m1Power += self.ease(self.m1Power, force, self.powerEasing)
		self.m1Power = self.constrain(self.m1Power, -self.powerLimit, self.powerLimit)
		if self.m1Flipped:
			self.m1Power *= -1
		
		force = self.powerScalar*(self.target - (self.m2Position + self.m2Offset))
		self.m2Power += self.ease(self.m2Power, force, self.powerEasing)
		self.m2Power = self.constrain(self.m2Power, -self.powerLimit, self.powerLimit)
		if self.m2Flipped:
			self.m2Power *= -1
		
		dual_g2_hpmd_rpi.motors.setSpeeds(self.m1Power,self.m2Power)

	def run(self):
		self.startup()
		
if __name__ == "__main__":
	mc = MotorController()
	try:
		# print(mc.defaultsPath)
		# print(os.path.join(mc.defaultsPath,"default_settings.json"))
		# mc.saveSettings()
		# mc.loadSettings()
		# mc.saveDefaults()
		# mc.loadDefaults()
		# print("settings: ", mc.getSettings())
		mc.start()
		while True:
			sleep(1)
	except Exception as e:
		print("Exception: ",e)
	finally:
		mc.stop()
		sys.exit()
