import bluetooth
import threading

# Client thread, handles each connected 
# client to the HomePi. This will take 
# care of receiving the commands from the 
# client and forwarding it to the HomePi 
# to be handled. 
class HomePiClientThread(threading.Thread):

	# Referene to the HomePi manager
	piMan = None
	
	# Reference to client socket
	client = None

	# Continue running?
	bRunning = True

	# Constructor, requires instance of client socket
	# as well as a reference to the HomePiManager to
	# be able to send commands to the system.
	def __init__(self, clientSocket, homePiManagerInstance):
		threading.Thread.__init__(self)
		self.piMan = homePiManagerInstance
		self.client = clientSocket

	# Receive data as long as the socket is active.
	def run(self):
		try:
			while self.bRunning:
				data = self.client.recv(1024)
				command = '{0}'.format(data)
				self.piMan.processData(command)	
				#print 'Received: {0}'.format(data)

		except IOError as e:
			# When client disconnect the read
			# returns an error 104, Connection reset by peer
			# This is a good time to remove the client from
			# the client list, since it is no longer 
			# connected to the Home Pi.
			print '{0}'.format(e)
			self.piMan.unregisterClient(self)
			pass
	
	# Send data back to the client. 	
	def send(self, data):
		try:
			self.client.send(data)
		except IOError as e:
			pass

	# Close the connections
	def close(self):
		try:
			self.piMan.unregisterClient(self)
			self.client.close()
			self.bRunning = False
		
		except IOError as e:
			pass

