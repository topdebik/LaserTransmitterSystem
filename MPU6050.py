#-*- coding: utf-8 -*-

import smbus
import math

class MPU6050:
	def __init__(self, bus = 1):
		self.PWR_M = 0x6B
		self.DIV = 0x19
		self.CONFIG = 0x1A
		self.GYRO_CONFIG = 0x1B
		self.INT_EN = 0x38
		self.ACCEL_X = 0x3B
		self.ACCEL_Y = 0x3D
		self.ACCEL_Z = 0x3F
		self.GYRO_X = 0x43
		self.GYRO_Y = 0x45
		self.GYRO_Z = 0x47
		self.TEMP = 0x41
		self.BUS = smbus.SMBus(bus)
		self.DEVICE_ADDRESS = 0x68
		self.AxCal=0
		self.AyCal=0
		self.AzCal=0
		self.GxCal=0
		self.GyCal=0
		self.GzCal=0
		self.BUS.write_byte_data(self.DEVICE_ADDRESS, self.DIV, 7)
		self.BUS.write_byte_data(self.DEVICE_ADDRESS, self.PWR_M, 1)
		self.BUS.write_byte_data(self.DEVICE_ADDRESS, self.CONFIG, 0)
		self.BUS.write_byte_data(self.DEVICE_ADDRESS, self.GYRO_CONFIG, 24)
		self.BUS.write_byte_data(self.DEVICE_ADDRESS, self.INT_EN, 1)

	def read(self, addr):
		high = self.BUS.read_byte_data(self.DEVICE_ADDRESS, addr)
		low = self.BUS.read_byte_data(self.DEVICE_ADDRESS, addr + 1)
		value = ((high << 8) | low)
		if(value > 32768):
			value = value - 65536
		return value

	def getGyro(self):
		x = self.read(self.ACCEL_X)
		y = self.read(self.ACCEL_Y)
		z = self.read(self.ACCEL_Z)
		return round(math.degrees(math.atan2(y, math.sqrt((x * x)+(z * z)))), 2), round(-math.degrees(math.atan2(x, math.sqrt((y * y)+(z * z)))), 2)

	def getAccel(self):
		x = self.read(self.GYRO_X)
		y = self.read(self.GYRO_Y)
		z = self.read(self.GYRO_Z)
		return round((x / 131.0 - self.GxCal), 2), round((y / 131.0 - self.GyCal), 2), round((z / 131.0 - self.GzCal), 2)


	def getTemp(self):
		tempRow = self.read(self.TEMP)
		tempC = (tempRow / 340.0) + 18.53
		tempC = float("%.2f" % tempC)
		return tempC

	def calibrate(self):
		x=0
		y=0
		z=0
		for i in range(50):
			x = x + self.read(self.ACCEL_X)
			y = y + self.read(self.ACCEL_Y)
			z = z + self.read(self.ACCEL_Z)
		x = x / 50
		y = y / 50
		z = z / 50
		self.AxCal = x / 16384.0
		self.AyCal = y / 16384.0
		self.AzCal = z / 16384.0
		x=0
		y=0
		z=0
		for i in range(50):
			x = x + self.read(self.GYRO_X)
			y = y + self.read(self.GYRO_Y)
			z = z + self.read(self.GYRO_Z)
		x = x / 50
		y = y / 50
		z = z / 50
		self.GxCal = x / 131.0
		self.GyCal = y / 131.0
		self.GzCal = z / 131.0