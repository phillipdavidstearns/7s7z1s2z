#!/usr/bin/python3

import os
import sys
import json
import signal
from tornado.websocket import WebSocketHandler
from tornado.web import authenticated, Application, RequestHandler, StaticFileHandler
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from time import sleep, time
from motor_controller import MotorController
from hashlib import sha256

cookie_secret=open("/usr/local/etc/7s7z1s2z/cookie_secret",'r').read().strip()
credentials=json.load(open("/usr/local/etc/7s7z1s2z/credentials.json",'r'))

class BaseHandler(RequestHandler):
	def get_current_user(self):
		return self.get_secure_cookie("7s7z1s2z",max_age_days=1)

class LoginHandler(BaseHandler):
	def get(self):
		self.render("login.html")
	def post(self):
		username = self.get_argument("username")
		if username in credentials['users']:
			password = self.get_argument("password")
			submitted_credentials = username+":"+password
			hashed_credentials = sha256(submitted_credentials.encode('utf-8')).hexdigest()
			if hashed_credentials == credentials['users'][username]:
				print("[+] Successful Authentication")
				self.set_secure_cookie("7s7z1s2z", username, expires_days=1)
			else:
				print("[!] Failed Authentication Attempt")
		else:
			print("[!] Invalid User: ", username)
		print("[*] Redirecting to /")
		self.redirect(self.get_argument("next", "/"))

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("7s7z1s2z")
        self.redirect(self.get_argument("next", "/"))

class MainHandler(BaseHandler):
	def prepare(self):
		if self.request.protocol == "http":	
			print ("[+] HTTP user connected.")
			self.redirect("https://%s" % self.request.full_url()[len("http://"):], permanent=True)
	@authenticated
	def get(self):
		print ("[+] HTTP session upgraded to HTTPS.")
		print ("[+] Current user: ", self.current_user)
		user = self.current_user.decode('utf-8')
		if user == 'valence':
			self.render("calibrate.html")	
		elif user == 'SFMOMA':
			self.render("operate.html")
		
class WSHandler(WebSocketHandler):
	def open(self):
		print ('[+] WS connection was opened.')
	def on_close(self):
		print ('[+] WS connection was closed.')
	async def on_message(self, message): # send WebSocket object and message to MotorController
		parsed = json.loads(message)
		if 'poweroff' in parsed and parsed['poweroff']:
			if sha256(parsed['poweroff'].encode('utf-8')).hexdigest() == credentials['poweroff']:
				await self.write_message(json.dumps({'poweroff':True}))
				self.close()
				poweroff()
			else:
				await self.write_message(json.dumps({'poweroff':False}))
		elif 'reboot' in parsed and parsed['reboot']:
			if sha256(parsed['reboot'].encode('utf-8')).hexdigest() == credentials['reboot']:
				await self.write_message(json.dumps({'reboot':True}))
				self.close()
				reboot()
			else:
				await self.write_message(json.dumps({'reboot':False}))
		else:
			await mc.websocket(self, message)

class DefaultHandler(RequestHandler):
	def prepare(self):
		self.set_status(404)

def make_app():
	settings = dict(
		template_path = os.path.join(os.path.dirname(__file__), 'templates'),
		static_path = os.path.join(os.path.dirname(__file__), 'static'),
		cookie_secret = cookie_secret,
		default_handler_class = DefaultHandler,
		login_url = "/login",
		debug = False
	)
	urls = [ # routing
		(r'/', MainHandler),
		(r'/ws', WSHandler),
		(r'/login', LoginHandler),
		(r'/logout', LogoutHandler),
		(r'/(favicon\.ico)', StaticFileHandler)
	]
	return Application(urls, **settings)

def waitUntilClosed(MotorController):
	if MotorController.machineState == -2:
		return True
	else:
		startTime = time()
		timeout = 30
		timeoutFlag = False
		MotorController.goto(3) # Go to CLOSE
		while not MotorController.machineState == 4 and not timeoutFlag: # Wait for MotorController to reach CLOSE_HOLD
			if time()-startTime >= timeout:
				timeoutFlag=True
				print('[!] Timed out waiting for close after %s seconds' % timeout)
			sleep(0.1)
		print('[+] Stopping MotorController.')
		MotorController.stop()
		return True

def poweroff():
		print('[!] Power off')
		print('[*] Shutting down HTTPServer.')
		http_server.stop()
		print('[*] Waiting for MotorController to reach CLOSED state.')
		waitUntilClosed(mc)
		print('[*] Stopping IOLoop.')
		main_loop.stop()
		print('[*] Powering off')
		os.system('sudo shutdown -h now')

def reboot():
		print('[!] Reboot')
		print('[*] Shutting down HTTPServer.')
		http_server.stop()
		print('[*] Waiting for MotorController to reach CLOSED state.')
		waitUntilClosed(mc)
		print('[*] Stopping IOLoop.')
		main_loop.stop()
		print('[*] Rebooting')
		os.system('sudo reboot')

if __name__ == "__main__":

	# signal callback for handling HUP, INT and TERM signals
	def signalHandler(signum, frame):
		print('[!] Caught termination signal: ', signum)
		print('[*] Shutting down HTTPServer.')
		http_server.stop()
		print('[*] Waiting for MotorController to reach CLOSED state.')
		waitUntilClosed(mc)
		print('[*] Stopping IOLoop.')
		main_loop.stop()
		sys.exit()

	signal.signal(signal.SIGINT, signalHandler)
	signal.signal(signal.SIGTERM, signalHandler)
	signal.signal(signal.SIGHUP, signalHandler)

	try:
		# Instantiate the MotorController and start it 
		mc = MotorController()
		mc.DEBUG = True
		mc.run()
		# Build the web application and HTTP server
		application = make_app()
		application.listen(80)
		http_server = HTTPServer(application,
			ssl_options = {
			  "certfile":"/etc/ssl/certs/7s7z1s2z.crt",
			  "keyfile":"/etc/ssl/certs/7s7z1s2z.key"
			}
		)
		http_server.listen(443)
		main_loop = IOLoop.current()
		print ("[+] Valence Server started")
		main_loop.start()
	except Exception as e:
		print ("[!] Exception raised: ",type(e), e)
	finally:
		print ("[+] Have a nice day! :)")
#End of Program
