from threading import Thread
from time import sleep

class myClassA(Thread):
	def __init__(self):
		self.message=""
		Thread.__init__(self)
		self.daemon = True
		self.start()
	def run(self):
		while True:
			if self.message:
				print("Got message: ",self.message)
				self.message=""
			else:
				print("A waiting for message")
				sleep(1)
			pass
	def send(self,message):
		self.message=message

a = myClassA()
while True:
	a.send("hello A")
	sleep(5)
