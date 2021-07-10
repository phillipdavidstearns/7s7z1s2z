#! /usr/bin/python3

import os
import sys
import json
import signal
from tornado.websocket import WebSocketHandler
from tornado.web import Application, RequestHandler, StaticFileHandler
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from time import sleep, time
from motor_controller import MotorController

# To do: Simple Login
# https://www.tornadoweb.org/en/stable/guide/security.html

class MainHandler(RequestHandler):
	def prepare(self):
		if self.request.protocol == "http":
			print ("[+] HTTP user connected.")
			self.redirect("https://%s" % self.request.full_url()[len("http://"):], permanent=True)
	def get(self):
		 print ("[+] HTTP session upgraded to HTTPS.")
		 self.render("index.html")

class WSHandler(WebSocketHandler): 
	def open(self):
		print ('[+] WS connection was opened.')
	def on_close(self):
		print ('[+] WS connection was closed.')
	def on_message(self, message):
		mc.send(message,self)

class DefaultHandler(RequestHandler):
	def prepare(self):
		self.set_status(404)

def make_app():
	settings = dict(
		template_path = os.path.join(os.path.dirname(__file__), 'templates'),
		static_path = os.path.join(os.path.dirname(__file__), 'static'),
		default_handler_class=DefaultHandler,
		debug=False
	)
	urls = [
		(r'/', MainHandler),
		(r'/ws', WSHandler),
		(r'/(favicon\.ico)', StaticFileHandler)
	]
	return Application(urls, **settings)

if __name__ == "__main__":
	try:
		application = make_app()
		application.listen(80)
		http_server = HTTPServer(application,
			ssl_options = {
			  "certfile":"/etc/ssl/certs/valence.crt",
			  "keyfile":"/etc/ssl/certs/valence.key"
			}
		)
		http_server.listen(443)
		main_loop = IOLoop.instance()
		
		mc = MotorController()
		mc.start()
		
		def signalHandler(signum, frame):
			print('[!] Caught termination signal: ', signum)
			main_loop.stop()
			mc.stop()
			sys.exit()
		
		signal.signal(signal.SIGINT, signalHandler)
		signal.signal(signal.SIGTERM, signalHandler)
		signal.signal(signal.SIGHUP, signalHandler)
		print ("[+] Valence Server started")
		main_loop.start()
	except Exception as e:
		print ("[!] Exception raised: ",type(e), e)
	finally:
		print ("[+] Have a nice day! :)")
		sys.exit()
#End of Program
