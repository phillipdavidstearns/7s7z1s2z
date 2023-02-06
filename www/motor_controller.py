#!/usr/bin/python3

import dual_g2_hpmd_rpi
from encoders_serial import Encoders
from threading import Thread, Timer
from math import log, exp, sin, tanh, pi
from time import time, sleep
from random import random
import sys
import os
import json
import asyncio
import pigpio

# machineState machine definitions
STOP = -2
PAUSED = -1
STARTUP = 0
OPEN = 1
OPEN_HOLD = 2
CLOSE =  3
CLOSE_HOLD = 4

# testing MotorController as non sublassed Thread.

class MotorController(Thread):
	def __init__(self, callback=None):
		self.DEBUG = True
		if self.DEBUG: print('[*] Initializing MotorController instance')
		self.defaultsFile="default_settings.json"
		self.defaultsPath=os.path.dirname(os.path.abspath(__file__))
		self.settings = {}
		self.loopDelay = 0.01
		self.timer = None # used to create precision timed loop for self.MotionControl()
		if self.DEBUG: print('[*] Setting up dual_g2_hpmd_rpi module')
		self.GPIO = pigpio.pi() #spin up a new pigpio Object... hope there are no conflicts
		self.m1Position = 0
		self.m2Position = 0
		self.m1LastPosition = 0
		self.m2LastPosition = 0
		self.m1Speed = 0
		self.m2Speed = 0
		self.m1Flipped = True
		self.m2Flipped = False
		if self.DEBUG: print('[*] Initializing up encoders')
		self.encoders = Encoders()
		self.powerEasing = 0.75
		self.m1Power = 0
		self.m2Power = 0
		self.powerLimit = 150
		self.powerScalar = 2.0
		self.sigmoidFunction = 2
		self.targetOpen = 5500
		self.targetClose = 0
		self.target = 0
		self.m1Offset = 0
		self.m2Offset = 0
		self.m1OffsetTarget = 0
		self.m2OffsetTarget = 0
		self.openDuration = 15
		self.openHoldDuration = 15
		self.closeDuration = 12.5
		self.closeHoldDuration = 17.5
		self.tCurrent = 0
		self.tFinal = 0
		self.tLast = 0
		self.tRemaining = 0
		self.progress = 0
		self.pauseOnOpen = False # flag to run self.pause() on arrival at OPEN_HOLD
		self.pauseOnClose = False # flag to run self.pause() on arrival at CLOSE_HOLD
		self.machineState = None
		self.lastMachineState = 0
		self.targetPositionWindow = 50
		if self.DEBUG: print('[*] Initializing thread')
		Thread.__init__(self)
		self.daemon = True
		self.applySettings(self.loadDefaults())
		self.shutdown = False
		if self.DEBUG: print('[+] Completed initizlization of MotorController instance.')

#------------------------------------------------------------------------
# start up, stop, pause, resume, Goto

	def startup(self):
		if self.DEBUG: print('[*] MotorController Startup')
		self.shutdown = False
		self.machineState=PAUSED
		self.progress = 0
		if self.DEBUG: print('[*] Starting Encoders')
		self.encoders.start()
		sleep(1)
		self.encoders.clearCounts()
		if self.DEBUG: print('[*] Excecuting self.motionControl() loop')
		self.motionControl()
		if self.DEBUG: print('[+] MotorController Startup finished')

	def stop(self):
		if not self.machineState == STOP:
			if not self.machineState == PAUSED:
				self.lastMachineState = self.machineState
			self.machineState = STOP
			if self.DEBUG: print('[*] MotorController Stopping')
			self.shutdown = True
			if self.timer:
				if self.DEBUG: print('[*] Cancelling MotorController.timer')
				self.timer.cancel()
			if self.DEBUG: print('[*] Setting motorspeeds to 0.0')
			dual_g2_hpmd_rpi.motors.setSpeeds(0.0,0.0)
			if self.DEBUG: print('[*] Terminating encoders')
			self.encoders.stop() # Stopping the Decoder Thread
			if self.DEBUG: print('[+] MotorController stopped')


	def pause(self):
		if self.DEBUG: print('[*] Pausing')
		if not (self.machineState == PAUSED or self.machineState == STOP):
			if not( self.machineState == OPEN_HOLD or self.machineState == CLOSE_HOLD):
				if self.timer:
					if self.DEBUG: print('[*] Cancelling self.timer')
					self.timer.cancel()
			if self.DEBUG: print('[*] Setting motorspeeds to 0.0')
			dual_g2_hpmd_rpi.motors.setSpeeds(0.0,0.0)
			self.lastMachineState = self.machineState
			self.machineState = PAUSED
			if self.DEBUG: print('[+] MotorController paused')
		else:
			if self.DEBUG: print('[-] MotorController already paused')
			
	def resume(self):
		if self.DEBUG: print('[*] Resuming')
		if self.machineState == PAUSED or self.machineState == STOP:
			self.shutdown = False
			tDuration = 10
			# Special case where we press RESUME from first boot/startup
			if self.lastMachineState == STARTUP:
				self.machineState = OPEN
				tDuration = self.openDuration
			else:
				self.machineState = self.lastMachineState
			if self.lastMachineState == OPEN:
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
			if self.machineState == STOP:
				self.lastMachineState = STOP
			else:
				self.lastMachineState = PAUSED
			if self.DEBUG: print('[*] Executing self.motionControl() loop')
			self.motionControl()
			if self.DEBUG: print('[+] Successfully resumed')
		else:
			if self.DEBUG: print('[-] MotorController was not paused or stopped')

	def goto(self, position):
		if not self.machineState == STOP:
			self.tCurrent = time()
			if int(position) == OPEN:
				if self.DEBUG: print('[*] Going to OPEN')
				self.machineState = OPEN
				self.tFinal = self.tCurrent + self.openDuration * (1-self.progress)
				self.pauseOnOpen = False
			elif int(position) == OPEN_HOLD:
				if self.DEBUG: print('[*] Going to OPEN_HOLD')
				self.machineState = OPEN
				self.tFinal = self.tCurrent + self.openDuration * (1-self.progress)
				self.pauseOnOpen = True
			elif int(position) == CLOSE:
				if self.DEBUG: print('[*] Going to CLOSE')
				self.machineState = CLOSE
				self.tFinal = self.tCurrent + self.closeDuration * self.progress
				self.pauseOnClose = False
			elif int(position) == CLOSE_HOLD:
				if self.DEBUG: print('[*] Going to CLOSE_HOLD')
				self.machineState = CLOSE
				self.tFinal = self.tCurrent + self.closeDuration * self.progress
				self.pauseOnClose = True
			else:
				if self.DEBUG: print('[!] Invalid position: %s' % position)
			if self.machineState == PAUSED:
				self.motionControl()

#------------------------------------------------------------------------
# helper functions
	
	# may keep this as synchronous and run in executor or run_coroutine_threadsafe() from server
	async def websocket(self, websocket, request):
		parsed={}
		response={}
		try:
			parsed = json.loads(request)
		except Exception as e:
			print("JSON parsing Exception: ",e)
		if 'get' in parsed:
			if parsed['get'] == "status":
				status = self.getStatus()
				response = {'status': status}
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
			elif parsed['set'] == "stop": 
				self.stop()
			elif parsed['set'] == "saveSettings":
				self.saveSettings()
			elif parsed['set'] == "saveDefaults":
				self.saveDefaults()
			elif 'applyOffsets' in parsed['set']:
				if self.machineState == PAUSED or self.machineState == OPEN_HOLD or self.machineState == CLOSE_HOLD:
					if self.machineState == OPEN_HOLD or self.lastMachineState == OPEN_HOLD:
						response['applyOffsets'] = 'go to close, then apply'
					elif self.machineState == CLOSE_HOLD or self.lastMachineState == CLOSE_HOLD or self.lastMachineState == STARTUP:
						self.m1Offset = 0
						self.m2Offset = 0
						self.m1OffsetTarget = 0
						self.m2OffsetTarget = 0
						self.encoders.clearCounts()
						response['applyOffsets'] = 'applied'
				else:
					response['applyOffsets'] = 'error'
			elif 'set' in parsed:
				if self.machineState == PAUSED or self.machineState == OPEN_HOLD or self.machineState == CLOSE_HOLD:
					response = self.applySettings(parsed['set'])
				else:
					response = {'settings':'error'}
			else:
				raise Exception("Unrecognized request: ", request)
		else:
			raise Exception("Unrecognized request: ", request)

		if websocket and response:
			try:
				await websocket.write_message(json.dumps(response))
			except Exception as e:
				print("WebSocket Write Exception: ",e)

	def getStatus(self):
		status = {}
		status['m1Flipped']=self.m1Flipped
		status['m2Flipped']=self.m2Flipped
		status['loopDelay']=self.loopDelay
		status['m1Position']=self.m1Position
		status['m2Position']=self.m2Position
		status['m1Speed']=self.m1Speed
		status['m2Speed']=self.m2Speed
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
		status['openDuration']=self.openDuration
		status['openHoldDuration']=self.openHoldDuration
		status['closeDuration']=self.closeDuration
		status['closeHoldDuration']=self.closeHoldDuration
		status['tCurrent']=self.tCurrent
		status['tFinal']=self.tFinal
		status['progress']=self.progress
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
		settings['openDuration']=self.openDuration
		settings['openHoldDuration']=self.openHoldDuration
		settings['closeDuration']=self.closeDuration
		settings['closeHoldDuration']=self.closeHoldDuration
		return settings

	def applySettings(self,params):
		if params:
			errors = { 'errors':{}}
			for param in params:
				value = params[param]
				if param == 'm1Flipped':
					self.m1Flipped = value
				elif param == 'm2Flipped':
					self.m2Flipped = value
				elif param == 'openDuration':
					self.openDuration = self.constrain(float(value),5,30)
				elif param == 'openHoldDuration':
					self.openHoldDuration = self.constrain(float(value),5,30)
				elif param == 'closeDuration':
					self.closeDuration = self.constrain(float(value),5,30)
				elif param == 'closeHoldDuration':
					self.closeHoldDuration = self.constrain(float(value),5,30)
				elif param == 'targetOpen':
					self.targetOpen = int(self.constrain(int(value),0,16800))
				elif param == 'targetClose':
					self.targetClose = int(self.constrain(int(value),-4200,4200))
				elif param == 'm1Offset':
					self.m1OffsetTarget = int(self.constrain(int(value),-8400,8400))
				elif param == 'm2Offset':
					self.m2OffsetTarget = int(self.constrain(int(value),-8400,8400))
				elif param == 'sigmoidFunction':
					self.sigmoidFunction = int(value)
				elif param == 'powerScalar':
					self.powerScalar = self.constrain(float(value),0.5,5.0)
				elif param == 'powerEasing':
					self.powerEasing = self.constrain(float(value),0.125,1.0)
				elif param == 'powerLimit':
					self.powerLimit = int(self.constrain(int(value),0,480))
				else:
					errors['errors']={param,value}
			if errors['errors']:
				return errors
			else:
				return {'settings':"applied"}
		else:
			return {'settings':{'error':'params == None'}}
	
	def saveSettings(self):
		self.settings = self.getSettings()

	def loadSettings(self):
		return self.settings

	def saveDefaults(self):
		path = os.path.join(self.defaultsPath, self.defaultsFile)
		with open(path, "w") as outfile:
			outfile.write(json.dumps(self.getSettings(), indent = 4))

	def loadDefaults(self):
		if self.DEBUG: print('[*] Loading defaults')
		path = os.path.join(self.defaultsPath, self.defaultsFile)
		if os.path.exists(path):
			try:
				with open(path, "r") as outfile:
					return json.load(outfile)
			except Exception as e:
				print("[!] Exception While Loading Defaults: ",e)
		else:
			if self.DEBUG: print('[-] Defaults file not found: %s' % path)
			return None

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

	def motionControl(self):
		# retrigger motioncontrol loop if shutdown flag isn't set
		if not self.shutdown:
			self.timer=Timer(self.loopDelay, self.motionControl)
			self.timer.start()

			# get counts from arduino
			self.m1Position, self.m2Position = self.encoders.getCounts()
			# calculate speed
			self.m1Speed = (self.m1Position - self.m1LastPosition) / self.loopDelay
			self.m2Speed = (self.m2Position - self.m2LastPosition) / self.loopDelay
			self.m1LastPosition = self.m1Position
			self.m2LastPosition = self.m2Position
			# State Machine
			self.tCurrent = time()
			self.tRemaining = self.tFinal - self.tCurrent
			if self.machineState == OPEN:
				if self.tCurrent >= self.tFinal: # OPEN is complete
					self.tFinal = self.tCurrent + self.openHoldDuration
					self.machineState = OPEN_HOLD
				else:
					self.progress = 1 - ( self.tRemaining / self.openDuration )
					self.target = (self.sigmoid(self.progress, self.sigmoidFunction) * (self.targetOpen - self.targetClose)) + self.targetClose
			elif self.machineState == OPEN_HOLD:
				if self.pauseOnOpen:
					self.pause()
					self.pauseOnOpen = False
				if self.tCurrent >= self.tFinal:
					self.tFinal = self.tCurrent + self.closeDuration
					self.machineState = CLOSE
				else:
					self.progress = 1
					self.target = self.targetOpen
			elif self.machineState == CLOSE:
				if self.tCurrent >= self.tFinal:
					self.tFinal = self.tCurrent + self.closeHoldDuration
					self.machineState = CLOSE_HOLD
				else:
					self.progress = ( self.tRemaining / self.closeDuration )
					self.target = (self.sigmoid(self.progress, self.sigmoidFunction) * (self.targetOpen - self.targetClose)) + self.targetClose
			elif self.machineState == CLOSE_HOLD:
				if self.pauseOnClose:
					self.pause()
					self.pauseOnClose = False
				if self.tCurrent >= self.tFinal:
					self.tFinal = self.tCurrent + self.openDuration
					self.machineState = OPEN
				else:
					self.progress = 0
					self.target = self.targetClose

			# Update Offsets
			if not self.m1Offset == self.m1OffsetTarget:
				if self.m1OffsetTarget > self.m1Offset:
					self.m1Offset+=1
				else:
					self.m1Offset-=1

			if not self.m2Offset == self.m2OffsetTarget:
				if self.m2OffsetTarget > self.m2Offset:
					self.m2Offset+=1
				else:
					self.m2Offset-=1

			# Calculate and apply speeds
			if self.m1Flipped: self.m1Position *= -1
			force = self.powerScalar*(self.target - self.m1Position + self.m1Offset)
			self.m1Power += self.ease(self.m1Power, force, self.powerEasing)
			self.m1Power = self.constrain(self.m1Power, -self.powerLimit, self.powerLimit)
			if self.m1Flipped: self.m1Power *= -1
			
			if self.m2Flipped: self.m2Position *= -1
			force = self.powerScalar*(self.target - self.m2Position + self.m2Offset)
			self.m2Power += self.ease(self.m2Power, force, self.powerEasing)
			self.m2Power = self.constrain(self.m2Power, -self.powerLimit, self.powerLimit)
			if self.m2Flipped: self.m2Power *= -1

			if self.machineState == CLOSE_HOLD or self.machineState == OPEN_HOLD:
				if abs(self.target - self.m1Position + self.m1Offset) < self.targetPositionWindow:
					self.m1Power=0.0
				if abs(self.target - self.m2Position + self.m2Offset) < self.targetPositionWindow:
					self.m2Power=0.0

			# if abs(self.m1Power) >= self.powerLimit and (self.m1Speed == 0 or self.m2Speed == 0):
			# 	print("[!] Stopped! Power limit %s reached and motors are not responding" % self.powerLimit)
			# 	self.m1Power=0.0
			# 	self.m2Power=0.0
			# 	self.stop()

			if self.machineState == STOP:
				self.m1Power=0.0
				self.m2Power=0.0

			dual_g2_hpmd_rpi.motors.setSpeeds(self.m1Power, self.m2Power)


		else:
			dual_g2_hpmd_rpi.motors.setSpeeds(0.0, 0.0)


	def run(self):
		self.startup()
		
if __name__ == "__main__":
	mc = MotorController()
	mc.DEBUG=True
	try:
		print(mc.defaultsPath)
		print(os.path.join(mc.defaultsPath,"default_settings.json"))
		mc.saveSettings()
		mc.loadSettings()
		mc.saveDefaults()
		mc.loadDefaults()
		print("settings: ", mc.getSettings())
		mc.run()
		while True:
			sleep(1)
	except Exception as e:
		print("Exception: ",e)
	finally:
		mc.stop()
		sys.exit()
