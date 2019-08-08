#!/usr/bin/python

import threading
import requests
from HomeDevice import HomeDevice

# Thread for notifying the backend of 
# sensor activity. 
class DeviceActivityThread(threading.Thread):

	# Url of the endpoint to post 
	# the data to. 
	mEndpointUrl = None
	
	# Key to post to the backend
	mApiKey = ""
	
	# ID of the hub the sensor is 
	# attached to.
	mHubId = None
	
	# Device sending 
	# the activity data
	mHomeDevice = None
	
	# Sensor data to post.
	mDeviceData = None
	
	def __init__(self, endpointUrl, apiKey, hubId, homeDevice, deviceData):
		threading.Thread.__init__(self)
		self.mEndpointUrl = endpointUrl
		self.mApiKey = apiKey
		self.mHubId = hubId
		self.mHomeDevice = homeDevice
		self.mDeviceData = deviceData
		
	def run(self):
		payload = {'apiKey':self.mApiKey,
				'hubId': self.mHubId,
				'deviceId': self.mHomeDevice.getDeviceId(),
				'data': self.mDeviceData}
				
		# Post sensor activity
		response = requests.post(url = self.mEndpointUrl, json = payload)
		
		pass
	
if __name__ == '__main__':
	endpointUrl = "http://localhost:8080/addSensorActivity"
	apiKey = ""
	hubId = 0
	homeDevice = HomeDevice(None, 1, "00:00:00:00:00:00", "LeakSensor", "BLE", "", "Lamp 1")
	deviceData = "Leak,1"
	sensorAct = DeviceActivityThread(endpointUrl, apiKey, hubId, homeDevice, deviceData)
	sensorAct.start()
	pass