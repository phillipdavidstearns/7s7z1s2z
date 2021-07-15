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
from threading import Thread
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
		hashed_credentials = sha256(submitted_credentials.encode()).hexdigest()
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
	async def open(self):
		print ('[+] WS connection was opened.')
		await mc.websocket=self
	async def on_close(self):
		print ('[+] WS connection was closed.')
		await mc.websocket=None
	async def on_message(self, message):
		await mc.send(message)

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
	urls = [
		(r'/', MainHandler),
		(r'/ws', WSHandler),
		(r'/login', LoginHandler),
		(r'/logout', LogoutHandler),
		(r'/(favicon\.ico)', StaticFileHandler)
	]
	return Application(urls, **settings)

async def waitUntilClosed(MotorController):
	await mc.goto(3)
	await while not MotorController.machineState == 4:
		asyncio.sleep(0.1)
		pass
	print('[+] Stopping MotorController.')
	await MotorController.stop()

async def main():
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
	
	await mc = MotorController()
	await mc.start()
	
	def signalHandler(signum, frame):
		print('[!] Caught termination signal: ', signum)
		print('[*] Waiting for Valence to Close.')
		waitUntilClosed(mc)
		print('[*] Shutting down server.')
		main_loop.stop()
		sys.exit()

	signal.signal(signal.SIGINT, signalHandler)
	signal.signal(signal.SIGTERM, signalHandler)
	signal.signal(signal.SIGHUP, signalHandler)
	print ("[+] Valence Server started")
	main_loop.start()

if __name__ == "__main__":
	try:
		main()
	except Exception as e:
		print ("[!] Exception raised: ",type(e), e)
	finally:
		print ("[+] Have a nice day! :)")
#End of Program
