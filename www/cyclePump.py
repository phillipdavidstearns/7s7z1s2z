import pigpio
from time import sleep

GPIO = pigpio.pi()

PUMP_PWM_PIN=21

GPIO.set_PWM_frequency(4,8000)
GPIO.set_PWM_dutycycle(PUMP_PWM_PIN, 0)

def setPumpSpeed(value):
	GPIO.set_PWM_dutycycle(PUMP_PWM_PIN, int(value*255))


if __name__ == "__main__":
	step = .01
	brightness = 0
	direction = True
	try:
		
		while True:
			
			if direction:
				brightness += step
			else:
				brightness -= step

			if direction and brightness >= 1.0:
				brightness = 1.0
				direction = False
			elif not direction and brightness <= 0.0: 
				brightness = 0.0
				direction = True

			
			setPumpSpeed(brightness)
			print("brightness: " , brightness)
			sleep(.1)
	except Exception as e:
		print("Exception: ",e)
	finally:
		exit()
