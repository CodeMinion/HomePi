from bluepy.btle import *
from struct import *
import threading

#B8:27:EB:9D:2E:47
#00:1A:7D:DA:71:13
 
class HomePiLeakInterpreter(DefaultDelegate):
	
	# Reference to the Leak Sensor Device
	leakSensor = None
	# Reference to connected device 
	leakSensorPeripheral = None
	
	#Home Sensing Service Information 
	home_sensing_service_uuid = "000028FF-0000-1000-8000-00805F9B34FB"
	leak_sensing_characteristic_uuid = "00004A38-0000-1000-8000-00805F9B34FB"

	battery_service_uuid = 0x180F
	battery_level_characteristic_uuid = 0x2A19

	home_sensing_service = None
	leak_sensing_characteristic = None
	
	battery_service = None
	battery_level_characteristic = None
	
	LEAK_DETECTED_TOP = 1
        LEAK_DETECTED_BOTTOM = 2
	LEAK_NONE = 0

	currentLeak = LEAK_NONE
	
	# DATA KEYS
	DATA_KEY_LEAK_VAL = "Leak"
	DATA_KEY_BATTERY_VAL = "Batt"
	
	def __init__(self, homeDev):
		DefaultDelegate.__init__(self)
		self.leakSensor = homeDev
		pass
		
		
	# REQUIRED
	# Attempts to stablish a connection with the 
	# device. In the event that it fails it 
	# return a negative value to indicate a failure.	
	def connect(self):
	
		try:
		
			deviceMac = self.leakSensor.getDeviceMac()
			# Connect to the motion sensor using hci1 interface (Note: Consider changing this to be better controlled)
			# 0 - /dev/hci0
			# 1 - /dev/hci1
			self.leakSensorPeripheral = Peripheral(deviceMac, ADDR_TYPE_RANDOM , 0)
			
			self.leakSensorPeripheral.setDelegate(self)
			
			self.home_sensing_service = self.leakSensorPeripheral.getServiceByUUID(self.home_sensing_service_uuid)
			self.leak_sensing_characteristic = self.home_sensing_service.getCharacteristics(self.leak_sensing_characteristic_uuid)[0]
	
			# Enable notifications 
			setup_data = struct.pack('<bb', 0x01, 0x00)
			ccc_desc = self.leak_sensing_characteristic.getDescriptors(forUUID=0x2902)[0]
			ccc_desc.write(setup_data)
	
			self.battery_service = self.leakSensorPeripheral.getServiceByUUID(self.battery_service_uuid)
			self.battery_level_characteristic = self.battery_service.getCharacteristics(self.battery_level_characteristic_uuid)[0]
	
			# Enable notifications 
			ccc_desc = self.battery_level_characteristic.getDescriptors(forUUID=0x2902)[0]
			ccc_desc.write(setup_data)
	
			PeripheralThread(self.leakSensorPeripheral, self).start()
			
		except BTLEException as btErr:
			print 'Connection to: {0} - FAILED'.format(self.leakSensor.getDeviceId())
			print 'Exception {0}'.format(btErr)
			return -1
			
			print 'SUCCESS - Connection to: {0}'.format(self.leakSensor.getDeviceId())
			
		return 0
		
		pass 
	
	# REQUIRED
	# Attempts to disconnect from the 
	# device.
	def disconnect(self):
		if(self.leakSensorPeripheral is not None):
			self.leakSensorPeripheral.disconnect()
			self.leakSensorPeripheral = None
		pass
		
	# REQUIRED
	# Attempts to perform the command on 
	# the connected device. If the command
	# fails then returns a negative number.
	# Commands are of the form:
	# Command : cmdVal1, cmdVal2, ...	
	def handleData(self, dataStr):
		# TODO 
		pass
		
		
	# REQUIRED
	# Attempts to receive data from the device
	# It returns the data.
	def receiveData(self):
		return self.currentLeak
		pass
	
	
	# Called when the device connection is lost.	
	def onConnectionError(self, btError):
		print "Connection Lost: {0} - {1}".format(self.leakSensor.getDeviceMac(), self.leakSensor.getDeviceUserId())
		
		# Signal to the rest of the system we are offline. 
		self.leakSensor.notifyDeviceDisconnected()
		pass
		
	def handleNotification(self, cHandle, data):
		# TODO Check if the handle is for the motion sensor characteristic.
		if(self.leak_sensing_characteristic.getHandle() == cHandle):
			unpackedTuple = unpack('<bb', data)
			leakValue = unpackedTuple[0]
			
			valueToSend = self.LEAK_NONE
			
			# Translate to Device Agnostic Values.
			if(leakValue == 1):
				valueToSend = self.LEAK_DETECTED_TOP
                        elif(leakValue == 2):
                                valueToSend = self.LEAK_DETECTED_BOTTOM
                        elif(leakValue == 3):
                                valueToSend = self.LEAK_DETECTED_TOP | self.LEAK_DETECTED_BOTTOM
			else: 
				valueToSend = self.LEAK_NONE
				
			self.currentLeak = valueToSend
			
			#print "Leak Value: {0}".format(self.currentLeak)
			
			data = "{0},{1}".format(self.DATA_KEY_LEAK_VAL, self.currentLeak)
			
			# Notify client
			self.leakSensor.notifyDataReceived(data)
			pass
			
		elif(self.battery_level_characteristic.getHandle() == cHandle):
			unpackedTuple = unpack('<b', data)
			battValue = unpackedTuple[0]
			
			data = "{0},{1}".format(self.DATA_KEY_BATTERY_VAL, battValue)
			
			# Notify client
			self.leakSensor.notifyDataReceived(data)
			pass
			
		pass
		
	
		
class PeripheralThread(threading.Thread):

	NOTIFICATION_TIMEOUT_SECONDS = 60.0
	peripheral = None
	connectionListner = None
	def __init__(self, peripheral, listener):
		threading.Thread.__init__(self)
		self.peripheral = peripheral
		self.connectionListner = listener
		pass
		
	def run(self):
		try:
			while True:
				if (self.peripheral.waitForNotifications(self.NOTIFICATION_TIMEOUT_SECONDS)):
					#print "Notification Handled"
					pass
			
				#print "Waiting...."
			pass
			
		except BTLEDisconnectError as btError:
			if self.connectionListner is not None:
				self.connectionListner.onConnectionError(btError)
			pass

#while True:
	
#	if p.waitForNotifications(1.0):
		# handleNotification() was called
#		continue
#	print "Waiting..."
	# Perhaps do something else here 
