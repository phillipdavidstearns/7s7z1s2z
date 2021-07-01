from serial import Serial, SerialException, SerialTimeoutException
import json
from time import sleep, time
from random import randint

params = [
	"sigmoidFunction",
	"machineState",
	"lastMachineState",
	"mPositionOffsets",
	"isOpen",
	"isClosed",
	"moveMotors",
	"openDuration",
	"openHoldDuration",
	"closeDuration",
	"closeHoldDuration",
	"startupDuration",
	"target",
	"targetOpen",
	"targetClosed",
	"powerScalar",
	"powerEasing",
	"targetWindow",
	"powerLimit",
	"powerCutoff",
	"speedCutoff",
	"mPositions",
	"mSpeeds",
	"tCurrent",
	"tInitial",
	"tDuration",
	"tFinal"
]

variables = {
	"sigmoidFunction" : 2,
	"machineState" : 5,
	"lastMachineState" : 0,
	"mPositionOffsets" : [ 0, 0 ],
	"isOpen" : False,
	"isClosed" : False,
	"moveMotors" : True,
	"openDuration" : 15000,
	"openHoldDuration" : 15000,
	"closeDuration" : 12500,
	"closeHoldDuration" : 17500,
	"startupDuration" : 5000,
	"target" : 0,
	"targetOpen" : 2550,
	"targetClosed" : 0,
	"powerScalar" : 2.0,
	"powerEasing" : 1.0,
	"targetWindow" : 3,
	"powerLimit" : 480,
	"powerCutoff" : 25,
	"speedCutoff" : 0.01
}

def main():
	serial = Serial('/dev/ttyACM0', 115200, timeout=.1)
	timeout=1
	while True:
		command={}
		data = []
		command['get']="all"
		# command['set']=variables
		print("command: ",command)
		serial.write(bytes(json.dumps(command), 'utf-8'))
		now=time()
		start=now
		while now-start < timeout and serial.in_waiting > 0:
			now=time()
			pass

		while True:
			line = serial.readline().decode('utf-8').rstrip()
			if line:
				data.append(line)
			else:
				break
		if len(data) > 0:
			# print("len(data):",len(data),", data: ", data)
			for entry in data:
				try:
					received = json.loads(entry)
					print("received: ", received)
					# if 'message' in received:
					# 	serial.write(bytes(json.dumps(response), 'utf-8'))
					# else:
				except Exception as e:
					# print(type(e),e)
					pass
		sleep(1)
		
if __name__ == "__main__":
	try:
		print(time())
		main()
	except Exception as e:
		print(type(e)," : ",e)
	finally:
		exit()