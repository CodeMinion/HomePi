#!/usr/bin/python

import json
from pprint import pprint
import bluetooth
import threading
import sys
import time

from HomeDevice import HomeDevice 
from HomePiClientThread import HomePiClientThread
from HomePiDeviceStatusCheckerThread import HomePiDeviceStatusCheckerThread

# Main Manager for the HomePi system. 
# Handles the initialization, connection
# and information passing to the registered
# devices. 
class HomePiManager(object):

	# Lock
	threadLock = None

	# Home Pi Id. Used to indentify
	# with other HomePi
	homePiId = ''

	# Directory name where all the interpreter
	# implementations are kept. 
	INTERPRETER_DIR = 'interpreters'
	
	# Default config filename.
	CONFIG_DATA_FILE = 'config'
	
	# The HomePi should keep 
	# running expecting requests.	
	bRunning = True

	# Bluetooth Servie Name
	btName = 'Home Pi Manager'
	# HomePi UUID
	btUuid = '385a5cd2-d573-11e4-b9d6-1681e6b88ec1'
	# Server Socket
	btServerSocket = None
	
	# BUG:
	# After connecting to more than one Classic 
	# Bluetooth client, the serve accept just hangs.
	# Steps to Replicate
	# 1- Connect to two Classic Bluetooth Clients
	# 2- Create a server socket and try to accept
	#    incomming connections.
	# Results: It Doesn't accept and connection times out.
	# 3a- Disconnect one of the devices and the 
	#     accept works again. 
	# Note: This is not limited to two devices 
	# it occurs with any number of device. If we 
	# conect to N devices, it hangs unless we 
	# disconnect from 1 of them before making 
	# the Bluetooth server socket accept().
	# Workaround: Using to Bluetooth Interface
	# one for connecting to clients and one 
	# to serve as a server.  
	clientInterfaceMac = ''
	serverInterfaceMac = ''

	# List of registered devices
	registeredDevices = []
	
	# Maps connected devices to their ids.
	connectedDevices = {}

	# Maps not connected devices to their ids.
	# This may be registered devices that were not available 
	# at boot but became available later. Client Apps 
	# should be able to request a connection to them.
	# Future Update: Have Apps request reconnection to
	# not connected devices. 
	unavailableDevices = {}
	
	# Thread to check the status of Unavailable devices.
	# This is used to know when a registered device becomes
	# available. This way we can notify the clients so they
	# can use it. 
	statusChecker = None

	# Commands understood by HomePi.
	# This are commands specific to the operation
	# of HomePi and not the underlying devices.
	# Tell HomePi to end operations	
	COMMAND_SHUTDOWN = 'shutdown'
	# Request list of connected devices.
	COMMAND_INFO_CONNECTED = 'connInfo'
	# Request list of not connected devices.
	COMMAND_INFO_NO_CONNECTED = 'conConnInfo'
	# Request check on unavaialble devices 
	# to see if any has become active
	COMMAND_INFO_UNAVAILABLE = 'upInfo'

	# Device status for connected devices.
	STATUS_CONNECTED = 'CONNECTED'
	# Device status for devices the HomePi is not 
	# connected to due to a connection failure or
	# because the device got disconnected.
	STATUS_UNAVAILABLE = 'UNAVAILABLE'

	# Information tags, used to wrap the device
	# details when sent over to the client.
	INFO_START = 'START_INFO'
	INFO_END = 'END_INFO'
	# Used to signal the drop of a device
	INFO_DROP = 'DRP'
	# Used to signal a device is back online
	INFO_UP = 'UP'
	# Used to let clients know that device information
	# update is complete
	INFO_DEV_UPDATE_DONE = 'DEV_UD'

	# List of Connected Clients. These are 
	# PiHome Controllers, like mobile Apps.
	connectedClients = []

	# Load the JSON HomePi configuration file.
	# This file contains all the information about
	# all the devices that will be handled by the 
	# HomePi System.
	def loadDevicesJSON(self, configPath):
		# Read from jason config file
		json_file = open(configPath)
		# Parse JSON data
		json_data = json.load(json_file)
		# Close file
		json_file.close()
		
		# Get This PiHome Id
		self.homePiId = json_data['homePiId']

		# Get the Mac for the interface to use to connect 
		# with registered devices.
		self.clientInterfaceMac = json_data['clientInterfaceMac']
			
		# Get the Mac for the interface to use to listen for
		# clients.
		self.serverInterfaceMac = json_data['serverInterfaceMac']


		# Get devices in JSON config
		json_devs = json_data['devices']
	
		# List of registered devices in the HomePi
		self.registeredDevices = []

		for device in json_devs:
			# Get the interpreter name
			interName = device['interpreter']
			# Import the interpreter class
			mod = __import__(self.INTERPRETER_DIR+'.'+interName, fromlist=[interName])
		

			devId = device['id']
			devMac = device['mac']
			devClass = device['class']
			devCat = device['category']
			devUserId = device['userId']
		
			# Create device Instance.
			homeDev = HomeDevice(devId, devMac, devClass, devCat, devUserId)
			# Instanciate the device interpreter
			devInterpreter = getattr(mod, interName)(homeDev)

			# Keep reference of the interpreter in device
			homeDev.setDeviceInterpreter(devInterpreter)

			# Set device listener
			homeDev.setDeviceListener(self)

			# Append to registered device list
			self.registeredDevices.append(homeDev)
		
		# Return all devices registered with this PI.
		return self.registeredDevices	

	# Attempts to connect to all registered devices. 
	# It returns two dictionaries one mapping device Id
	# to device successfully connected to and one mapping
	# device Id to devices it was not able to connect to.
	# Return: connectedDevs, notConnectedDvs
	def connectToRegisteredDevices(self, registeredDevicesList):
		connectedDevs = {}
		notConnectedDevs = {}
		# Attempt to conenct to each registered device
		for device in registeredDevicesList:
			#if device.getDeviceInterpreter().connect() == 0:
			if device.connect() == 0:
				connectedDevs[device.getDeviceId()] = device		
			else:
				notConnectedDevs[device.getDeviceId()] = device

		self.connectedDevices = connectedDevs
		self.unavailableDevices = notConnectedDevs

		return connectedDevs, notConnectedDevs	


	# Given a dictionary of connected devices it
	# attempts to disconnect from each device. 
	def disconnectFromDevices(self, connectedDevsDic):
		for devId,device in connectedDevsDic.iteritems():
			device.disconnect()


	# Given a list of devices it attempts to disconnet
	# from each device.
	def disconnectFromRegisteredDevices(self, registeredDevicesList):
		# Attempt to disconnect from each resgistered device
		for device in registeredDevicesList:
			#device.getDeviceInterpreter().disconnect()
			device.disconnect()

	# Takes a piece of incomming data and turns it into 
	# something HomePi can understand. 
	# Expected data format:
	# Receiver Dev Id @ Device Command\n 
	# Ex. RGBLightBulb1@Color:255,0,255  
	def processData(self, dataBytes):
		dataString = dataBytes

		commandsArr = dataString.split('\n')
		#commandStr = commandsArr[0]
		for commandStr in commandsArr:
			self.processDataHelper(commandStr)
	

	# Helper method to handle an individual command.
	def processDataHelper(self, cmdLine):

		dataArr = cmdLine.split("@", 1)

		# We must receive at least 1 device id 
		# followed by a command
		if len(dataArr) < 2:
			return
			#continue
		
		receiverId = dataArr[0]
		command = dataArr[1]

		# If it is a command for the Pi
		# execute it. Else send it to the
		# registered devices for handling.
		if receiverId == self.homePiId or not receiverId:

			if command == self.COMMAND_SHUTDOWN:
				#self.shutdown()
				pass

			if command == self. COMMAND_INFO_UNAVAILABLE:
				#print '\nChecking unavailable devices...'
				#self.checkUnavailableDevices()
				#print '\nDone checking devices!'
				self.deviceChecker = HomePiDeviceStatusCheckerThread(self)
				self.deviceChecker.start()
				pass


			# If no receiver Id is present, then the 
			# command is intended for the HomePi system
			# itself. Handle it here.
			pass
		else:
			# Find the device to handle this command.
			if receiverId in self.connectedDevices:	
				# Make device handle the command.
				try:
					self.connectedDevices[receiverId].handleData(command)
				except IOError as e:	
					# Device is no longer available
                        		# Notify HomePi so that it switches
                        		# it to the unavailable list.
                        		# TODO
					pass
			# If we are getting a command for an unavailable device
			# it probably means that connection was lost but the client
			# did not receive the status change update.
			elif receiverId in self.unavailableDevices:
				# send device dropped status update to client
				# TODO
				pass


		pass

	# Attempt to disconnect from all conencted clients
	def disconnectFromClients(self, connectedClientsThread):
		for client in connectedClientsThread:
			client.close()

	# Opens a bluetooth channel for client apps
	# Connect to the HomePi.
	def listenForClients(self):
		self.btServerSocket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
		port = 29#bluetooth.PORT_ANY
		
		res = self.btServerSocket.bind((self.serverInterfaceMac, port))
		
		self.btServerSocket.listen(1)
		port = self.btServerSocket.getsockname()[1]
		#time.sleep(5)
		print 'Listening on Port: {0}'.format(port)

		# Advertise service
		bluetooth.advertise_service(self.btServerSocket, self.btName, self.btUuid)
		#time.sleep(2)
		while self.shouldRun():
			try:

				print 'Waiting for Clients...'
				client_sock, client_addr = self.btServerSocket.accept()
				print '{0}: Connection Accepted'.format(client_addr)
				homePiClient = HomePiClientThread(client_sock, self)
				self.connectedClients.append(homePiClient)
				homePiClient.setDaemon(True)
				# Send device information to client.
				self.sendDeviceStatus(homePiClient)
				# Register client
				self.registerClient(homePiClient)
				# Start listening
				homePiClient.start()

			except KeyboardInterrupt as key:
				bluetooth.stop_advertising(self.btServerSocket)
				self.shutdown()
				break
		
		self.shutdown()
		pass

	# Registers client with Home Pi
	def registerClient(self,connectedClientThread):
		self.connectedClients.append(connectedClientThread)
		pass

	# Remove client from registered list.
	def unregisterClient(self, connectedClientThread):
		self.connectedClients.remove(connectedClientThread)
		pass
	
	# Notifies clients of message
	def notifyClients(self, message):
		for client in self.connectedClients:
			client.send('{0}\n'.format(message))

	# Notifies clients of HomePi shutdown.
	def notifyShutdown(self):
		for client in self.connectedClients:
			client.send('{0}\n'.format(self.COMMAND_SHUTDOWN))
		pass

	# Sends the client the status of every device 
	# registered with the HomePi
	def sendDeviceStatus(self, clientThread):
		clientThread.send('{1}:{0}\n'.format(len(self.registeredDevices), self.INFO_START))
		
		for deviceId, dev in self.connectedDevices.iteritems():
			clientThread.send(self.statusDeviceLineHelper(dev))

		for deviceId, dev in self.unavailableDevices.iteritems():
			clientThread.send(self.statusDeviceLineHelper(dev))

		clientThread.send('{0}\n'.format(self.INFO_END))
		pass

	# Helper method to build the status line based the status of the
	# device.	
	def statusDeviceLineHelper(self, device):
		status = ''
		if device.getDeviceId() in self.connectedDevices:
			status = self.STATUS_CONNECTED
		elif device.getDeviceId() in self.unavailableDevices:
			status = self.STATUS_UNAVAILABLE

		statusLine = '{0}:{1}:{2}:{3}:{4}\n'.format(self.homePiId, device.getDeviceId(), device.getDeviceClass(), status, device.getDeviceUserId())	
		
		return statusLine

	# Disconnects all the connected devices
	# So as to leave them in a safe state
	def shutdown(self):
		try:
			print '\nShutting down HomePi!!'
			self.notifyShutdown()
			#self.bRunning = False
			self.disconnectFromDevices(self.connectedDevices)
			self.disconnectFromClients(self.connectedClients)		
			self.notifyShutdown()
			self.btServerSocket.close()
			print '\nServer Socket Closed'
		except bluetooth.btcommon.BluetoothError:
			pass

	
	def shouldRun(self):
		return self.bRunning

	# Initialize HomePi System
	def init(self, configFile):
	 	# Create a lock object for synchronization.
		self.threadLock = threading.Lock()
	
		print 'Loading Home Devices...'
		regDevices = self.loadDevicesJSON(configFile)
		print 'Done Loading Home Device!'
		print '\nAttempting connection to devices...'
		self.connectToRegisteredDevices(regDevices)
		print '\nConnection attempt done!'
		
		# Note: Seemed like a good idea but slows 
		# down interaction with the HomePi while it is 
		# trying to connect to the unavailable devices.
		# Removing for now until a better solution comes
		# to mind.
		print '\nSpawning Device Checker Thread...'
		#self.statusChecker = HomePiDeviceStatusCheckerThread(self, 15)
		#self.statusChecker.setDaemon(True)
		#self.statusChecker.start()
		
		# Listening to devices...	
		self.listenForClients()


	# Device Status listener method.
	# Gets called when a given device gets disconnected. 
	def onDeviceDisconnected(self, device):
		print '{0} Disconnected'.format(device.getDeviceMac())
		# 1 - Move Device from Connected to Unavailable Map
		devId = device.getDeviceId()
		# If device is already in the list do nowthing
		if devId in self.unavailableDevices:
			return

		del self.connectedDevices[devId]
		self.unavailableDevices[devId] = device
		# 2 - Create status line
		statusLine = self.statusDeviceLineHelper(device)
		# 3 - Append drop INFO in front of it.
		statusMess = '{0}:{1}'.format(self.INFO_DROP, statusLine)
		# 4 - Send each client the drop message about this device
		self.notifyClients(statusMess)
		print 'Clients Notified - {0}'.format(statusMess)
		pass

	# Device Status Listener Method.	
	# Gets called when a given device becomes available.
	def onDeviceAvailable(self, device):
		print '{0} Available'.format(device.getDeviceMac())
		# 1 - Move device from Unavalable Map to Connected Map
		devId = device.getDeviceId()

		# If device is already in the list then do nothing.
		if devId in self.connectedDevices:
			return

		del self.unavailableDevices[devId]
		self.connectedDevices[devId] = device
		# 2 - Create status line
		statusLine = self.statusDeviceLineHelper(device)
		# 3 - Append up INFO in front of it.
		statusMess = '{0}:{1}'.format(self.INFO_UP, statusLine)
		# 4 - Send client the up messafe about the device
		self.notifyClients(statusMess)
		print 'Client Notified - {0}'.format(statusMess)
		pass

	# Gets called when a device receives data. 
	def onDeviceDataReceived(self, device, deviceData):
		print 'Data - {0} - From {1}'.format(deviceData, device.getDeviceMac())
		pass

	
	# For every device that is Unavailable it tries to 
	# connect to it to see if it is available now. 
	# If the device becomes available it moves it into the 
	# connected map and lets the clients know.
	# NOTE: Should be called from within a seprate thread.
	def checkUnavailableDevices(self):
		self.threadLock.acquire()
		availDevs = []
		devsToTest = []
		# Copy the devices so we can modify the dictionary
		# as devices connect. This allows us to send the
		# devices to the clients as soon as they become 
		# available as opposed to wiating for the entire
		# search to be over for the client to get all the 
		# available devs at once.
		for deviceId, dev in self.unavailableDevices.iteritems():
			devsToTest.append(dev)
			#if dev.connect() == 0:
				# Device is now available
				# self.onDeviceAvailable(dev)
			#	availDevs.append(dev)
		
		#for dev in availDevs:
		#	self.onDeviceAvailable(dev)
	
		for dev in devsToTest:
			if dev.connect() == 0:
				self.onDeviceAvailable(dev)

		# Notify clients of device update done
		cmdLine = '{0}'.format(self.INFO_DEV_UPDATE_DONE)
		self.notifyClients(cmdLine)	
		self.threadLock.release()
		pass


if __name__ == '__main__':
	piManager = HomePiManager()

	if len(sys.argv) == 2:
		piManager.init(sys.argv[1])
	else:
		piManager.init(HomePiManager.CONFIG_DATA_FILE)


