import socket
import sys
import threading
import numpy as np
from enum import Enum
class board_command(Enum):
    INIT=0
    START=1
    PAUSE=2
    STOP=3
    NONE=4
class socket_type(Enum):
    SEND=0
    RECV=1
    NONE=3
class naal_socket(object):
    def __init__(self, IP_addr,dimensions,type=socket_type.RECV ,command=board_command.INIT):
        self.IP_addr =IP_addr
        self.type=type
        self.dimensions=dimensions

        self.message = np.empty(self.dimensions+2)
        self.message[0] = np.nan
        
        self._socket = None
        self.open()

    def __call__(self):
        if self.type.value == socket_type.RECV.value :
            self.open()
            self._socket.bind(self.IP_addr)
        else :
            self.open()

    @property
    def command(self):
        return self.message[0]
    def set_command(self,command):
        self.message[0]=command.value
    @property
    def dt(self):
        return self.message[1]
    @property
    def vector(self):
        return self.message[2:]
    @vector.setter
    def vector(self,vector):
        self.message[2:]=vector            
    @property
    def closed(self):
        return self._socket is None
    def open(self):
        try :
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            if sys.platform.startswith('bsd') or sys.platform.startswith('darwin'):
                self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            else:
                self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        except ValueError : 
            print("socket errorIP :"+IP_addr+" socket exit")
            return
    def recv(self):
        self._socket.recv_into(self.message.data)

    def send(self,dt, vector_data,command=board_command.START):

        self.message[0] =  command.value
        self.message[1] = dt
        self.message[2:] = vector_data
        self._socket.sendto(self.message.tobytes(), self.IP_addr)

class NAAL_UDPnetwork(object):
    def __init__(self, host_IP,remote_IP,in_demesion,out_demension):
        self.host_IP=host_IP
        self.remote_IP=remote_IP
        self.in_demesion=in_demesion
        self.out_demension=out_demension
        #command [0] step[1]
        self.dt=0.0
        self.recv=naal_socket(self.remote_IP,self.in_demesion)
        self.send =naal_socket(self.host_IP,self.out_demension,socket_type.SEND)
        self.recv()
        self.send()
        initarr=[]
        for i in range(0,self.out_demension):
           initarr.append(0.0)
        tuple(initarr)
        self.send.send(0,initarr,board_command.START)
        self.send.set_command(board_command.START)
        self.recv.recv()
        print("board recv:")
        print(self.recv.message)

        # print(self.recv.message)
        # print("while")
        #self.send()
        # print("test")
        # self.recv.recv()
        # while True :
        #     self.send.send(0,initarr,board_command.START)
        #     print("asdasd")
        # self.send.send(0,initarr,board_command.START)
        # self.send.set_command(board_command.PROCEEDING)
        # self.dt=0.0



    def step_call_recv(self,dt):
        self.recv.recv()
        self.recv.set_command(board_command.START)
        return self.recv.message

    def step_call_send(self,dt,vector_data):
        self.send.send(dt,vector_data)



class TCPcommandSocket(object):
        def __init__(self,local_addr, remote_addr,remote_port,connection_timeout=300.):
            self.local_addr =local_addr
            self.remote_addr = remote_addr
            self.remote_port = remote_port
            self.connection_timeout = connection_timeout
            self.sim_status=board_command.INIT

        
        def connect_host(self):
            print("tcp connect");
            command=0x00 # connect
   
            connect_thread = threading.Thread(target=self.connect_thread_function,args=())
            connect_thread.start()        
        

        def connect_thread_function(self):
            self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.send_sock.connect((self.remote_addr, self.remote_port))
            print("");
            print("");
            self.sim_status=board_command.NONE
            while True :
                data=  self.send_sock.recv(1024)
                if not data :
                    pass
                else :
                    data = data.decode('utf-8')
                    try : 
                        return_value=int(data)
                        self.sim_status=board_command(return_value) 
                        print("mode change +"+str(self.sim_status));                                                  
                    except :
                        print(self.data)
                        return None
                        


        def CleanUP(self):
            self.send_sock.close()

            