import sockets
import socket
import os
import threading
import paramiko
import numpy as np
import config_FPGA
import npzFile
import random
from host_Init import host_init
import time

class pes_network(object):

    def __init__(self, fpga_name, in_dimension, out_dimensions, learning_rate,dt =0.01,host_info=None, socket_args={}):
        self.fpga_name= fpga_name
        self.in_dimension =in_dimension
        self.out_dimensions=out_dimensions

        self.learning_rate =learning_rate
        #보드로 전달되는 사이즈 = 인풋값 + 원핫인코딩된 아웃풋 값
        self.output_size =self.out_dimensions
        self.input_size=self.in_dimension+out_dimensions
        if dt <=0 :
            print("dt error impossible range")
            return 0
        self.__dt=dt
        if host_info is None :
            self.__host_info=host_init(self.fpga_name,self.in_dimension+self.out_dimensions,self.out_dimensions,self.learning_rate,socket_args)
        else :
            self.__host_info=host_info
       

        
    @property
    def dt(self):
        return self.__dt;
    @dt.setter
    def dt(self,dt):
        if dt<=0 :
            print("error : dt value")

        self.__dt =dt

    @property
    def host_info(self):
        return self.__host_info

    #def set_host_info(self,host_info=None,socket_args={}):

    #    if host_info is None :
    #        self.__host_info=host_init(self.fpga_name,self.in_dimension+self.out_dimensions,self.out_dimensions,self.learning_rate,socket_args)
    #    else :
    #        if self.__host_info is not None :
    #            del __host_info
    #            self.fpga_name= fpga_name
    #            self.in_dimension =in_dimension
    #            self.out_dimensions=out_dimensions
    #            self.learning_rate =learning_rate
                

    #        self.__host_info= host_info

    def init_pes(self,npzFile=None):
        if npzFile is None :
            self.__host_info.build_pes_network("fpen_args_mnist.npz")
        else:
            self.__host_info.build_pes_network(npzFile.filepath)
        self.__host_info.connect()                             
        self.__host_info.command_socketstep_init()
        self.step=self.__host_info.udp_socket.make_step(self.in_dimension+self.out_dimensions,self.out_dimensions,self.__dt)



test =pes_network('pynq',196,10,0)
test.init_pes()

initarr=[]
for i in range(0,206):
    initarr.append(0.0)
test.step(0.001,initarr)
time.sleep(5)


arr=[ -0.99999982, -0.99999982, -0.99999982, -0.99999982, -0.99999982, -0.99999982 ,
 -0.99999982, -0.99999982, -0.99999982, -0.99999982, -0.99999982, -0.99999982 ,
 -0.99999982, -0.99999982, -0.99993724, -1.00001895, -1.00018394, -0.97852391 ,
 -0.97361755, -0.98755383, -0.99448031, -0.99436629, -0.99441528, -0.99412483 ,
 -0.99688542, -1.00020802, -0.99995738, -0.99999422, -1.00037062, -0.99956846 ,
 -1.000301  , -1.11846364, -1.14392531, -1.0661819 , -1.02240407, -1.02133191 ,
 -1.02200174, -1.02104914, -1.00115299, -0.99860108, -1.0003686 , -0.99997777 ,
 -0.99807757, -1.00098097, -1.00434256, -0.35019329, -0.20200004, -0.68225461 ,
 -0.93153632, -0.93776047, -0.93234223, -0.92379862, -1.01715457, -1.00645006 ,
 -0.99823505, -1.00017107, -0.99572438, -1.0100497 , -0.96687561,  0.21046254 ,
  0.41991907,  0.60456067,  0.59101242,  0.62949377,  0.60421276,  0.63887888 ,
  0.17215104, -1.03205812, -0.99579549, -0.99698889, -1.00026083, -0.99901474 ,
 -1.00238538, -1.0637399 , -1.08755708, -0.87971812, -0.70014888, -0.59729546 ,
 -0.7704674 ,  0.37011743,  0.30798629, -1.10766518, -0.98368192, -0.99784207 ,
 -0.99995798, -1.00023079, -0.99937618, -0.99168265, -0.98864633, -1.02984595 ,
 -1.04689217, -1.14468837, -0.69366574,  0.8370682 , -0.70495856, -1.07517719 ,
 -0.98372257, -1.00026202, -0.99999231, -1.00000846, -0.9999609 , -0.99758428 ,
 -0.99738938, -0.99225742, -0.9640761 , -1.1102016 ,  0.43997291,  0.14614365 ,
 -1.1324141 , -0.97457147, -0.99944866, -0.99995434, -0.99999982, -1.         ,
 -1.        , -0.99994928, -1.00106263, -0.97882307, -1.09130275, -0.65414655 ,
  0.694269  , -0.83890831, -1.04696012, -0.98874271, -1.00014889, -0.99999797 ,
 -0.99999982, -1.        , -0.9999935 , -0.99998665, -0.99338341, -1.00774539 ,
 -0.99664432,  0.66030759,  0.00442731, -1.14107478, -0.97103256, -1.00032341 ,
 -0.99993467, -1.        , -0.99999982, -1.        , -0.99999446, -1.00020993 ,
 -0.9696092 , -1.16439462,  0.04788996,  0.66432226, -0.99485326, -1.01052296 ,
 -0.99317265, -0.99997413, -0.99999952, -1.        , -0.99999982, -1.         ,
 -1.00011349, -0.98284274, -1.07314336, -0.65321428,  0.92115009, -0.57623333 ,
 -1.10393226, -0.97609288, -1.00104666, -0.99995553, -1.        , -1.         ,
 -0.99999976, -1.        , -0.99721801, -0.98630452, -1.0818249 ,  0.428691   ,
  0.98300523, -0.83287889, -1.03282452, -0.99036288, -0.99982405, -1.         ,
 -1.        , -1.        , -0.99999988, -1.        , -0.99797207, -0.99956781 ,
 -1.02320671, -0.17812452, -0.44231874, -1.05466521, -0.98907381, -0.99921405 ,
 -0.99999088, -1.        , -1.        , -1.        ,  0.        ,  0.         ,
  0.        ,  0.        ,  0.        ,  0.        ,  0.        ,  0.         ,
  0.        ,  0. ]

test.step(0.003,arr)
t= 0.001
while True :
  
    if(t>0.1):
        break
    test.step(t,arr)
    t=t+0.002
    time.sleep(2)
