#!/usr/bin/env python
import pigpio
from threading import Thread

class Decoder(Thread):
	def __init__(self, pi, gpioA, gpioB, callback=None):
		if not pi.connected:
			raise IOError("Can't connect to pigpio")
		self.pi = pi
		self.gpioA = gpioA
		self.gpioB = gpioB
		self.callback = callback

		self.levA = 0
		self.levB = 0

		self.lastGpio = None

		self.pi.set_mode(gpioA, pigpio.INPUT)
		self.pi.set_mode(gpioB, pigpio.INPUT)

		self.pi.set_pull_up_down(gpioA, pigpio.PUD_UP)
		self.pi.set_pull_up_down(gpioB, pigpio.PUD_UP)

		self.cbA = self.pi.callback(gpioA, pigpio.EITHER_EDGE, self._pulse)
		self.cbB = self.pi.callback(gpioB, pigpio.EITHER_EDGE, self._pulse)
		
		Thread.__init__(self)
		self.daemon = True

	def _pulse(self, gpio, level, tick):
		if gpio == self.gpioA and not level == 2:
			self.levA = level
		else:
			self.levB = level

		if gpio != self.lastGpio: # debounce
			self.lastGpio = gpio
			if gpio == self.gpioA and level == self.levB:
					self.callback(1)
			elif gpio == self.gpioA and not level == self.levB:
					self.callback(-1)
			elif gpio == self.gpioB and level == self.levA:
					self.callback(-1)
			elif gpio == self.gpioB and not level == self.levA:
					self.callback(1)

	def cancel(self):
		self.cbA.cancel()
		self.cbB.cancel()

	def run(self):
		pass	

if __name__ == "__main__":

	import time
	import pigpio
	import rotary_encoder

	pos = 0

	def callback(step):
		global pos
		pos += step
		print("pos={}".format(pos))

	pi = pigpio.pi()
	decoder = rotary_encoder.decoder(pi, 7, 8, callback)
	decoder.start()
	time.sleep(300)
	decoder.cancel()
	decoder.join()
	pi.stop()