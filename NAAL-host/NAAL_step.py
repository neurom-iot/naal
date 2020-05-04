from __future__ import absolute_import
import config_FPGA
import socket
import sys
import threading
import numpy as np
from enum import Enum
import time
import config_FPGA
class board_command(Enum):
    INIT=0
    START=1
    PROCEEDING=2
    PAUSE=3
    STOP=4
class socket_type(Enum):
    SEND=0
    RECV=1
    NONE=3
class naal_socket(object):
    def __init__(self, IP_addr,bufer_size,stepcnt=0,type=socket_type.RECV,command=board_command.INIT):
        self.IP_addr =IP_addr
        self.type=type
        self.commandlist=[]
        self.commandlist.append(command)
        # command[0], step[1]
        self.message = np.empty(bufer_size+2)
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

    def send(self,dt, vector_data,command=board_command.PROCEEDING):

        self.message[0] =  command.value
        self.message[1] = dt
        self.message[2:] = vector_data
        self._socket.sendto(self.message.tobytes(), self.IP_addr)

class NAAL_UDPnetwork(object):
    #int(np.random.uniform(low=20000, high=65535))
    #host_IP or remote=(config_FPGA.config_parser('host', 'ip'),udp_port)
    def __init__(self, host_IP,remote_IP,in_demesion,out_demension):
        self.host_IP=host_IP
        self.remote_IP=remote_IP
        #command [0] step[1]
        self.in_demesion=in_demesion
        self.out_demension=out_demension
        self.dt=0.0
        self.send=naal_socket(self.remote_IP,self.in_demesion,self.dt,socket_type.SEND)
        self.recv =naal_socket(self.host_IP,self.out_demension,self.dt,socket_type.RECV)
        self.send.set_command(board_command.INIT)
        self.send()
        self.recv.set_command(board_command.INIT)
        self.recv()
        self.recv.recv()
        print("host recv :")
        print(self.recv.message);
        initarr=[]
        for i in range(0,self.in_demesion):
           initarr.append(0.0)
        tuple(initarr)
        self.send.send(0,initarr,board_command.START)
        self.send.set_command(board_command.PROCEEDING)
        


    def step_call(self,vector):
       
        if self.send.command ==board_command.PROCEEDING.value:
            self.send.send(self.dt,vector)
        elif self.send.command ==board_command.PAUSE.value:
            self.send.send(self.dt,vector,board_command.PAUSE)
        elif self.send.command ==board_command.STOP.value:
            self.send.closed
            self.recv.closed

        self.recv.recv()
        if self.recv.dt == self.dt:
            self.recv.set_command(board_command.PROCEEDING)
            print(self.recv.message)

        ##중간 보고 0501 dt값의 증가를 구현해야함
        #self.dt+=0.001

# test 예제 수행가능함
#config =config_FPGA.Is_fpgaboard("pynq")
#print(config_FPGA.config_parser('host', 'ip'))
#udp_port = int(np.random.uniform(low=20000, high=65535))
#addd=(config_FPGA.config_parser('host', 'ip'),udp_port)
#test =NAAL_UDPnetwork(addd,addd,10)
#initarr=[0,0]
## 0 커맨드 1 step
#for i in range(0,2):
#    initarr.append(1.4)
#test.step_call(i)

fpga_name= "pynq"
in_dimension =4
out_dimensions=2
learning_rate=0.01
##
#host_init(fpga_name,self.in_dimension+self.out_dimensions,self.out_dimensions,self.learning_rate,socket_args)
#test=host_init(fpga_name,in_dimension,out_dimensions)
#test.build_pes_network("fpen_args_mnist.npz")
#test.connect()
#config =config_FPGA.Is_fpgaboard("pynq")
#print(config_FPGA.config_parser('host', 'ip'))
#udp_port = int(8080)
#addr=(config_FPGA.config_parser('host', 'ip'),udp_port)
#remote=(config_FPGA.config_parser(fpga_name, 'ip'),udp_port)
#naaltest =NAAL_UDPnetwork(addr,remote,196,10)
