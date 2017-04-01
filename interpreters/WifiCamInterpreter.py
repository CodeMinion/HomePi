# Interpreter for a Raspberry Pi 
# the camera. It is a placeholder
# for the remote clients to connect
# to. Most of the streaming will 
# be done from the remote client
# to the actual camera.
class WifiCamInterpreter(object):

	# Declare instance variables here.
	# TODO

	# Instance to the HomeDevice this
	# interpreter is connected to.
	homeDevice = None

	# Every interpreter must implement a 
	# constructor that takes a HomeDevice 
	# instance.
	def __init__(self, homeDev):
		self.homeDevice = homeDev
		# Do Nothing Else we don't really connect.	
		
	# REQUIRED
	# Attempts to establish a connection with the
	# device. In the event it fails it returns 
	# a negative value to indicate failure.
	def connect(self):
		# Return negative on fail.
		# return -1

		# Return positive or 0 on
		# success.
		print 'SUCCESS: Connected to {0} - WiFiCam'.format(self.homeDevice.getDeviceId())

		return 0
		pass

	# REUIQRED
	# Attempts to disconnect from the device
	def disconnect(self):
		# No connection so there is no need to connect.
		print 'SUCCESS: Conn to {0} - WiFiCam'.format(self.server.getDeviceId())

		pass

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
		# Return negative on fail.
		# return -1
		
		# Return positive or 0 on
		# success.
		return 0
		pass 


	# REQUIRED
	# Attempts to receive data from the device.
	# It returns the data received.
	def receiveData(self):
		# Return data received.
		return self.homeDevice.getDeviceMac(); 
		pass
