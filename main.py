#-*- coding: utf-8 -*-

from MCP3008 import MCP3008
from MPU6050 import MPU6050
import comm
import json
import RPi.GPIO as gpio
from threading import Thread, Condition
from multiprocessing import Process, Manager
from http.server import BaseHTTPRequestHandler, HTTPServer
from ast import literal_eval
from time import sleep
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder, Quality
from picamera2.outputs import FileOutput
import io

class StreamingOutput(io.BufferedIOBase):
	def __init__(self):
		self.frame = None
		self.condition = Condition()
	
	def write(self, buf):
		with self.condition:
			self.frame = buf
			self.condition.notify_all()

class ServerHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		if "messages" not in self.path:
			print("GET request, path:", self.path)
		if self.path:
			self.send_response(200)
			if "?" in self.path or self.path == "/":
				self.send_header("Content-type", "text/html")
				self.end_headers()                
				self.wfile.write(open("server/index.html").read().encode("utf-8"))
			elif "favicon" in self.path:
				self.send_header("Content-type", "image/x-icon")
				self.end_headers()
				self.wfile.write(open("server/favicon.png", "rb").read())
			elif "messages" in self.path:
				self.send_header("Content-type", "text/plain")
				self.end_headers()
				global incomingMessages, incomingSentMessages
				a = list(incomingMessages)
				b = list(incomingSentMessages)
				for i in b:
					a.remove(i)
				if a == []:
					self.wfile.write("None".encode("utf-8"))
				else:
					self.wfile.write("PADDING".join(a).encode("utf-8"))
					incomingSentMessages = list(incomingMessages)
			elif "style" in self.path:
				self.send_header("Content-type", "text/css")
				self.end_headers()                
				self.wfile.write(open(self.path[1:]).read().encode("utf-8"))
			elif "stream.mjpg" in self.path:
				self.send_response(200)
				self.send_header("Age", 0)
				self.send_header("Cache-Control", "no-cache, private")
				self.send_header("Pragma", "no-cache")
				self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=FRAME")
				self.end_headers()
				try:
					while True:
						with output.condition:
							output.condition.wait()
							frame = output.frame
						self.wfile.write(b"--FRAME\r\n")
						self.send_header("Content-Type", "image/jpeg")
						self.send_header("Content-Length", len(frame))
						self.end_headers()
						self.wfile.write(frame)
						self.wfile.write(b"\r\n")
				except Exception as e:
					print("\033[31mRemoved streaming client {}: {}\033[37m".format(self.client_address, str(e)))
			else:
				self.send_header("Content-type", "text/html")
				self.end_headers()                
				self.wfile.write(open(self.path[1:]).read().encode("utf-8"))
		else:
			self.send_error(404, "Page Not Found {}".format(self.path))

	def do_POST(self):
		global laserPin, fanPin, incomingMessages, incomingSentMessages, servoZFreq1, servoZFreq, servoXFreq1, servoYFreq1, servoXFreq, servoYFreq, servoZPin, xOffset, servoZ
		content_length = int(self.headers["Content-Length"])
		body = self.rfile.read(content_length)
		print("POST request, path:", self.path, "body:", body.decode("utf-8"))
		try:
			self.send_response(200)
			if "message" in self.path:
				message = literal_eval(body.decode("utf-8"))
				transmitMessage = Process(target = comm.transmit, args = (message["message"], laserPin, alfKeys))
				transmitMessage.start()
			else:
				if "turnOnLaser" in self.path:
					comm.turnOnLaser(laserPin)
					print("\033[32mTurning Laser On\033[37m")
				elif "turnOffLaser" in self.path:
					comm.turnOffLaser(laserPin)
					print("\033[32mTurning Laser Off\033[37m")
				elif "turnOnFan" in self.path:
					comm.turnOnFan(fanPin)
					print("\033[32mTurning Fan On\033[37m")
				elif "turnOffFan" in self.path:
					comm.turnOffFan(fanPin)
					print("\033[32mTurning Fan Off\033[37m")
				elif "turnZRight" in self.path:
					comm.moveZRight(servoZPin, servoZFreq1, servoZFreq, servoZ)
					print("\033[32mMoving Z Right\033[37m")
				elif "turnZLeft" in self.path:
					comm.moveZLeft(servoZPin, servoZFreq1, servoZFreq, servoZ)
					print("\033[32mMoving Z Left\033[37m")
				elif "turnXDown" in self.path:
					xOffset -= 1
					print("\033[32mMoving X Down\033[37m")
				elif "turnXUp" in self.path:
					xOffset += 1
					print("\033[32mMoving X Up\033[37m")
				elif "calibrateGyro" in self.path:
					mpu.calibrate()
					print("\033[32mCalibrating Gyroscope\033[37m")
				elif "resetToDefaults" in self.path:
					xOffset = 0
					incomingMessages = []
					incomingSentMessages = []
					print("\033[32mResetting to defaults\033[37m")
		except Exception as err:
			print("\033[31mdo_POST exception: %s\033[37m" % str(err))    

def server_thread(port):
	global picam2, output
	server_address = ("", port)
	httpd = HTTPServer(server_address, ServerHandler)
	picam2 = Picamera2()
	picam2.configure(picam2.create_video_configuration(main = {"size": (1280, 720)}))
	picam2.set_controls({"FrameRate": 30.00})
	output = StreamingOutput()
	picam2.start_recording(JpegEncoder(), FileOutput(output), quality=Quality.MEDIUM)		
	try:	
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass

def main():
	global laserPin, fanPin, incomingMessages, incomingSentMessages, servoZFreq1, servoZFreq, servoXFreq1, servoYFreq1, servoXFreq, servoYFreq, servoZPin, xOffset, alfKeys, servoZ
	with open("alfKeys.json", "r") as fp:
		alfKeys = json.load(fp)
	gpio.setmode(gpio.BCM)
	laserPin = 4
	gpio.setup(laserPin, gpio.OUT)
	fanPin = 17
	gpio.setup(fanPin, gpio.OUT)
	servoXPin = 12
	servoYPin = 13
	servoZPin = 18
	servoZFreq1 = 12 / 2 + 1
	servoZFreq = servoZFreq1
	servoXFreq1 = 12 / 2 + 1
	servoYFreq1 = 12 / 2 + 1     
	servoXFreq = servoXFreq1
	servoYFreq = servoYFreq1
	gpio.setup(servoZPin, gpio.OUT)
	servoZ = gpio.PWM(servoZPin, 50)
	servoZ.start(servoZFreq)	
	xOffset = 0 
	incomingMessages = Manager().list()
	incomingSentMessages = []
	adc = MCP3008()
	mpu = MPU6050()
	TFan = Thread(target = comm.fanActivate, args = (mpu, fanPin))
	TStabilize = Thread(target = comm.stabilize, args = (mpu, servoXPin, servoYPin, xOffset, servoXFreq1, servoYFreq1, servoXFreq, servoYFreq))
	TServer = Process(target = server_thread, args = (8080, ))
	TFan.start()
	TStabilize.start()
	sleep(1)
	sr = comm.calibrate(adc)
	print(f"\033[33mCalibration: {sr}\033[37m")	
	TRecieve = Process(target = comm.recieve, args = (adc, sr, alfKeys, incomingMessages))	
	TRecieve.start()
	TServer.start()

if __name__ == "__main__":
	main()
