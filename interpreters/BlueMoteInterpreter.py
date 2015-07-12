import bluetooth
import time
import socket
import select

# Implementation of the interpreter to 
# handle communications with the BlueMote
# server and the HomePi. The idea is 
# to have an app implemeting the BlueMote
# protocol connect to the Raspberry Pi 
# instead of directly to the server. 
# The goal is to unify all the controls 
# into a single app. 
# As a result since the app already 
# talks the protocol of the server all
# this interpreter does is forward the
# commands to the server. 

class BlueMoteInterpreter(object):

	# Device to interact with
	server = None

	# Socket to send data to server
	bmSocket = None

	# Port
	bmPort = 1

	# Host
	bmHost = ''

	# Time out in seconds, useful for knowing 
	# when the operation is hangin due to a socket
	# loss.
	TIME_OUT = 5 

	# Hibernate command
	COMMAND_HIBERNATE = 'COMPUTER_HIBERNATE'

	# Constructor
	def __init__(self, blueMoteServer):
		self.server = blueMoteServer
		
		self.createSocket()
	
	# Helper Method.
	# Creates a new Socket and attempts to find
	# the service for it.
	def createSocket(self):
		self.bmSocket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
		self.bmSocket.settimeout(None)

		#self.bmPort = bluetooth.PORT_ANY
		services = bluetooth.find_service(uuid='1d374b6f-4e12-4126-abec-5e92daf7c434', address=self.server.getDeviceMac())
		if len(services) > 0:
			match = services[0]
			self.bmPort = match['port']
			self.bmHost = match['host']
		
	# REQUIRED
	# Attempts to establish a connection with the
	# device. In the event it fails it returns 
	# a negative value to indicate failure.
	def connect(self):
		# Do some exception handling here.
		try :
			# If there is no socket
			# probably something went wrong 
			# during the creation so try to 
			# create it again before connecing.
			if self.bmSocket == None:
				self.createSocket()
	
			#self.bmSocket.connect((self.server.getDeviceMac(), self.bmPort))		
			self.bmSocket.connect((self.bmHost, self.bmPort))
			print 'SUCCESS: Connected to {0} - BlueMote'.format(self.server.getDeviceId())
			#time.sleep(10)
			return 0
		except bluetooth.btcommon.BluetoothError as btErr:
			print btErr
			print 'FAIL: {0}:{1} - Error trying to connect to BlueMote server. Make sure the Raspberry Pi is paired with it and that the server is running.'.format(self.server.getDeviceId(), self.server.getDeviceMac())
			self.bmSocket = None
			return -1

	# REUIQRED
	# Attempts to disconnect from the device
	def disconnect(self):
		self.bmSocket.close();
		print 'Disconnected from {0} -  BlueMote'.format(self.server.getDeviceId())

	# REQUIRED
	# Attempts to perform the command on
	# the connected device. If the 
	# command fails it return a negative
	# number to indicate failure.
	# Note: This interpreter sits
	# as an intermediary between the 
	# BlueMote App and the BlueMote server
	# so interpreter simply forward 
	# the commands received directly
	# To the server and performs no other
	# parsing. 
	def handleData(self, dataStr):
		
		# Sometimes commands are recevied back to 
		# back on the same line regardless of the new
		# line. For now, we just take the first command
		# and ignore the rest.
		#print 'Data'
		dataStr = dataStr.split('\n',1)[0]
		dataStr = '{0}{1}'.format(dataStr, '\n')
		msgLen = len(dataStr)
		totalSent = 0
		self.bmSocket.settimeout(self.TIME_OUT)
		# If we receive the Hibernate Command
		# the remote server will be put to hibernate
		# causing a loss in the connection. So
		# let's signal the device disconnected
		# right after sending the message.
		disconnectOnSend = False
		if self.COMMAND_HIBERNATE in dataStr:
			disconenctOnSend = True
			# Prevent PC from Hibernating
			# for testing.
			#return - 1
		
		try:
			while totalSent < msgLen:

				bytesSent = self.bmSocket.send(dataStr[totalSent:])
				if bytesSent == 0:
					return -1

				totalSent = totalSent + bytesSent

		except socket.timeout as t:
			self.bmSocket = None
			return -1
		except Exception as ex:
			#print 'Caught it {0}'.format(type(ex))
			# if we have any issues writing to the 
			# socket it must mean the end point must
			# be down. 
			self.bmSocket = None
			return -1
		

		if disconnectOnSend:
			return -1

		return 0 

	# REQUIRED
	# Attempts to receive data from the device.
	# It returns the data received.
	def receiveData(self):
		data = self.bmSocket.recv(1024)
		return data
