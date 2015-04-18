import sys
import pexpect

# Implementation of the interpreter to
# handle communication with a Roybens
# Bluetooth Led Bulb.
# This turns all the Color bulb commands
# from HomePi into low level commands
# specific to the bulb.

class RoybensBleBulbInterpreter(object):

	# Device to interact with.
	bulb = None
	
	# GATT process instance used to send commands to the bulb.
	gatt = None
	
	# Commands Handled
	COMMAND_COLOR_CHANGE = 'Color'
	COMMAND_POWER = 'Power'
	COMMAND_DIM = 'Dim'
	
	#Last colors applied.
	lastR = 255
	lastG = 255
	lastB = 255
	
	# Last Dim applied
	lastDim = 255
	
	# Ignore any command request if we are
	# still working on executing one command.
	executingCommand = False
	
	# Constructor
	def __init__(self, bulbHomeDev):
		self.bulb = bulbHomeDev
		
	# REQUIRED
	# Attempts to stablish a connection with the 
	# device. In the event that it fails it 
	# return a negative value to indicate a failure.
	def connect(self):
		try:

			# Run gatttool
			self.gatt = pexpect.spawn('gatttool -I')
			# Connect to the bulb
			self.gatt.sendline('connect {0}'.format(self.bulb.getDeviceMac()))
			# Expect success or time out after 30 seconds
			result = self.gatt.expect(['Connection successful', 'Error:. *'], timeout=30)
			if result == 1:
				print '{0}:{1} - Error Trying to reach device. Could be busy or probably didn\'t disconnect properly.'.format(self.bulb.getDeviceId(), self.bulb.getDeviceMac())
				print '{0}'.format
				return -1
			
			print 'Connected to {0} - Roybens LED Bulb'.format(self.bulb.getDeviceId())
			return 0

		except pexpect.TIMEOUT:
			# If we cannot connect to the device
			# we return a value less than 0.
			print 'Connection to: {0} - TIMED OUT'.format(self.bulb.getDeviceId())
			return -1


	# REQUIRED
	# Attmepts to disconnect from the 
	# device. 
	def disconnect(self):
		self.gatt.close()
		print 'Disconnected from {0} - Roybens LED Bulb'.format(self.bulb.getDeviceId())

		
	# REQUIRED
	# Attempts to perform the command on 
	# the connected device. If the command
	# fails then returns a negative number.
	# Commands are of the form:
	# Command : cmdVal1, cmdVal2, ...
	# Ex. Color:250,0,255
	def handleData(self, dataStr):
		# Don't accept any new commands 
		# if we are executing one.
		if self.executingCommand:
			return 0
		
		dataStr = dataStr.split("\n",1)[0]	
		dataArr = dataStr.split(":", 1)
		
		commandId = dataArr[0]
		commandVals = dataArr[1];
		
		commandVals = commandVals.rstrip()
		if commandId == self.COMMAND_COLOR_CHANGE:
			cmdValsArr = commandVals.split(',', 3)
			
			self.lastR = colorR = int(cmdValsArr[0])
			self.lastG = colorG = int(cmdValsArr[1])
			self.lastB = colorB = int(cmdValsArr[2])

			# Send color change to bulb
			commandToWrite = self.commandHelper(self.lastDim, self.lastR, self.lastG, self.lastB)
			return self.sendCommandHelper(commandToWrite)

		elif commandId == self.COMMAND_POWER:
			offValue = int(commandVals)
			commandToWrite = ''
			if offValue == 1:
				commandToWrite = 'char-write-cmd 0x0043 CC2333'
			else:
				commandToWrite = 'char-write-cmd 0x0043 CC2433'
			
			return self.sendCommandHelper(commandToWrite)

		elif commandId == self.COMMAND_DIM:
			#print 'Dimming Light'
			dimValue = int(commandVals)
			self.lastDim = dimValue
			self.lastOnOff = 1
			commandToWrite = self.commandHelper(self.lastDim, self.lastR, self.lastG, self.lastB)
			#print commandToWrite
			return self.sendCommandHelper(commandToWrite)

		# If the command is not supported return a 
		# negative number.	
		return -1			

	# HELPER METHOD
	# Helper method to build a command to send.	
	def commandHelper(self, dim, r, g, b):
		
		# This bulb handles dim by using a percentage of the 
		# active colors, rather than a separate value. 
		dimPercent = dim / 255.0
		r = int(r * dimPercent)
		g = int(g * dimPercent)
		b = int(b * dimPercent)
		
		commandToWrite = 'char-write-cmd 0x0043 56{0:02X}{1:02X}{2:02X}00F0AA'.format(r, g, b)
		return commandToWrite
			
		
	# HELPER METHOD
	# Sends a command to the bulb and expects a 
	# result. Useful for knowing the when bulb
	# has disconnected.
	def sendCommandHelper(self, commandToWrite):
		self.executingCommand = True
		self.gatt.sendline(commandToWrite)
		#print commandToWrite
		result = self.gatt.expect(['Command Failed:.*', 'Error: .*', '\r\n'], timeout=2)
		#result = 0
		#print 'GATT Result - {0}'.format(result)
		if result == 0 or result == 1:
			# Error communicating with bulb
			 result = -1

		self.executingCommand = False
		return result

	# REQUIRED
	# Attempts to receive data from the device
	# It returns the data.
	def receiveData(self):
		# No data received from this device
		data = ''
		return
