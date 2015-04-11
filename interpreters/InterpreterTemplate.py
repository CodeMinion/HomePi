# Template for all interpreters.
# Includes all the interface that must 
# be implemented by any interpreter 
# added to the Home Pi.

class InterpreterTemplate(object):

	# Declare instance variables here.
	# TODO

	# Instance to the HomeDevice this
	# interpreter is connected to.
	homeDevice = None

	# Every interpreter must implement a 
	# constructor that takes a HomeDevice 
	# instance.
	def __init__(self, homedev):
		self.homeDevice = homeDev
		
		
	# REQUIRED
	# Attempts to establish a connection with the
	# device. In the event it fails it returns 
	# a negative value to indicate failure.
	def connect(self):
		# Return negative on fail.
		# return -1

		# Return positive or 0 on
		# success.
		# return 0
		pass

	# REUIQRED
	# Attempts to disconnect from the device
	def disconnect(self):
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
		# return 0
		pass 


	# REQUIRED
	# Attempts to receive data from the device.
	# It returns the data received.
	def receiveData(self):
		# Return data received.
		pass
