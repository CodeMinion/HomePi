#!/usr/bin/python

import json
from pprint import pprint
import bluetooth
import threading
import sys
import time
import subprocess, signal
import os
import signal 
import sys 
import commands

from shutil import copyfile

import piglow


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
	threadLock = None

	# Path used to configure the HomePi
	configFilePath = None 
	configFileTempExt=".swp"
	
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
	clientHciInterface = ''
	serverHciInterface = ''

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
	# Request data read from a given device
	COMMAND_READ_DATA = 'readData'
	# Request the PI to configure itself with the provided configuration data.
	COMMAND_CONFIG_PI = 'configPi'
	# Request the PI To configure wifi. 
	COMMAND_CONFIG_WIFI = 'configWifi'
	# Request to update the HomePi firmware.
	COMMAND_UPDATE_FIRMWARE = 'updateFirmware'

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
	# Used to let clients know that configuration is done
	INFO_CONFIG_DONE = 'CONFIG_END'
	# Used to notify the client that wifi configuration is over.
	INFO_CONFIG_WIFI_DONE = 'CONFIG_WIFI_END'
	# Used to notify the client that the firmware update is done.
	INFO_FIRMWARE_UPDATE_DONE = 'FIRMWARE_UPDATE_DONE'
	
	# Read data tags, used to wrap the device details
	# about data read from a device to the clients.
	READ_START = 'READ_START'
	READ_END = 'READ_END'

	# JSON Keys
	KEY_CLIENT_INTERFACE_MAC = 'clientInterfaceMac'
	KEY_SERVER_INTERFACE_MAC = 'serverInterfaceMac'
	KEY_DEVICES = 'devices'
	KEY_HOME_PI_ID = 'homePiId'
	KEY_WIFI_SSID = 'ssid'
	KEY_WIFI_PSK = 'psk'
	KEY_PIN_CODE = 'pinCode'
	
	# TODO Add missing keys 
	
	# List of Connected Clients. These are 
	# PiHome Controllers, like mobile Apps.
	connectedClients = []

	feedbackGlow = 32

	# Helper to load the configuraiton file.
	# If the configuration no configuration file is available
	# a default file will be loaded. 
	# If a corrupted or invalid config is found it will try to 
	# load the last correct configuration file if any. 
	def loadConfigHelper(self, configPath, prevConfig):
	
		try:
			# Read from Json config file
			json_file = open(configPath)
			# Parse JSON data
			json_data = json.load(json_file)
			# Close file
			json_file.close()
			return json_data
			
		except ValueError as e: #JSONDecodeError as e:
			print "Corrupted Config File! Attempting to configure with last saved file..."
			# Read from Json config file
			json_file = open(prevConfig)
			# Parse JSON data
			json_data = json.load(json_file)
			# Close file
			json_file.close()
			return json_data
			
		except IOError as e:
			# No Config file found this means that this is a new HomePi. 
			# Generate a default config file to allow connection by the clients.
			json_data = self.generateDefaultConfig()
			# Store it as the current config
			with open(self.configFilePath, "w+") as configFile:
				configFile.write(json.dumps(json_data))
			return json_data
			
		pass

	# Generates a default configuration file which contains 
	# Hci0 as the default interface for the mobile client connection. 
	# It also has an empty list of devices. 
	def generateDefaultConfig(self):
		json_data = {}
		macs = self.getHomePiBluetoothInterfaces()
		json_data[self.KEY_HOME_PI_ID] = "HomePi"
		json_data[self.KEY_CLIENT_INTERFACE_MAC] = macs[0]
		json_data[self.KEY_SERVER_INTERFACE_MAC] = macs[1]
		json_data[self.KEY_DEVICES] = []
		return json_data	
	
	# Load the JSON HomePi configuration file.
	# This file contains all the information about
	# all the devices that will be handled by the 
	# HomePi System.
	def loadDevicesJSON(self, configPath):
		
		# Read from jason config file
		json_data = self.loadConfigHelper(configPath, configPath+self.configFileTempExt)
		
		# Get This PiHome Id
		self.homePiId = json_data['homePiId']

		# Replace Mac Addresses with system addresses. 
		# Note: Users will no longer have to specify these values 
		# because will get them from the system
		macs = self.getHomePiBluetoothInterfaces()
		json_data[self.KEY_CLIENT_INTERFACE_MAC] = macs[0]
		json_data[self.KEY_SERVER_INTERFACE_MAC] = macs[1]
		
		self.clientHciInterface = macs[2]
		self.serverHciInterface = macs[3]
		
		# Get the Mac for the interface to use to connect 
		# with registered devices.
		self.clientInterfaceMac = json_data[self.KEY_CLIENT_INTERFACE_MAC]
			
		# Get the Mac for the interface to use to listen for
		# clients.
		self.serverInterfaceMac = json_data[self.KEY_SERVER_INTERFACE_MAC]


		# Get devices in JSON config
		json_devs = json_data[self.KEY_DEVICES]
	
		# List of registered devices in the HomePi
		self.registeredDevices = []

		for device in json_devs:
			# Get the interpreter name
			interName = device['interpreter']
			# Import the interpreter class
			mod = __import__(self.INTERPRETER_DIR+'.'+interName, fromlist=[interName])
	
			# Ensure IDs are treated as strings
			devId = '{0}'.format(device['id'])
			devMac = device['mac']
			devClass = device['class']
			devCat = device['category']
			devUserId = device['userId']
			devPinCode = None
			
			if self.KEY_PIN_CODE in device:
				devPinCode = '{0}'.format(device[self.KEY_PIN_CODE])
			
			#TODO Handle Pairing data.
		
			# Create device Instance.
			homeDev = HomeDevice(self, devId, devMac, devClass, devCat, devPinCode, devUserId)
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
		# Attempt to connect to each registered device
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


	# Given a list of devices it attempts to disconnect
	# from each device.
	def disconnectFromRegisteredDevices(self, registeredDevicesList):
		# Attempt to disconnect from each registered device
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
			if len(commandStr) == 0:
				continue
				
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

			elif command == self.COMMAND_INFO_UNAVAILABLE:
				#print '\nChecking unavailable devices...'
				#self.checkUnavailableDevices()
				#print '\nDone checking devices!'
				self.deviceChecker = HomePiDeviceStatusCheckerThread(self)
				self.deviceChecker.start()
				pass

			elif command.startswith(self.COMMAND_CONFIG_PI):
				# Handle the Configuration
				configData = command[len(self.COMMAND_CONFIG_PI):]
				# Create a temp file with the old config
				copyfile(self.configFilePath, self.configFilePath+self.configFileTempExt)
				# Copy the config to the current location.
				configFile = open(self.configFilePath, "w+")
				configFile.write(configData)
				configFile.close()
				# Notify clients of Configuration Complete.
				cmdLine = '{0}'.format(self.INFO_CONFIG_DONE)
				self.notifyClients(cmdLine)	
				# Do any any clean up needed for shutdown. 
				self.shutdown()
				# Reboot device 
				os.system("sudo reboot")
				pass
			
			elif command.startswith(self.COMMAND_CONFIG_WIFI):
				configData= command[len(self.COMMAND_CONFIG_WIFI):]
				json_data = json.loads(configData)
				ssid = json_data[self.KEY_WIFI_SSID]
				psk = json_data[self.KEY_WIFI_PSK]
				# TODO Execute wpa_passphrase
				cmd = "wpa_passphrase {0} {1} >> /etc/wpa_supplicant/wpa_supplicant.conf".format(ssid, psk)
				status, output = commands.getstatusoutput(cmd)
				
				if status == 0:
					# Restart wifi 
					cmd = "wpa_cli -i wlan0 reconfigure"
					status, output = commands.getstatusoutput(cmd)
					cmdLine = '{0}'.format(self.INFO_CONFIG_WIFI_DONE)
					self.notifyClients(cmdLine)	
				else: 
					print "Error Configuring Wifi" 
					# TODO Notify Wifi Config Failed
				pass
			elif command == self.COMMAND_UPDATE_FIRMWARE:
				firmware_branch = "master"
				firmware_remote = "origin"
				cmd = "git pull -r {0} {1}".format(firmware_remote, firmware_branch)
				status, output = commands.getstatusoutput(cmd)
								
				# TODO Handle the status to better notify the users
				# Notify clients of Configuration Complete.
				cmdLine = '{0}'.format(self.INFO_FIRMWARE_UPDATE_DONE)
				self.notifyClients(cmdLine)	
				# Do any any clean up needed for shutdown. 
				self.shutdown()
				# Reboot device 
				os.system("sudo reboot")
				pass
				
			# If no receiver Id is present, then the 
			# command is intended for the HomePi system
			# itself. Handle it here.
			pass
			
			
		else:
			# Find the device to handle this command.
			if receiverId in self.connectedDevices:	
				if command == self.COMMAND_READ_DATA:
                    # Read from the device and notify clients
					dataRead = self.connectedDevices[receiverId].readData();
					# Notify each client of the data.	
					self.notifyClientsDataRead(receiverId,dataRead)	
				else: 
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
		
	# Attempt to disconnect from all connected clients
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

	# Notifies client of data read from a device.
	def notifyClientsDataRead(self, deviceId, data):
		for client in self.connectedClients:
			client.send('{0}\n'.format(self.READ_START))
			client.send('{0}:{1}\n'.format(deviceId, data))
			client.send('{0}\n'.format(self.READ_END))

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
			
			# Feedback - Performing cleanup
			piglow.blue(0)
			piglow.red(self.feedbackGlow)
			piglow.show()

			# Start device disconnect.
			self.disconnectFromDevices(self.connectedDevices)
			self.disconnectFromClients(self.connectedClients)		
			self.notifyShutdown()
			self.btServerSocket.close()
			print '\nServer Socket Closed'
			time.sleep(3)
		
		except bluetooth.btcommon.BluetoothError:
			pass

	def shufdownHelper(self):
		piglow.off()
	pass
	
	def shouldRun(self):
		return self.bRunning
		
	# Initialize HomePi System
	def init(self, configFile):

		# Track the file used to configure the current instance
		self.configFilePath = configFile 
		
		# Set up handler for process termination
		signal.signal(signal.SIGTERM, onHomePiKilled)
		signal.signal(signal.SIGINT, onHomePiKilled)
	
		# Create a lock object for synchronization.
		self.threadLock = threading.Lock()

		# Feedback -  Performing cleanup.
		piglow.red(self.feedbackGlow)
		piglow.show()

		print 'Closing all existing GATT Connections... '
		self.closeAllGattConnections()	
		print 'Done'
		
		# Feedback - Performing Config Initialization.
		piglow.red(0)
		piglow.orange(self.feedbackGlow)
		piglow.show()

		print 'Loading Home Devices... '
		regDevices = self.loadDevicesJSON(configFile)
		print 'Done Loading Home Device!'

		# Feedback - Connecting to registered devices.
		piglow.orange(0)
		piglow.yellow(self.feedbackGlow)
		piglow.show()

		print '\nAttempting connection to devices...'
		self.connectToRegisteredDevices(regDevices)
		print '\nConnection attempt done!'
		
		# Note: Seemed like a good idea but slows 
		# down interaction with the HomePi while it is 
		# trying to connect to the unavailable devices.
		# Removing for now until a better solution comes
		# to mind.
		#print '\nSpawning Device Checker Thread...'
		#self.statusChecker = HomePiDeviceStatusCheckerThread(self, 15)
		#self.statusChecker.setDaemon(True)
		#self.statusChecker.start()
		
		# Feedback - Ready and waiting for connections.
		piglow.red(0)
		piglow.orange(0)
		piglow.yellow(0)

		piglow.blue(self.feedbackGlow)
		piglow.show()

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
		self.notifyClientsDataRead(device.getDeviceId(),deviceData)	
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

	# This will close all GATT connections that the Raspberry Pi
	# currently has open. 
	def closeAllGattConnections(self):
		ps = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
		out, err = ps.communicate()

		for prcLine in out.splitlines():
			if 'gatttool' in prcLine:
				pid = int(prcLine.split(None, 1)[0])
				os.kill(pid, signal.SIGKILL)

		pass
	
	# Requests the MAC Addresses of the Bluetooth adapters.
	# @returns A tubple containg clientMac, serverMac. 
	def getHomePiBluetoothInterfaces(self):
		# MAC used to connect peripherals.
		clientHci = "hci1"
		clientMac = self.getBtInterfaceMac(clientHci)
		# MAC used to listener for mobile clients. 
		serverHci = "hci0"
		serverMac = self.getBtInterfaceMac(serverHci)
		return (clientMac, serverMac, clientHci, serverHci)
		
		
	# Helper function to retreive device the PI BT MAC	
	def getBtInterfaceMac(self, interfaceId):
		cmd = "hciconfig"
		status, output = commands.getstatusoutput(cmd)
		btMac = output.split("{}:".format(interfaceId))[1].split("BD Address: ")[1].split(" ")[0].strip()
		return btMac

# Handler for KILL of HomePi process
def onHomePiKilled(signum, frame):
	piManager.shutdown()
	sys.exit(0)

if __name__ == '__main__':
	piManager = HomePiManager()

	if len(sys.argv) == 2:
		piManager.init(sys.argv[1])
	else:
		piManager.init(HomePiManager.CONFIG_DATA_FILE)


