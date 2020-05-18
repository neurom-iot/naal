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
import config_FPGA
class socket_type(Enum):
    SEND=0
    RECV=1
    NONE=3
class pes_network(object):

    def __init__(self,in_dimensions, out_dimensions, npz_path=None, fpga_name="auto", max_training=None):
        self.fpga_name= fpga_name
        self.in_dimension =in_dimensions
        self.out_dimensions=out_dimensions
        self.max_dt=max_training
        self.__host_info=host_init(fpga_name,in_dimension,out_dimensions)
        self.isinit=False


    def host_info(self):
        return self.__host_info
    
    def NAAL_command  (self, command=socket_type.__init__, reserved=None):
        pass;

    def NAAL_step(self, error =False):
        if self.isinit ==False :
            self.__host_info.build_pes_network("fpen_args_140027362053704.npz")
            self.__host_info.connect()
            self.isinit=True
            return 

        

            






