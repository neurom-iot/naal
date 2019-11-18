from __future__ import absolute_import

import socket
import sys
import threading
import numpy as np



class ConnectionTimeout(RuntimeError):
    pass

class _UDPSocket(object):
    def __init__(self, addr, dims, byte_order, timeout=None):
        self.addr = addr
        self.dims = dims
        if byte_order == "little":
            byte_order = "<"
        elif byte_order == "big":
            byte_order = ">"
        if byte_order not in "<>=":
            raise ValidationError("Must be one of '<', '>', '=', 'little', "
                                  "'big'.", attr="byte_order")
        self.byte_order = byte_order
        if np.isscalar(timeout):
            self.timeout = (timeout, timeout)
        else:
            self.timeout = timeout
        if self.timeout is not None:
            self.current_timeout = max(self.timeout)
        else:
            self.current_timeout = None

        self._buffer = np.empty(dims + 1, dtype="%sf8" % byte_order)
        self._buffer[0] = np.nan
        self._socket = None

    @property
    def t(self):
        return self._buffer[0]

    @property
    def x(self):
        return self._buffer[1:]

    @property
    def closed(self):
        return self._socket is None

    def open(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if sys.platform.startswith('bsd') or sys.platform.startswith('darwin'):
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        else:
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if self.timeout is not None:
            self.current_timeout = max(self.timeout)
        else:
            self.current_timeout = None

    def bind(self):
        self._socket.bind(self.addr)

    def recv(self, timeout):
        print("Waiting for packet with timeout %fs.", timeout)
        self._socket.settimeout(timeout)
        self._socket.recv_into(self._buffer.data)
        print("Received packet for t=%fs.", self.t)

    def recv_with_adaptive_timeout(self):
        if self.current_timeout is not None:
            print(
                "Waiting for packet with adaptive timeout "
                "(current value %fs.)", self.current_timeout)
        else:
            print("Waiting for packet (blocking).")
        self._socket.settimeout(self.current_timeout)
        try:
            self._socket.recv_into(self._buffer.data)
            if self.current_timeout is not None:
                self.current_timeout = max(
                    min(self.timeout), 0.9 * self.current_timeout)
        except socket.timeout:
            if self.current_timeout is not None:
                self.current_timeout = max(self.timeout)
            raise

    def send(self, t, x):
        self._buffer[0] = t
        self._buffer[1:] = x
        self._socket.sendto(self._buffer.tobytes(), self.addr)
        print("Send packet for t=%fs.", self.t)

    def close(self):
        if not self.closed:
            self._socket.close()
            self._socket = None

class socketstep(object):


    def __init__(self, dt, send=None, recv=None,
                 remote_dt=None, connection_timeout=None, loss_limit=None, ignore_timestamp=False):
        self.send_socket = send
        self.recv_socket = recv
        self.remote_dt = remote_dt
        self.connection_timeout = connection_timeout
        self.ignore_timestamp=ignore_timestamp
        self.loss_limit = loss_limit
        self.n_lost = 0


        self.dt = dt
        if remote_dt is None:
            remote_dt = dt
  
        self.remote_dt = max(remote_dt, dt)

        self.value = np.zeros(0 if self.recv_socket is None
                              else self.recv_socket.dims)

    def __call__(self, t, x=None):
       
        if t== 0.:
            return self.value
                     
        if self.send_socket is not None:
            assert x is not None, "A sender must receive input"
            self.send(t, x)
        if self.recv_socket is not None and (
                self.loss_limit is None or self.n_lost <= self.loss_limit):
            try:
                self.recv(t)
                self.n_lost = 0
            except socket.timeout:  # packet lost
                print("No packet received for t=%fs.", t)
                self.n_lost += 1
        return self.value  


    def __del__(self):
        self.close()

    def close(self):
        if self.send_socket is not None:
            self.send_socket.close()
        if self.recv_socket is not None:
            self.recv_socket.close()

    def recv(self, t):
        if self.recv_socket.t < 0:
            raise RuntimeError(
                "UDP Socket connection terminated by remote side.")

        if self.ignore_timestamp:
            self.recv_socket.recv_with_adaptive_timeout()
            self._update_value()
            return

        # Receive initial packet
        if np.isnan(self.recv_socket.t):
            try:
                self.recv_socket.recv(self.connection_timeout)
            except socket.timeout:
                raise ConnectionTimeout(
                    "Did not receive initial packet within connection "
                    "timeout.")
            self._update_value()

        while self.recv_socket.t < t - self.remote_dt / 2.:
            self.recv_socket.recv_with_adaptive_timeout()

        if self.recv_socket.t < t + self.remote_dt / 2.:
            self._update_value()

    def _update_value(self):
        self.value = np.array(self.recv_socket.x)

    def send(self, t, x):
        if (np.isnan(self.send_socket.t) or
                (t + self.dt / 2.) >= (self.send_socket.t + self.remote_dt)):
            self.send_socket.send(t, x)


class UDPsendreceive_socket(object):

    def __init__(
            self, listen_addr, remote_addr, remote_dt=None,
            connection_timeout=300., recv_timeout=0.1,loss_limit=0,ignore_timestamp=False, byte_order='='):
        super(UDPsendreceive_socket, self).__init__()
        self.listen_addr = listen_addr
        self.remote_addr = remote_addr
        self.remote_dt = remote_dt
        self.loss_limit =loss_limit
        self.ignore_timestamp=ignore_timestamp
        self.connection_timeout = connection_timeout
        self.recv_timeout = recv_timeout
        self.byte_order = byte_order


    def make_step(self, input_data, output_data, dt):
        recv = _UDPSocket(
            self.listen_addr, output_data, self.byte_order,
            timeout=self.recv_timeout)
        recv.open()
        recv.bind()
        send = _UDPSocket(self.remote_addr, input_data, self.byte_order)
        send.open()
        return socketstep(
            dt=dt,
            send=send, recv=recv,
            remote_dt=self.remote_dt,
            connection_timeout=self.connection_timeout,loss_limit=self.loss_limit,ignore_timestamp=self.ignore_timestamp)








class TCPcommandSocket(object):
        def __init__(self,local_addr, remote_addr,remote_port,connection_timeout=300.):
            self.local_addr =local_addr
            self.remote_addr = remote_addr
            self.remote_port = remote_port
            self.connection_timeout = connection_timeout
            self.list_status = ['start','pause','restart','stop','None']

        
        def connect_host(self):
            print("tcp connect");
   
            connect_thread = threading.Thread(target=self.connect_thread_function,args=())
            connect_thread.start()

        def send_command(self, command):
            if command in self.list_status:
                self.send_sock.send((command).encode("utf-8"))
            else :
                print("not command")
            



        def connect_thread_function(self):
            self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.send_sock.connect((self.remote_addr, self.remote_port))
            self.send_sock.send(("<"+self.local_addr+"> "+("tcpconnection")).encode("utf-8"))

            while True :
                data=  self.send_sock.recv(1024)
                if not data :
                    pass
                else :
                    data=str(data)
                    print("board status :"+data)

        def CleanUP(self):
            self.send_sock.close()

            



        

            
