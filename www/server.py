#!/usr/bin/python3

import os
import sys
import json
import signal
from tornado.websocket import WebSocketHandler
from tornado.web import authenticated, Application, RequestHandler, StaticFileHandler
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from time import sleep
from motor_controller import MotorController
from hashlib import sha256

cookie_secret=open("/usr/local/etc/valence/cookie_secret",'r').read().strip()
credentials=open("/usr/local/etc/valence/credentials",'r').read().strip()

class BaseHandler(RequestHandler):
	def get_current_user(self):
		return self.get_secure_cookie("valence_user",max_age_days=1)

class LoginHandler(BaseHandler):
	def get(self):
		self.render("login.html")
	def post(self):
		username = self.get_argument("username")
		password = self.get_argument("password")
		submitted_credentials = username+":"+password
		hashed_credentials = sha256(submitted_credentials.encode('utf-8')).hexdigest()
		if hashed_credentials == credentials:
			print("[+] Successful Authentication")
			self.set_secure_cookie("valence_user", self.get_argument("username"),expires_days=1)
		else:
			print("[!] Failed Authentication Attempt")
		self.redirect(self.get_argument("next", "/"))

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("valence_user")
        self.redirect(self.get_argument("next", "/"))

class MainHandler(BaseHandler):
	def prepare(self):
		if self.request.protocol == "http":
			print ("[+] HTTP user connected.")
			self.redirect("https://%s" % self.request.full_url()[len("http://"):], permanent=True)
	@authenticated
	def get(self):
		 print ("[+] HTTP session upgraded to HTTPS.")
		 self.render("index.html")

class WSHandler(WebSocketHandler):
	def open(self):
		print ('[+] WS connection was opened.')
	def on_close(self):
		print ('[+] WS connection was closed.')
	async def on_message(self, message): # send WebSocket object and message to MotorController
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
	mc.goto(3) # Go to CLOSE
	while not MotorController.machineState == 4: # Wait for MotorController to reach CLOSE_HOLD
		sleep(0.1)
	print('[+] Stopping MotorController.')
	MotorController.stop()

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
		mc.start()
		# Build the web application and HTTP server
		application = make_app()
		application.listen(80)
		http_server = HTTPServer(application,
			ssl_options = {
			  "certfile":"/etc/ssl/certs/valence.crt",
			  "keyfile":"/etc/ssl/certs/valence.key"
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
