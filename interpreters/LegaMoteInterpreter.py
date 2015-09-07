import bluetooth
import time
import socket

# Implementation of the interpreter to
# handle communications with the LegaMote
# server and the HomePi. This implementation
# is more straight forward as all we will do
# is forward the commands as the come to the
# LegaMote server running on Arduino. HomePi
# will receive all the commands and strip
# away anything specific to the HomePi protocol
# and send thus the reminder. This remainder 
# will be a command in LegMote protocol so
# we just forward it to the LegaMote server.

class LegaMoteInterpreter(object):

	# Device to interact with
	server = None

	# Socket to send data to the server
	lmSocket = None

	# Port
	lmPort = 1

	# Host
	lmHost = ''

	# Socket time out time in secods
	TIME_OUT = 5

	# Constructor
	def __init__(self, legaMoteServer):
		self.server = legaMoteServer

		self.createSocket()

	# Helper Method
	# Creates a new Socket and attempts to
	# find the service fo it.
	def createSocket(self):
		self.lmSocket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
		self.lmSocket.settimeout(None)

		# We communicate with LegaMore via SPP
		services = bluetooth.find_service(uuid='00001101-0000-1000-8000-00805F9B34FB', address=self.server.getDeviceMac())
		if len(services) >0:
			match = services[0]
			self.lmPort = match['port']
			self.lmHost = match['host']

	# REQUIRED
	# Attempts to establish a connection with the device.
	# In the event it fails it returns a negative value
	# to indicate failure.
	def connect(self):
		# Do some exception handling here.
		try :
			# If there is no socket
			# probably something went wrong
			# during creation so try 
			# to create it again before 
			# connecting.
			if self.lmSocket == None:
				self.createSocket()

			self.lmSocket.connect((self.lmHost, self.lmPort))
			print 'SUCCESS: Connected to {0} - LegaMote'.format(self.server.getDeviceId())

			return 0

		except bluetooth.btcommon.BluetoothError as btErr:
			print btErr
			print 'FAIL: {0}:{1} - Error trying to connect to LegMote server. Make sure the Raspberry Pi is paired with it and that the server is running.'.format(self.server.getDeviceId(), self.server.getDeviceMac())
			self.lmSocket = None
			return -1

	# REQUIRED
	# Attempts to disconnect from the device
	def disconnect(self):
		self.lmSocket.close()
		print 'Disconnected from {0} - LegaMote'.format(self.server.getDeviceId())

	
	# REQUIRED
	# Attempts to perform the command on 
	# the connected device. If the command
	# fails it returns a negative number.
	# Note: This interpreter simply sits as 
	# an intermediary between the LegaMote app
	# talking to HomePi and the LegaMote server
	# so it simply forwards the command to the
	# LegaMote server directly.
	# It does not perform any additional work.
	def handleData(self, dataStr):

		# We don't do anything if there 
		# is no command.
		if len(dataStr) < 1:
			return 0
		
		# Commands in the LegaMote are
		# two characters long. 
		# A command character and 
		# the new line chracter.
		# So we are just going to take 
		# the first character of the dataStr
		# and send it with the '\n' character.
		dataStr = '{0}{1}'.format(dataStr[0], '\n')
		msgLen = len(dataStr)
		self.lmSocket.settimeout(self.TIME_OUT)
		totalSent = 0
		try:

			while totalSent < msgLen:
				bytesSent = self.lmSocket.send(dataStr[totalSent:])
				if bytesSent == 0:
					return -1

				totalSent = totalSent + bytesSent


		except socket.timeout as t:
			print 'LegaMote - Time out'
			self.lmSocket = None
			return -1

		except Exception as ex:
			print 'LegaMote - Caught it {0}'.format(type(ex))
			# If we have any issues writing to
			# the socket it must mean the end
			# point must be down.
			self.lmSocket = None
			return -1

		return 0

	# REQUIRED
	# Attempts to receive data form the device.
	# It returns the data received.
	def receiveData(self):
		data = self.lmSocket.recv(1024)
		return data;

	

		

