#-*- coding: utf-8 -*-

import RPi.GPIO as gpio
from time import sleep
from errors import keyNotInAlfabetError
import math

def turnOnLaser(pin):
	gpio.output(pin, gpio.LOW)
	return

def turnOffLaser(pin):
	gpio.output(pin, gpio.HIGH)
	return

def turnOnFan(pin):
	gpio.output(pin, gpio.HIGH)
	return

def turnOffFan(pin):
	gpio.output(pin, gpio.LOW)
	return

def moveZRight(servoZPin, servoZFreq1, servoZFreq, servoZ):
	servoZFreq1 = servoZFreq + 0.1
	if 1.5 <= servoZFreq1 <= 11.5:
		servoZFreq = servoZFreq1
	servoZ.ChangeDutyCycle(round(servoZFreq, 1))
	return

def moveZLeft(servoZPin, servoZFreq1, servoZFreq, servoZ):
	servoZFreq1 = servoZFreq - 0.1
	if 1.5 <= servoZFreq1 <= 11.5:
		servoZFreq = servoZFreq1
	servoZ.ChangeDutyCycle(round(servoZFreq, 1))
	return

def fanActivate(mpu, pin):
	while True:
		print(f"\033[33mTemperature: {mpu.getTemp()}\033[37m")
		if mpu.getTemp() >= 40:
			gpio.output(pin, gpio.HIGH)
		else:
			gpio.output(pin, gpio.LOW)
		sleep(60)

def stabilize(mpu, servoXPin, servoYPin, xOffset, servoXFreq1, servoYFreq1, servoXFreq, servoYFreq):
	global servoX
	gpio.setup(servoXPin, gpio.OUT)
	gpio.setup(servoYPin, gpio.OUT)
	servoX = gpio.PWM(servoXPin, 50)
	servoY = gpio.PWM(servoYPin, 50)
	servoX.start(servoXFreq)
	servoY.start(servoYFreq)
	while True:
		x, y = mpu.getGyro()
		x, y = round(x) + xOffset, round(y)
		servoXFreq1 = servoXFreq + (0.01 * math.copysign(1, x))
		servoYFreq1 = servoYFreq + (0.01 * math.copysign(1, y))
		if 1.5 <= servoXFreq1 <= 11.5:
			servoXFreq = servoXFreq1
		if 1.5 <= servoYFreq1 <= 11.5:
			servoYFreq = servoYFreq1
		if  servoXFreq <= 11.5 and servoXFreq >= 1.5 and servoYFreq <= 11.5 and servoXFreq >= 1.5:
			servoX.ChangeDutyCycle(round(servoXFreq, 2))
			servoY.ChangeDutyCycle(round(servoYFreq, 2))
		sleep(0.005)

def calibrate(adc, channel = 0):
	values = []
	for i in range(100):
		values.append(adc.read(channel))
		sleep(0.01)
	sr = sum(values) // len(values)
	return sr

def convertToText(data, sr, alfKeys):
	for i in range(len(data)):
		if sr - 300 < data[i] < sr + 300:
			data[i] = "0"
		elif not (sr - 300 < data[i] < sr + 300):
			data[i] = "1"
	print(*data, sep = "")
	while data[-1] != "1":
		data.pop(-1)
	while data[-1] != "0":
		data.pop(-1)
	data.pop(-1)
	print(*data, sep = "")
	convertedData = []
	symbol = ""
	for i in range(-1, -len(data), -1):
		if i % 9 == 0:
			symbol = data[i] + symbol
			convertedData.append(symbol)
			symbol = ""
		else:
			symbol = data[i] + symbol
	for i in range(len(convertedData)):
		try:
			convertedData[i] = alfKeys[convertedData[i]]
		except KeyError:
			convertedData[i] = "?"
	print("".join(convertedData)[::-1])
	return "".join(convertedData)[::-1]

def transmit(data, pin, alfKeys, speed = 20):
	speed = 1 / speed
	correction = speed / 180
	data1 = data.strip()
	data = []
	for i in data1:
		if i not in list(alfKeys.values()):
			return keyNotInAlfabetError(i)
	data1 = list(data1)
	for i in range(len(data1)):
		for f in list(alfKeys.keys())[list(alfKeys.values()).index(data1[i])]:
			data.append(f)
	for i in range(3):
		data.insert(0, "1")
	data.append("0")
	data.append("1")
	print(*data, sep = "")
	print(f"beginning transmittion: {len(data)} bytes")
	for i in data:
		if i == "1":
			gpio.output(pin, gpio.LOW)
			sleep(speed + correction)
		elif i == "0":
			gpio.output(pin, gpio.HIGH)
			sleep(speed + correction)
	gpio.output(pin, gpio.HIGH)
	return

def recieve(adc, sr, alfKeys, messagesList, speed = 20, channel = 0):
	speed = 1 / speed
	while True:
		while True:
			if adc.read(channel) + 300 < sr:
				print("detected input")
				break
		repeatingElement = 0
		data = [sr, sr]
		sleep(speed / 3)
		while repeatingElement < 10:
			byte = adc.read(channel)
			data.append(byte)
			print(byte)
			if (data[-2] - 300 < byte < data[-2] + 300) and (sr - 300 < byte < sr + 300):
				repeatingElement += 1
			else:
				repeatingElement = 0
			sleep(speed)
		print("recieve completed")
		messagesList.append(convertToText(data, sr, alfKeys))