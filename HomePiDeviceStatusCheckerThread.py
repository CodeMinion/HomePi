import threading
import time
# This thread scans the devices that are registered 
# but are not connected to see if any of them has
# changed its status since the HomePi was initialize.
# NOTE: All of the work is done by the HomePi 
# so very little code is found here.
class HomePiDeviceStatusCheckerThread(threading.Thread):

	# Reference to the Home Pi
	homePi = None

	# Sleep time, time to wait before checking again
	sleepTime = 10

	# Continue running ?
	bRunning = True

	def __init__(self, homePi, sleepTime = 10):
		threading.Thread.__init__(self)
		self.homePi = homePi
		self.sleepTime = sleepTime
		self.setDaemon(True)
		
		pass	
	# Try to connect to devices then, go back to sleep
	def run(self):

		while self.bRunning:
			print '\nChecking Unavailable devices for satus change...'
			self.homePi.checkUnavailableDevices()
			print '\nDone Checking for Devices, going to sleep now!\n'
			# Just run once for now
			# Still need to make code thread safe.
			#time.sleep(self.sleepTime)
			self.bRunning= False
		pass

	# Set the running flag.
	def setRunning(self, running):
		if running:
			if not self.bRunning:
				self.bRunning = running
				self.start()
				self.setDaemon(True)
		else:
			self.bRunnning = running
	
		pass

	# Sets the time to sleep before checking again for
	# devices.
	def setSleepTime(self, sleepTime):
		self.sleepTime = sleepTime
		pass	
