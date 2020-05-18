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
    PAUSE=2
    STOP=3
    NONE=4
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
    def set_dt(self,dt):
        self.message[1]=dt

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


class TCPcommandSocket(object):
        def __init__(self,local_addr,remote_port):
            self.local_addr =local_addr
            self.remote_port = remote_port
            self.remote_addr = (self.local_addr,self.remote_port)

        def connect_host(self):
            print("command tcp connect");
            connect_thread = threading.Thread(target=self.connect_thread_function,args=())
            
            connect_thread.start()


        def connect_thread_function(self):
            self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.send_sock.bind((self.remote_addr))
            self.data=None
            self.send_sock.listen(1)
            self.client_socket,addr =self.send_sock.accept()
            while True :
                self.data=  self.client_socket.recv(1024)
                if not self.data :
                    pass
                else :
                    self.data=str(data.decode("utf-8"))

        def CleanUP(self):
            self.send_sock.close()
        def send_board_command(self,boardcommand=board_command.INIT):

            self.client_socket.send((str(boardcommand.value)).encode("utf-8"))
            try :
                return_value=int(self.data)
                return board_command(return_value)                                                   
            except :
                print(self.data)
                return None

class NAAL_UDPnetwork(object):
    #int(np.random.uniform(low=20000, high=65535))
    #host_IP or remote=(config_FPGA.config_parser('host', 'ip'),udp_port)
    def __init__(self, host_IP,remote_IP,tcp_port,in_demesion,out_demension):
        self.host_IP=host_IP
        self.remote_IP=remote_IP
        self.currcommand=board_command.INIT
        self.tcp_addr =TCPcommandSocket(self.host_IP[0],tcp_port)
        self.tcp_addr.connect_host()
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
        self.send.set_command(board_command.START)
        self.recv.recv()
        print("host Init  out_value: ")
        print(self.recv.message);    

        self.currcommand =board_command.PAUSE
       


    def send_boardcommand(self,boardcommand=board_command.INIT):
        #동기화문제로 정상작동 x 수정하거나 주석삭제
        temp =self.tcp_addr.send_board_command(boardcommand)
       # if temp == None :
       ##     return
       # self.currcommand=temp
        self.currcommand=boardcommand
        
    def step_call(self,vector):

        if self.currcommand is board_command.START :
            self.send.send(self.dt,vector)
            temp_dt =self.send.dt
        elif self.currcommand is board_command.PAUSE:
            #동기화문제 보내야하나 말아야하나 리얼타임 dt기준으로 하면 살리고 나서 보드에서 쓸모없는값을 전송 아니라면 그냥 return 
            #self.send.send(self.dt,vector,board_command.PAUSE)
            return
        elif self.currcommand is board_command.STOP:
            self.send.closed
            self.recv.closed
            self.tcp_addr.CleanUP()

        self.recv.recv()
        ##if self.recv.dt == self.dt:
        self.recv.set_command(board_command.START)
        self.send.set_dt(self.recv.dt)
        self.recv.set_dt(self.recv.dt)

        print(self.recv.message)           



 

            



        


        


        
        
