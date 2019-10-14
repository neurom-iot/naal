import socket 
import numpy as np
import logging
import sys

class UDPSocket(object):
	def __init__(self, addr, connection_timeout=300., recv_timeout=10):
		self.addr = addr
		self.conection_timeout = connection_timeout
		self.recv_timeout = recv_timeout
		self.buffer = np.empty(2)
		self._socket = None

	@property
	def closed(self):
		return self._socket is None

	def open(self):
		self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		if sys.platform.startswith('bsd') or sys.platform.startswith('darwin'):
			self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
		else:
			self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		
	def bind(self):
		self._socket.bind(self.addr)

	def recv(self):
		self._socket.settimeout(self.recv_timeout)
		
		try:
			print('Now Start Recceiving...')
			
			while True:
				recv_len = self._socket.recv_into(self.buffer)
				print('recv_len:', recv_len, ', buffer:', self.buffer)

		except socket.timeout:
			socket.close()

	def send(self, buff):
		# for test
		self.buffer[0] = buff
		self._socket.sendto(self.buffer.tobytes(), self.addr)
		print('already send: ', buff)

	def close(self):
		if not self.closed:
			self._socket.close()
			self._socket = None

class UDPReceiveSocket(object):
	def __init__(self, listen_addr, connection_timeout=300., recv_timeout=10):
		self.listen_addr = listen_addr
		self.connection_timeout = connection_timeout
		self.recv_timeout = recv_timeout

	def recv(self):
		recv = UDPSocket(self.listen_addr, self.connection_timeout, self.recv_timeout)
		recv.open()
		recv.bind()
		recv.recv()

class UDPSendSocket(object):
	def __init__(self, remote_addr):
		self.remote_addr = remote_addr

	def send(self, send_buff):
		send = UDPSocket(self.remote_addr)
		send.open()
		send.send(send_buff)


rsocket = UDPReceiveSocket(('192.168.1.28', 5001))
rsocket.recv()
