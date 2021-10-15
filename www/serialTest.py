import serial
from time import time, sleep
# consider pyserial-asyncio https://tinkering.xyz/async-serial/

class Encoders():
	def __init__(self, port='/dev/ttyAMA0', baud=115200, timeout=0):
		self.port=port
		self.baud=baud
		self.timeout=timeout
		self.ser=None
		try:
			self.ser=serial.Serial(self.port, self.baud, write_timeout=self.timeout, timeout=self.timeout)
		except Exception as e:
			print(e)

	def getCount(self, device):
		if device == 1 or device == 2:
			command = 'g'+str(device)
			self.ser.write(command.encode('utf-8'))
			while True:
				response = self.ser.readlines()
				if response:
					break
			return response
		else:
			raise Exception("Device must be 1 or 2")

	def clearCount(self,device): # expects a serial object
		if device == 1 or device == 2:
			command = 'c'+str(device)
			self.ser.write(command.encode('utf-8'))
			while True:
				response = self.ser.readlines()
				if response:
					break
			return response
		else:
			raise Exception("Device must be 1 or 2")

	def resyncConnection(self): # expects a serial object
		command = 'aa'
		self.ser.write(command.encode('utf-8'))
		while True:
			response = self.ser.readlines()
			if response:
				break
		for line in response:
			print(line)

	def clearSerialBuffer(self):
		while True:
			response = self.ser.read()
			if not response:
				break

	def getCounts(self):
		return self.getCount(1), self.getCount(2)

	def clearCounts(self):
		return self.clearCount(1), self.clearCount(2)


def main():
	encoders = Encoders()
	encoders.clearSerialBuffer()

	while True:
		startTime = time()
		print(encoders.clearCounts())
		print(time() - startTime)
		sleep(.01)

if __name__ == '__main__':
	try:
		main()
	except Exception as e:
		print('[!] Caught Exception: ', e)
	finally:
		exit()