import asyncio
import serial_asyncio
from threading import Thread
import time

# based on example: pyserial-asyncio https://tinkering.xyz/async-serial/
# Another way of interfacing sync and async code: https://gist.github.com/phizaz/20c36c6734878c6ec053245a477572ec

#==========================================================================
class Encoders(Thread): # subclasses Thread
	def __init__(self, url='/dev/ttyAMA0', baudrate=115200, timeout=1.0):
		self.loop = None
		self.terminate = False
		self.reader = None
		self.writer = None
		self.enc1 = 0
		self.enc2 = 0
		self.url = url
		self.baudrate = baudrate
		self.serialPortIsOpen = False
		self.timeout = timeout
		Thread.__init__(self)
		self.daemon = True
		
	def run(self):
		self.loop = asyncio.new_event_loop() # create new event loop in Thread
		self.loop.create_task(self.main())
		self.loop.run_forever()

	def stop(self):
		self.terminate = True
		time.sleep(0.1)
		print("closing loop")
		self.loop.close()
		time.sleep(0.1)
		print("terminating thread")
		self.join()
		
	# https://github.com/GNS3/gns3-server/commit/01bcbe2fd9ef7707061008e18424e93c6518a3cc

	async def openSerialPort(self):
		print("connecting to serial port")
		try:
			self.reader, self.writer = await serial_asyncio.open_serial_connection(url=self.url, baudrate=self.baudrate)
		except OSError as e:
			print("OSError while connecting: ", e)
		if (not self.reader) or (not self.writer):
			raise IOError("Unable to connect to serial port")
		else:
			self.serialPortIsOpen = True
		
	async def send(self, msg):
		try:
			self.writer.write(msg) # cannot be awaited
			await self.writer.drain()
		except Exception as e:
			print("Serial write error: ", e)

	async def recv(self, _depth):
		result = None
		depth = _depth
		if depth >= 5:
			raise Exception("Serial receive recusrion depth exceeded: %s" % depth)
			return None, depth
		try:
			result = await asyncio.wait_for(self.reader.readuntil(separator=b'\r\n'), timeout=0.005)
		except asyncio.TimeoutError:
			pass
		if result:
			return result, depth
		else:
			# print("Nothing to read. Trying once more... depth = ", depth)
			result, depth = await self.recv(depth+1)
		return result, depth

	async def rdwr(self, msg):
		await self.send(msg)
		received, depth = await self.recv(0)
		return received
		
	async def readEncoders(self):
		result = await self.rdwr(b'g0\n')
		if result:
			msg = result.decode().strip()
			if msg == 'err!':
				pass
				# print("Arduino didn't like that.")
			elif '|' in msg:
				counts = msg.split('|')
				self.enc1 = int(counts[0])
				self.enc2 = int(counts[1])
			else:
				# print("That's strange... got: ", result)
				pass
			return msg
		else:
			return None
		
	async def read(self):
		result = None
		try:
			result = await asyncio.wait_for(self.reader.readuntil(separator=b'\r\n'), timeout=0.005)
		except asyncio.TimeoutError:
			pass
		if result:
			msg = result.decode().strip()
			if '|' in msg:
				counts = msg.split('|')
				self.enc1 = int(counts[0])
				self.enc2 = int(counts[1])
			else:
				print("This is garbage: %s" % msg)

	# these are meant to be called from external synchronous code
	def getCounts(self):
		return self.enc1, self.enc2

	def clearCounts(self):
		# asyncio.run_coroutine_threadsafe(self.send(b'c0\n'), self.loop)
		asyncio.run_coroutine_threadsafe(self.send(b'a'), self.loop)

	async def main(self):
		await self.openSerialPort()
		while self.serialPortIsOpen:
			if self.terminate:
				break
			try:
				# await self.readEncoders() # the old way of requesting the receiving
				await self.read()
				await asyncio.sleep(.005)
			except Exception as e:
				print("main() loop: ",e)
				continue
		self.loop.stop()

#==========================================================================
# Test serial asyncio implementation and shutdown

if __name__ == '__main__':
	count = 0
	enc1 = 0
	enc2 = 0
	try:
		encoders = Encoders()
		encoders.start()
		time.sleep(1)
		encoders.clearCounts()
		while True:
			enc1, enc2 = encoders.getCounts()
			print("                                     ", end='\r')
			print("counts: ", enc1, enc2, end='\r')
			time.sleep(.01)

	except Exception as e:
		print('[!] Caught Exception: ', e)
	finally:
		encoders.stop()
		exit()