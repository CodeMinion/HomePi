import sys
import pexpect
from struct import *

# Implementation of the interpreter to
# handle communications with bPoint outlet 
# HomePi will receive all the commands and strip
# away anything specific to the HomePi protocol
# and send thus the reminder. This remainder 
# will be a command in bpoint protocol so
# we just forward it to bpoint outlet.

class BPointInterpreter(object):

	# Device to interact with
	bPoint = None

	# GATT proces instance used to 
	# send commands to the outlet.
	gatt = None


	# Commands Handled
	COMMAND_ON = 1 
	COMMAND_OFF = 0

	executingCommand = False

	# Socket time out time in secods
	TIME_OUT = 5

	# Constructor
	def __init__(self, bPointHomeDev):
		self.bPoint = bPointHomeDev

	# REQUIRED
	# Attempts to establish a connection with the device.
	# In the event it fails it returns a negative value
	# to indicate failure.
	def connect(self):
		# Do some exception handling here.
		try :
			# Run gatttool
			self.gatt = pexpect.spawn('gatttool -I')
			# Connect to bPoint
			self.gatt.sendline('connect {0}'.format(self.bPoint.getDeviceMac()))
			# Expect success or time out after 30 seconds
			result = self.gatt.expect(['Connection successful', 'Error:. *'], timeout=30)
			if result == 1:
				print '{0}:{1} - Error Trying to reach device. Could be busy or probably didn\'t disconnect properly'.format(self.bPoint.getDeviceId(), self.bPoint.getDeviceMac())
				return -1

			print 'Connected to {0} - bpoint Outlet'.format(self.bPoint.getDeviceMac())

			return 0
		except pexpect.TIMEOUT:
			# Timed out connecting to device.
			print 'Connection to: {0} - TIMED OUT'.format(self.bPoint.getDeviceId())
			return -1

	# REQUIRED
	# Attempts to disconnect from the device
	def disconnect(self):
		self.gatt.close()
		print 'Disconnected from {0} - bpoint'.format(self.bPoint.getDeviceId())

	
	# REQUIRED
	# Attempts to perform the command on 
	# the connected device. If the command
	# fails it returns a negative number.
	# For this we will use the LegaMote protocol
	# where the last four bits of the first byte 
	# represent the command. 
	def handleData(self, dataStr):
		# Don't accept any new commands
		# if we are executing one
		if self.executingCommand:
			return 0


		# We don't do anything if there 
		# is no command.
		if len(dataStr) < 1:
			return 0
		
		# Commands in the LegaMote are
		# two characters long. 
		# A command character and 
		# the new line chracter.
		# So we are just going to take 
		# the first character of the dataStr
		# and send it with the '\n' character.
		commandChar = unpack('B', dataStr[0])
		commandId = int(commandChar[0]) & 0x0F

		if commandId == self.COMMAND_ON:
			commandToWrite = self.commandHelper(self.COMMAND_ON)
			return self.sendCommandHelper(commandToWrite)

		elif commandId == self.COMMAND_OFF:
			commandToWrite = self.commandHelper(self.COMMAND_OFF)
			return self.sendCommandHelper(commandToWrite)

		return -1



	# HELPER METHOD 
	# Created command to send.
	def commandHelper(self, onOff):
		command = 28 + onOff;

		commandToWrite = 'char-write-cmd 0x0025 41544350000{0}{1}00000000000000000000000000'.format(onOff, command)
		return commandToWrite

	# HELPER METHOD
	# Sends a command to bPoint and expects a result.
	def sendCommandHelper(self, commandToWrite):
		self.executingCommand = True
		self.gatt.sendline(commandToWrite)

		result = self.gatt.expect(['Command Failed:.*', 'Error: .*', '\r\n'], timeout=2)

		if result == 0 or result == 1:
			result = -1

		self.executingCommand = False

		return result

		
	# REQUIRED
	# Attempts to receive data form the device.
	# It returns the data received.
	def receiveData(self):
		# No data to receive
		data = ''
		return 

	

		

