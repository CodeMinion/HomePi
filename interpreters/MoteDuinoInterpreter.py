import bluetooth
import time
import socket
import select
import threading

# Implementation of the interpreter to 
# handle communications with the MoteDuino
# server and the HomePi. The idea is 
# to have an app implementing the MoteDuino
# protocol connect to the Raspberry Pi 
# instead of directly to the server. 
# The goal is to unify all the controls 
# into a single app. 
# As a result since the app already 
# talks the protocol of the server all
# this interpreter does is forward the
# commands to the server. 

class MoteDuinoInterpreter(object):

	# Device to interact with
	server = None

	# Socket to send data to server
	bmSocket = None

	# Port
	bmPort = 1

	# Host
	bmHost = ''

	# Time out in seconds, useful for knowing 
	# when the operation is hanging due to a socket
	# loss.
	TIME_OUT = 5 

	# Have we sen't data since our last keep alive.
	mDataSentSinceKeepAlive = False
	
	# Time after which to send a Keep Alive
	KEEP_ALIVE_DELAY_IN_SECONDS = 60 * 60 * 2 

	# Keep alive timer
	mKeepAliveTimer = None
	
	# Constructor
	def __init__(self, moteDuinoServer):
		self.server = moteDuinoServer
		
		self.createSocket()
	
	# Helper Method.
	# Creates a new Socket and attempts to find
	# the service for it.
	def createSocket(self):
		self.bmSocket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
		self.bmSocket.settimeout(None)

                # We communicate with the MoteDuino server via SPP
		services = bluetooth.find_service(uuid='00001101-0000-1000-8000-00805F9B34FB', address=self.server.getDeviceMac())
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
			
			if self.server.requiresPair() and not self.server.isPaired():
				# Try to pair. HC-06 default pin: 1234
				self.server.pairDevice()
			
			# If there is no socket
			# probably something went wrong 
			# during the creation so try to 
			# create it again before connecing.
			if self.bmSocket == None:
				self.createSocket()
	
			self.bmSocket.connect((self.bmHost, self.bmPort))
			print 'SUCCESS: Connected to {0} - MoteDuino'.format(self.server.getDeviceId())
			#time.sleep(10)
			# Start Keep Alive
			self.keepAliveTimerHelper()
			#self.keepAlive()
			#self.mKeepAliveTimer.start()
			return 0
		except bluetooth.btcommon.BluetoothError as btErr:
			print btErr
			print 'FAIL: {0}:{1} - Error trying to connect to MoteDuino server. Make sure the Raspberry Pi is paired with it and that the server is running.'.format(self.server.getDeviceId(), self.server.getDeviceMac())
			self.bmSocket = None
			return -1

	# REUIQRED
	# Attempts to disconnect from the device
	def disconnect(self):
		self.mKeepAliveTimer.cancel()
		self.bmSocket.close();
		print 'Disconnected from {0} -  MoteDuino'.format(self.server.getDeviceId())

	# REQUIRED
	# Attempts to perform the command on
	# the connected device. If the 
	# command fails it return a negative
	# number to indicate failure.
	# Note: This interpreter sits
	# as an intermediary between the 
	# MoteDuino App and the MoteDuino server
	# so interpreter simply forward 
	# the commands received directly
	# To the server and performs no other
	# parsing. 
	def handleData(self, dataStr):
		
		# Sometimes commands are received back to 
		# back on the same line regardless of the new
		# line. For now, we just take the first command
		# and ignore the rest.
		#print 'Data'
		dataStr = dataStr.split('\n',1)[0]
		dataStr = '{0}{1}'.format(dataStr, '\n')
		msgLen = len(dataStr)
		totalSent = 0
		self.bmSocket.settimeout(self.TIME_OUT)
				
		try:
			while totalSent < msgLen:

				bytesSent = self.bmSocket.send(dataStr[totalSent:])
				if bytesSent == 0:
					return -1

				totalSent = totalSent + bytesSent

		except socket.timeout as t:
			print 'Timed out'
			self.bmSocket = None
			return -1
		except Exception as ex:
			print 'Caught it {0}'.format(type(ex))
			# if we have any issues writing to the 
			# socket it must mean the end point must
			# be down. 
			self.bmSocket = None
			return -1
	
		mDataSentSinceKeepAlive = True
		
		return 0 

	# REQUIRED
	# Attempts to receive data from the device.
	# It returns the data received.
	def receiveData(self):
		data = self.bmSocket.recv(1024)
		return data

	
	# Helper Method
	# It seems that either the Arduino or the module
	# close the connection if a couple of hours pass by
	# without any traffic. So we'll use this method to
	# send an empty line every so often to make sure the 
	# connection is not closed.
	def sendKeepAlive(self):
		result = self.handleData('')
		# print 'Keep Alive Sent'	
		return result
	
	def keepAlive(self):
		result = 0
		if self.mDataSentSinceKeepAlive:
			#do nothing
			pass
		else:	
			result = self.sendKeepAlive()
			# Since we just sent the flag will be active. 
			# We don't want to count our sends as traffic.
			self.mDataSentSinceKeepAlive = False
		if result == 0:
			# schedule next keep alive
			self.keepAliveTimerHelper()
			#threading.Timer(self.KEEP_ALIVE_DELAY_IN_SECONDS, self.keepAlive).start()
		else:
			# Don't schedule anything connection has been closed
			pass

	# Helper to create a timer for sending keep alive to Arduino
	# and start it. 
	def keepAliveTimerHelper(self):
		self.mKeepAliveTimer = threading.Timer(self.KEEP_ALIVE_DELAY_IN_SECONDS, self.keepAlive)
		self.mKeepAliveTimer.start()
