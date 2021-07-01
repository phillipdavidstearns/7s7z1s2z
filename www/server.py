#! /usr/bin/python3

import os
import json
from tornado.websocket import WebSocketHandler
from tornado.web import Application, RequestHandler, StaticFileHandler
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from serial import Serial, SerialException, SerialTimeoutException
from time import sleep

# Tonado server port
PORT = 80

def constrain( _val, _min, _max):
	return min(_max, max(_min,_val))

class MainHandler(RequestHandler):
	def get(self):
		 print ("[HTTP](MainHandler) User Connected.")
		 self.render("index.html")

class WSHandler(WebSocketHandler): 
	def open(self):
		print ('[WS] Connection was opened.')
	def on_close(self):
		print ('[WS] Connection was closed.')
	def on_message(self, message):
		# change to json parsing
		# message = json.loads(message)
		print ('[WS] Incoming message:', message)

class DefaultHandler(RequestHandler):
	def prepare(self):
		self.set_status(404)
		self.render("404.html")

def make_app():
	settings = dict(
		template_path = os.path.join(os.path.dirname(__file__), 'templates'),
		static_path = os.path.join(os.path.dirname(__file__), 'static'),
		default_handler_class=DefaultHandler,
		debug=True
	)
	urls = [
		(r'/', MainHandler),
		(r'/ws', WSHandler),
	]
	return Application(urls, **settings)

if __name__ == "__main__":
	try:
		serial = Serial('/dev/ttyACM0', 115200, timeout=.1)
		application = make_app()
		application.listen(PORT)
		http_server = HTTPServer(application,
			# ssl_options = {
			#   "certfile":"/etc/letsencrypt/live/milkandhoneylabs.com/fullchain.pem",
			#   "keyfile":"/etc/letsencrypt/live/milkandhoneylabs.com/privkey.pem"
			# }
		)
		# http_server.listen(443)
		main_loop = IOLoop.instance()
		print ("Tornado Server started")
		main_loop.start()
	except Exception as e:
		# Ooops message
		print ("Exception raised: ", e)
	finally:
		print ("Have a nice day! :)")
		exit()
#End of Program
