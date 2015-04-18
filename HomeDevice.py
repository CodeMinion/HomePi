import threading

class HomeDevice(object): #threading.Thread):

	# Id for the device
	devId = "" 
	# Mac of the Device to Connect to.
	macAddress = ""
	# Device Class
	# Used to identify the kind of device.
	# Ex: Bulb, Computer, etc
	devClass = ""
	# Category of the Device.
	# Ex. BLE, Bluetooth, etc.
	devCategory = ""
	# Device User Indentifier
	devUserIdentifier = ""
	# Interpreter that will be used to communicate with
	# the device. Meant to translate commands 
	# into device specific instructions
	devInterpreter = None
	# Reference to the device listener
	# used to listen to changes in the device
	# like data received, disconnect
	devListener = None

	# Is running
	bRunning = True

	def __init__(self, devId, mac, devClass, devCat, userId):
		#threading.Thread.__init__(self)
		self.devId = devId
		self.macAddress = mac
		self.devClass = devClass
		self.Category = devCat
		self.devUserIdentifier = userId
		#self.setDaemon(True)
		#pass

	# Returns the id of this device.
	# Ex. RGBLightBulb1
	def getDeviceId(self):
		return self.devId

	# Returns the device mack address.
	def getDeviceMac(self):
		return self.macAddress

	# Returns the device class.
	def getDeviceClass(self):
		return self.devClass

	# Returns the device user identifier
	def getDeviceUserId(self):
		return self.devUserIdentifier

	# Returns the device interpreter
	def getDeviceInterpreter(self):
		return self.devInterpreter
	
	# Sets the interpreter for this device.
	def setDeviceInterpreter(self, interpreter):
		self.devInterpreter = interpreter

	# Sets a device listener
	def setDeviceListener(self, devListener):
		self.devListener =  devListener

	# Attempt to connect this device.
	def connect(self):
		retCode = self.devInterpreter.connect()
		if retCode == 0:
			
			#self.thread = threading.Thread(target=self.run)
			#self.thread.setDaemon(True)
			#self.thread.start()
			
			# self.setDaemon(True)
			# If sucessfully connected
			# start listening.
			#self.start()
			pass
		return retCode

	# Attmpet to disconnect from this device.
	def disconnect(self):
		self.devInterpreter.disconnect()
		self.bRunning = False


	# Attempt to handle the data
	# Data could be expected to be of the form
	# Command : cmdVal1, cmdVal2, etc..
	# Ex. Color:255,00,255
	# Note: It is ultimately left to the 
	# interpreter to parse the command
	# so the actual form of the data is 
	# only relevat at that level as it is not
	# handled here.
	def handleData(self, dataStr):
		#print 'Handling Data: {0}'.format(dataStr)
		retVal = self.devInterpreter.handleData(dataStr)
		# If there was an error sending then
		# the socket is probably closed.
		if retVal < 0:
			#print 'Devices Lost- {0}'.format(self.getDeviceMac())
			self.devListener.onDeviceDisconnected(self)
		#print 'Dev Returned: {0}'.format(retVal)

		pass

	# Handle Data Receive
	def run(self):
		try:
			while self.bRunning:
				# Ask data from Interpreter
				data = self.devInterpreter.receiveData()
				# Don't do anything if we dont get
				# any data.
				if not data:
					continue
				
				# Notify listener of data received
				self.devListener.onDeviceDataReceived(self, data)
		except IOError as e:
			# Device was disconnected
			# Let listner know
			self.devListener.onDeviceDisconnected(self)
			pass

		pass

	# Stop listening
	def stopListening(self):
		self.bRunning
		pass

