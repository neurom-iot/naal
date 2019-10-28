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
            raise RuntimeError("Must be one of '<', '>', '=', 'little', "
                               "'big'.", attr="byte_order")
        self.byte_order = byte_order
        if np.isscalar(timeout):
            self.timeout = (timeout, timeout)
        else:
            self.timeout = timeout

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

    def bind(self):
        self._socket.bind(self.addr)

    def recv(self, timeout):
        self._socket.settimeout(timeout)
        self._socket.recv_into(self._buffer.data)
        

    def send(self, t, x):
        self._buffer[0] = t
        self._buffer[1:] = x
        print("x size  "+str(len(x)))
        self._socket.sendto(self._buffer.tobytes(), self.addr)
   

    def close(self):
        if not self.closed:
            self._socket.close()
            self._socket = None


class SocketStep(object):


    def __init__(self, dt, send=None, recv=None,
                 remote_dt=None, connection_timeout=None):
        self.send_socket = send
        self.recv_socket = recv
        self.remote_dt = remote_dt
        self.connection_timeout = connection_timeout

        self.dt = dt
        if remote_dt is None:
            remote_dt = dt
        # Cannot run faster than local dt
        self.remote_dt = max(remote_dt, dt)

        # State used by the step function
        self.value = np.zeros(0 if self.recv_socket is None
                              else self.recv_socket.dims)

    def __call__(self, t, x=None):

        if t <= 0.:
            return self.value

        if self.send_socket is not None:
            assert x is not None, "A sender must receive input"
            self.send(t, x)
        if self.recv_socket is not None:
            self.recv(t)
        return self.value

    def __del__(self):
        self.close()

    def close(self):
        if self.send_socket is not None:
            self.send_socket.close()
        if self.recv_socket is not None:
            self.recv_socket.close()

    def recv(self, t):
        if np.isnan(self.recv_socket.t):
            try:

                self.recv_socket.recv(self.connection_timeout)
            except socket.timeout:
                raise ConnectionTimeout(
                    "Did not receive initial packet within connection "
                    "timeout.")
            self._update_value()

        while self.recv_socket.t < t - self.remote_dt / 2.:
            self.recv_socket.recv(self.recv_socket.timeout)

        if self.recv_socket.t < t + self.remote_dt / 2.:
            self._update_value()

    def _update_value(self):
        self.value = np.array(self.recv_socket.x)
    # t dt , x, input dimension
    #다음 패킷을 보낼때가 안되었으면 보내지않음 마지막 보낸시간 +remote_dt
    def send(self, t, x):
        if (np.isnan(self.send_socket.t) or
                (t + self.dt / 2.) >= (self.send_socket.t + self.remote_dt)):
            self.send_socket.send(t, x)
        else :
            print ("ok")


class UDPSendReceiveSocket(object):

    def __init__(
            self, listen_addr, remote_addr, remote_dt=None,
            connection_timeout=300., recv_timeout=0.1, byte_order='='):
        super(UDPSendReceiveSocket, self).__init__()
        self.listen_addr = listen_addr
        self.remote_addr = remote_addr
        self.remote_dt = remote_dt
        self.connection_timeout = connection_timeout
        self.recv_timeout = recv_timeout
        self.byte_order = byte_order
        print("udpsendrecv init")

    def make_step(self, input_dimensions, output_dimensions, dt):
        recv = _UDPSocket(
            self.listen_addr, output_dimensions, self.byte_order,
            timeout=self.recv_timeout)
        recv.open()
        recv.bind()
        send = _UDPSocket(self.remote_addr, input_dimensions, self.byte_order)
        send.open()
        return SocketStep(
            dt=dt,
            send=send, recv=recv,
            remote_dt=self.remote_dt,
            connection_timeout=self.connection_timeout)


class TCPcommandSocket(object):
        def __init__(self,local_addr, remote_addr,remote_port,connection_timeout=300.):
            self.local_addr =local_addr
            self.remote_addr = remote_addr
            self.remote_port = remote_port
            self.connection_timeout = connection_timeout

        
        def connect_host(self):
            print("tcp connect");
   
            connect_thread = threading.Thread(target=self.connect_thread_function,args=())
            connect_thread.start()


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
                    print(data)

        def CleanUP(self):
            self.send_sock.close()

            



        

            
