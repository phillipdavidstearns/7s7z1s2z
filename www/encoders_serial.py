import asyncio
import serial_asyncio
from threading import Thread
import time

# based on example: pyserial-asyncio https://tinkering.xyz/async-serial/
# Another way of interfacing sync and async code: https://gist.github.com/phizaz/20c36c6734878c6ec053245a477572ec

#==========================================================================
class Encoders(Thread): # subclasses Thread
	def __init__(self, url='/dev/ttyAMA0', baudrate=115200):
		self.loop = None
		self.terminate = False
		self.reader = None
		self.writer = None
		self.enc1 = 0
		self.enc2 = 0
		self.url = url
		self.baudrate = baudrate
		Thread.__init__(self)
		self.daemon = False
		
	def run(self):
		self.loop = asyncio.new_event_loop() # create ne event loop in Thread
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

	async def connect(self, timeout=0.):
		print("connecting")
		try:
			self.reader, self.writer = await serial_asyncio.open_serial_connection(url=self.url, baudrate=self.baudrate)
		except OSError as e:
			print("OSError while connecting: ", e)
		if (not self.reader) or (not self.writer):
			raise IOError("Unable to connect to serial port")
		
	async def send(self, msg):
		try:
			self.writer.write(msg) # apparently this is not async code
		except Exception as e:
			print("Send error: ", e)

	async def recv(self):
		try:
			msg = await asyncio.wait_for(self.reader.readuntil(b'\r\n'), timeout=0.001)
			if not msg == None:
				msg = msg.decode().strip()
				if msg == 'err!':
					raise Exception("Arduino didn't like that.")
				else:
					return msg
		except Exception as e:
			pass

	async def rdwr(self, msg):
		sent = await self.send(msg)
		received = await self.recv()
		return received
		
	async def readEncoders(self):
		result = await self.rdwr(b'g0\n')
		if result and '|' in result:
			counts = result.split('|')
			self.enc1 = int(counts[0])
			self.enc2 = int(counts[1])

	# these are meant to be called from external synchronous code
	def getCounts(self):
		return self.enc1, self.enc2

	def clearCounts(self):
		asyncio.run_coroutine_threadsafe(self.send(b'c0\n'), self.loop)

	 async def main(self):
			await self.connect()
			while True:
				if self.terminate:
					break
				try:
					await self.readEncoders()
					await asyncio.sleep(.005)
				except Exception as e:
					print("main() loop: ",e)
					continue
			self.loop.stop()

#==========================================================================
# Test serial asyncio implementation and shutdown

if __name__ == '__main__':
	start=0
	end=0
	count = 0
	enc1 = 0
	enc2 = 0
	try:
		encoders = Encoders()
		encoders.start()
		while True:
			if count >= 10:
				count = 0
				encoders.clearCounts()
			start = time.time()
			enc1, enc2 = encoders.getCounts()
			end = time.time() - start
			print("counts: ", enc1, enc2)
			print("request time", end)
			time.sleep(.01)
			count+=1
	except Exception as e:
		print('[!] Caught Exception: ', e)
	finally:
		encoders.stop()
		exit()