#! /usr/bin/python3

import os
import json
from tornado.websocket import WebSocketHandler
from tornado.web import Application, RequestHandler, StaticFileHandler
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from serial import Serial, SerialException, SerialTimeoutException
from time import sleep, time

serial = Serial('/dev/ttyACM0', 115200, timeout=.1)

# To do: Simple Login
# https://www.tornadoweb.org/en/stable/guide/security.html

def sendToArduino(ws,message):
	parsed={}
	try:
		parsed = json.loads(message)	
	except Exception as e:
		print(type(e),e)
		pass
	if 'set' in parsed or 'goto' in parsed:
		serial.write(bytes(message,'utf-8'))
	if 'get' in parsed and parsed['get'] == "all":
		serial.write(bytes(message,'utf-8'))
		sleep(.5)
		data = []
		while True:
			line = serial.readline().decode('utf-8').rstrip()
			if line:
				data.append(line)
			else:
				break
		if len(data) > 0:
			for entry in data:
				try:
					response = json.loads(entry)
					ws.write_message(entry)
				except Exception as e:
					print(type(e),e)
					pass
	

def constrain( _val, _min, _max):
	return min(_max, max(_min,_val))

class MainHandler(RequestHandler):
	def prepare(self):
		if self.request.protocol == "http":
			self.redirect("https://%s" % self.request.full_url()[len("http://"):], permanent=True)
	def get(self):
		 print ("[HTTP](MainHandler) User Connected.")
		 self.render("index.html")

class WSHandler(WebSocketHandler): 
	def open(self):
		print ('[WS] Connection was opened.')
	def on_close(self):
		print ('[WS] Connection was closed.')
	def on_message(self, message):
		sendToArduino(self, message)

class DefaultHandler(RequestHandler):
	def prepare(self):
		self.set_status(404)
		# self.render("404.html")

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
		print ("[+] Valence Server started")
		main_loop.start()
	except Exception as e:
		# Ooops message
		print ("[!] Exception raised: ",type(e), e)
	finally:
		print()
		print ("[+] Have a nice day! :)")
		exit()
#End of Program
