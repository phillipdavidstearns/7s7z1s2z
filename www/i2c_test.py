from smbus2 import SMBus, i2c_msg


class Encoders():
	def __init__(self,bus=1, address=0x10):
		self.bus = SMBus(bus)
		self.address = address

	def getCount(self, encoderId):
		if encoderId == 1 or encoderId == 2:
			write = i2c_msg.write(self.address, [ord('g'), ord(str(encoderId))])
			read = i2c_msg.read(self.address, 4)
			try:
				self.bus.i2c_rdwr(write, read)
			except Exception as e:
				print("Exception for encoder %s: " % encoderId, e)
			if (list(read)):
				count = int.from_bytes(list(read)[1:],byteorder='big',signed=True) 
				return count
			else:
				raise Exception('Could not read from I2C Bus.')
				return None
		else:
			raise Exception('encoderId must be either 1 or 2')
			return None

	def clearCount(self, encoderId):
		if encoderId == 1 or encoderId == 2:
			write = i2c_msg.write(self.address, [ord('c'), ord(str(encoderId))])
			read = i2c_msg.read(self.address, 4)
			try:
				self.bus.i2c_rdwr(write, read)
			except Exception as e:
				print(e)
			if (list(read)):
				string = ''
				string.join([chr(x) for x in list(read)])
				return string
			else:
				raise Exception('Could not read from I2C Bus.')
				return None
		else:
			raise Exception('encoderId must be either 1 or 2')
			return None

	def getCounts(self):
		count1 = self.getCount(1)
		count2 = self.getCount(2)
		return count1, count2

	def clearCounts(self):
		count1 = self.clearCount(1)
		count2 = self.clearCount(2)
		return count1, count2


if __name__ == "__main__":
	from time import time, sleep
	try:
		encoders = Encoders(1,0x10)
		while True:
			enc1Count = encoders.getCount(1)
			enc2Count = encoders.getCount(2)
			print("Encoder 1 count: %s | Encoder 2 count: %s" % (enc1Count, enc2Count))
			sleep(.01)
	except Exception as e:
		print(e)