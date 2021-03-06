import threading
import commands
import os

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
	# Pin code used for the device
	pinCode = None
	# User Key of the owner of this Device
	userKey = None
	
	# Reference to the device listener
	# used to listen to changes in the device
	# like data received, disconnect
	devListener = None
	
	# Owner HomePi
	homePiOwner = None
	
	# Is running
	bRunning = True

	def __init__(self, homePiOwner, devId, mac, devClass, devCat, devPinCode, userId):
		#threading.Thread.__init__(self)
		self.homePiOwner = homePiOwner
		self.devId = devId
		self.macAddress = mac
		self.devClass = devClass
		self.Category = devCat
		self.devUserIdentifier = userId
		self.pinCode = devPinCode
		self.userKey = userId
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
			#self.devListener.onDeviceDisconnected(self)
			self.notifyDeviceDisconnected()
		#print 'Dev Returned: {0}'.format(retVal)

		pass

	# Attempt to read data from the device.
	def readData(self):
		dataRead = self.devInterpreter.receiveData()
		print 'Data Read - {0}'.format(dataRead)
		return dataRead
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
				#self.devListener.onDeviceDataReceived(self, data)
				notifyDataReceived(data)
		except IOError as e:
			# Device was disconnected
			# Let listener know
			self.devListener.onDeviceDisconnected(self)
			pass

		pass
	
	# Used to notify the listener that this device has
	# disconnected. 
	def notifyDeviceDisconnected(self):
		self.devListener.onDeviceDisconnected(self)
		pass
	
	# Used to notify the listener that the device 
	# has received data. 
	def notifyDataReceived(self, data):
		self.devListener.onDeviceDataReceived(self, data)
		pass

	# Creates a pair record for the device and the HomePi
	def pairDevice(self, pinCode = None):
		if pinCode is None:
			pinCode = self.pinCode
	
		# If device is already paired, do nothing.
		if self.isPaired():
			return 
			
		cmd = "./bluetoothPair.sh {0} {1} {2}".format(self.macAddress, pinCode, self.homePiOwner.clientInterfaceMac)
		status, output = commands.getstatusoutput(cmd)
		pass
	
	def unpairDevice(self):
		cmd = "./bluetoothUnpair.sh {0} {1}".format(self.macAddress, self.homePiOwner.clientInterfaceMac)
		status, output = commands.getstatusoutput(cmd)
		pass 
	
	# Returns true if the device is paired
	def isPaired(self):
		#Check if a folder exists if the following directory exists:
		#  /var/lib/bluetooth/{self.homePiOwner.clientInterfaceMac}/{self.macAddress}
		pairRecordPath = '/var/lib/bluetooth/{0}/{1}/'.format(self.homePiOwner.clientInterfaceMac, self.macAddress)
		exists = os.path.isdir(pairRecordPath)
		return exists
		pass
	
	# Returns true if the device requires pairing
	def requiresPair(self):
		pairReq = (not self.pinCode is None) and len(self.pinCode) > 0
		return pairReq
		
	# Stop listening
	def stopListening(self):
		self.bRunning
		pass

