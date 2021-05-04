
import socket
import os
import threading
import paramiko
import numpy as np
import config_FPGA
import npzFile
import random
from NAAL_step import naal_socket
from NAAL_step import NAAL_UDPnetwork
from NAAL_step import TCPcommandSocket
from NAAL_step import board_command
import time
import sys
import numpy as np


# 종료시 소켓 및 레지정리 미구현
import atexit



class host_init(object):
    def __init__(self, fpga_name, n_neurons, dimensions,params_path, learning_rate=0.01,error_rate=False, socket_args={}):
        self.exist_map={}
        fpga_name=self.__select_board(fpga_name,params_path)
        #fpga_name='de1'
        #print("selected board : " + str(fpga_name))
        self.config =config_FPGA.Is_fpgaboard(fpga_name)
        self.fpga_name=fpga_name
        self.tcp_port = random.randint(int(config_FPGA.config_parser(self.fpga_name, 'tcp_port')), int(config_FPGA.config_parser(self.fpga_name, 'tcp_port'))+ 100)
        self.udp_port =int(config_FPGA.config_parser(self.fpga_name, 'udp_port'))
        self.tcp_socket=None
        self.udp_socket=None
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_info_str = ''
        self.ssh_lock = False
        self.fpga_name = fpga_name
        self.arg_data_path = os.curdir
        self.arg_data_file = ''
        #[command][step][vector ....][output ..]
        self.in_dimensions = n_neurons+dimensions
        self.out_dimensions= dimensions

        self.neuron_map={
            'RectifiedLinear','SpikingRectifiedLinear'
            }

        self.EET_culculration(1)
        self.EET_culculration(2)
        self.EET_culculration(3)
        self.EET_culculration(4)
        self.EET_culculration(5)
        self.EET_culculration(6)
        self.EET_culculration(7)
        #print("test용 삭제");
        #exit(0);

        self.learning_rate =learning_rate;
        self.udp_port =8080 #int(np.random.uniform(low=20000, high=65535))
        
        socket_kwargs = dict(socket_args)
        socket_kwargs.setdefault('recv_timeout', 0.1)

        #self.udp_socket = sockets.UDPsendreceive_socket(
        #    listen_addr=(config_FPGA.config_parser('host', 'ip'), self.udp_port),
        #    remote_addr=(config_FPGA.config_parser(fpga_name, 'ip'), self.udp_port),**socket_kwargs, ignore_timestamp=True)
    def CheckexecutionTime(self):
        i=0
       # 192.168.1.66
        neuron_map={}
        while True:
            if i ==0 :
                if (config_FPGA.config_parser('de1_1', 'ip')) ==True:
                    neuron_map['de1']=0
                if (config_FPGA.config_parser('host', 'de1')) ==True:
                    neuron_map['pynq']=0
                if (config_FPGA.config_parser('host', 'de1')) ==True:
                    neuron_map['loihi']=0
                continue

            #de1='de1_'+i
            #pynq='pynq_'+i
            #loihi='loihi_'+i
            #checkpass=False 
            #if (config_FPGA.config_parser('host', de1)) ==True:
            #    neuron_map['de1']=0
            #    checkpass=True
            #if (config_FPGA.config_parser('host', pynq)) ==True:
            #    neuron_map['pynq']=0
            #    checkpass=True
            #if (config_FPGA.config_parser('host', loihi)) == True:
            #    neuron_map['loihi']=0
            #    checkpass=True
            #if checkpass ==False :
            #    break
            #i=i+1
    #현재 미구현상태로 ET만
    def selecting_minimumEET_NA(self):
        selectedNA=""
        selectedNA_EET=1.0
        min=1.0
        for NA in self.exist_map:
            #executiontime ->EET 로 변경해야함 현재 EET 미구현
            min=float(config_FPGA.config_parser(NA,"executiontime"))
            if(selectedNA_EET>min ):
                selectedNA=NA
                selectedNA_EET=min
        if selectedNA=="" :
            print("Error SelectedNA Not exist")
            exit()
       
        print("selectedNA %s" % selectedNA)
        return selectedNA


    def set_excutintime(self,executiontime):
        config_FPGA.set_config(self.fpga_name,'executiontime',executiontime);

    #만약 에러가 발생한다면 호출
    #error 가발생했을 경우 (msg[1]= 5인경우)
    #기존에 적힌 errorrate를 읽은후 1/2 //임시 오류율임
    ##이단계일때 EET를 다시 계산하도록 구현
    def set_errorrate(self):
        error=float(config_FPGA.config_parser(NA,"errorrate"))
        config_FPGA.set_config(self.fpga_name,'errorrate',error/2.0);
        
    
    def EET_culculration(self,n=0):
        p=float(config_FPGA.config_parser(self.fpga_name,"errorrate"))
        #print("p : " + str(p))
        p=1-p
        if p >1 :
           print("EET_culculration() error : p value is in correct p ="+str(p))
        a=float(config_FPGA.config_parser(self.fpga_name,"executiontime"))
        a=a*30
        if (n==0):
            n=int(config_FPGA.config_parser(self.fpga_name,"n_step"))
        temp =0.0;
        for k in range(0,n+1):
            temp+=((k+1)*((1-p)**k)*p)
            #print("temp ="+str(temp)+"k="+str(k))

        #print("a="+str(a)+"n="+str(n))
        EET_vaule =(a/n)*temp
        print("EET_value ="+str(EET_vaule))
        if (n > 1 ):
            EET_vaule+=a
        #추정 시간이라 x30 나중에 수정

        print("EET:"+str(EET_vaule))
        config_FPGA.set_config(self.fpga_name,'EET',EET_vaule);



        
    def __select_board(self,fpga_name,params_path, error_Mode=False,minmum_step_time = 0.003):
        de1_check=False
        pynq_check=False
        self.arg_data_file =params_path
   
        if fpga_name == "auto":
            arg_data = np.load(self.arg_data_file, encoding='latin1',allow_pickle=True)
            sim_args = arg_data['sim_args'].item()
            ens_args = arg_data['ens_args'].item()
            conn_args = arg_data['conn_args'].item()
            
            # Various model parameters
            self.dt = sim_args['dt']
            
            n_neurons = ens_args['n_neurons']
            #params in & out dimension 
            input_dimensions = ens_args['input_dimensions']
            output_dimensions = ens_args['output_dimensions']
            neuron_type = ens_args['neuron_type']
            bias = ens_args['bias']
            scaled_encoders = ens_args['scaled_encoders']
            
            learning_rate = conn_args['learning_rate']
            weights = conn_args['weights']

            if (n_neurons * max(input_dimensions, output_dimensions) > 32768):
                raise AttributeError('Maximum supported N * D is 32,768.')
            if (n_neurons > 16384):
                raise AttributeError('Maximum supported N is 16,384.')
            if (max(input_dimensions, output_dimensions) > 1024):
                raise AttributeError('Maximum supported D is 1024.')

            if (n_neurons * max(input_dimensions, output_dimensions) > 16000):
                pynq_check =True
            elif (n_neurons * max(input_dimensions, output_dimensions) < 16000):
                de1_check= True
                pynq_check =True

            if pynq_check:
                if self.config_listcheck("pynq")==False:
                    print("Not pynq board configuration")
            if de1_check:
                if self.config_listcheck("de1")==False:
                    print("Not pynq board configuration")
            if len(self.exist_map) ==0:
                print("Error : not exist NA ")
                exit()

            return self.selecting_minimumEET_NA()

        if fpga_name =="pynq"or pynq_check:
            return fpga_name                       
        if fpga_name =="de1" or de1_check:
            return fpga_name;
        #not implement

        if fpga_name =="loihi":
            return fpga_name  
        print("not exist board");
        exit();


    def config_listcheck(self,fpga_name):
        exist_name=fpga_name
        i=0
        while True :
            i=i+1
            if config_FPGA.config_parser_board(exist_name,"ip"):
                self.exist_map[exist_name]=config_FPGA.config_parser(exist_name,"EET")
            else :
                break;
            exist_name=exist_name+"_"+str(i)

        if i ==0:
            return False
        return True

    @property
    def local_data_filepath(self):
        return os.path.join(self.arg_data_path, self.arg_data_file)  
    
    @property
    def ssh_command(self):
        ssh_str = \
            ('python ' + config_FPGA.config_parser(self.fpga_name, 'NAAL_script') +
             ' --host_ip="%s"' % config_FPGA.config_parser('host', 'ip')
           + ' --remote_ip="%s"' % config_FPGA.config_parser(self.fpga_name, 'ip')
          + ' --udp_port=%i' % self.udp_port 
          +' --tcp_port=%i' % self.tcp_port
          +' --in_dimensions=%i' % self.in_dimensions
          +' --out_dimensions=%i' % self.out_dimensions
          + ' --arg_data_file="%s/%s"' %
             (config_FPGA.config_parser(self.fpga_name, 'NAAL_tmp'),
             self.arg_data_file) + '\n')
        return ssh_str
    def connect_thread_function(self,command):
        remote_ip = self.config['ip'] 
        ssh_port = self.config['ssh_port']
        ssh_user = self.config['ssh_user']
        ssh_pwd = self.config['ssh_pwd']
        
        if self.fpga_name is 'pynq':
            self.ssh_client.connect(remote_ip, port=ssh_port,
            username=ssh_user, password=ssh_pwd)
  
  #lsy
        if self.fpga_name is 'de1':
            #privatekeyfile = os.path.expanduser('~/.ssh/id_rsa')
            privatekeyfile = os.path.expanduser('/home/pi/.ssh/id_rsa')
            mykey = paramiko.RSAKey.from_private_key_file(privatekeyfile, "oslab")
            self.ssh_client.connect(remote_ip, username=ssh_user, pkey = mykey)
  #lsy 

        #리눅스에서 해당 명령어 안됨 수정요망 if문이안됨
        #리눅스에선 send _str = connect 로 수정    if문삭제하고          
        send_str =self.ssh_command
#        if ssh_pwd is not None:
#            self.ssh_client.connect(remote_ip, port=ssh_port,
#                                    username=ssh_user, password=ssh_pwd)
#        else:
#            self.ssh_client.connect(remote_ip, port=ssh_port,
#                                    username=ssh_user)
    
    
        remote_data_filepath = \
            '%s/%s' % (config_FPGA.config_parser(self.fpga_name, 'NAAL_tmp'),
                       self.arg_data_file)
    
        print("remote_data_file path"+remote_data_filepath)
        print("npz_file_path "+(self.local_data_filepath))
    
        #if not os.path.exists(self.local_data_filepath):
        #    print("none npz file exit")
        #    exit()

        print("local data"+self.local_data_filepath)
        ssh_channel = self.ssh_client.invoke_shell()
        if ssh_user != 'root':
            print('<%s> Script to be run with sudo. Sudoing.' %
                  remote_ip, flush=True)
            ssh_channel.send('sudo su\n')
    
    
        ssh_channel.send(send_str)
   
        got_error = 0
        error_strs = []
    
        got_error = 0
        error_strs = []
        # Create sftp connection
        sftp_client = self.ssh_client.open_sftp()
    
    
        #리눅스 사용시
        if os.path.isfile(self.local_data_filepath):
            sftp_client.put(self.local_data_filepath, remote_data_filepath)
    
    
        while True:
            data = ssh_channel.recv(256)
            if not data:                                    
    
                ssh_channel.close()
                break
    
            self.ssh_output_string(data)
            info_str_list = self.ssh_info_str.split('\n')
            for info_str in info_str_list[:-1]:
                if info_str.startswith('Killed'):
                    print('<%s> ENCOUNTERED ERROR!' % remote_ip, flush=True)
                    got_error = 2
    
                if info_str.startswith('Traceback'):
                    print('<%s> ENCOUNTERED ERROR!' % remote_ip, flush=True)
                    got_error = 1
                elif got_error > 0 and info_str[0] != ' ':
                    got_error = 2
    
                if got_error > 0:
    
                    error_strs.append(info_str)
                else:
                    print('<%s> %s' % (remote_ip, info_str), flush=True)
            self.ssh_info_str = info_str_list[-1]
            
            if got_error == 2:
                ssh_channel.close()
                raise RuntimeError(
                    'Received the following error on the remote side <%s>:\n%s'
                    % (remote_ip, '\n'.join(error_strs)))
    
    def connect(self):
        print("<%s> Open SSH connection" %
              self.config['ip'], flush=True)
        command=0x00 # connect
        connect_thread = threading.Thread(target=self.connect_thread_function,
                                          args=("connect",))
        connect_thread.start()
        self.host_addr=(config_FPGA.config_parser('host', 'ip'),self.udp_port)
        self.remote_addr=(config_FPGA.config_parser(self.fpga_name, 'ip'),self.udp_port)
        #self.tcp_socket = TCPcommandSocket(config_FPGA.config_parser('host', 'ip'),config_FPGA.config_parser(self.fpga_name, 'ip'),self.tcp_port)
       # self.tcp_socket.connect_host()
       
        self.udp_socket=NAAL_UDPnetwork(self.host_addr,self.remote_addr,self.tcp_port,self.in_dimensions,self.out_dimensions)

        

    def ssh_output_string(self, data):
        str_data = data.decode('latin1').replace('\r\n', '\r')
        str_data = str_data.replace('\r\r', '\r')
        str_data = str_data.replace('\r', '\n')
        self.ssh_info_str += str_data

    def build_pes_network(self,npz_filename):
        #if sys.platform.startswith('win') :
        #    self.npz_filename=npz_filename
        #    self.arg_data_file =npz_filename
            
        self.npz_filename=npz_filename
        self.arg_data_file =npz_filename

    def board_command(self, command,reserved):
        #reserved is Not Implemented
        if command.value is (board_command.INIT).value:
            self.connect()
            return
        self.udp_socket.send_boardcommand(command)
     
    def checking_npz(self,filepath=None):
        if filepath is None:
            arg_data = np.load(self.local_data_filepath, encoding='latin1',allow_pickle=True)
        else:
            arg_data=np.load(filepath)
            print("============npz")                                                                                                               

        sim_args = arg_data['sim_args'].item()
        ens_args = arg_data['ens_args'].item()
        conn_args = arg_data['conn_args'].item()

        # Various model parameters
        self.dt = sim_args['dt']
        n_neurons = ens_args['n_neurons']
        self.input_dimensions = ens_args['input_dimensions']
        self.output_dimensions = ens_args['output_dimensions']
        neuron_type = ens_args['neuron_type']
        bias = ens_args['bias']
        scaled_encoders = ens_args['scaled_encoders']

        learning_rate = conn_args['learning_rate']
        weights = conn_args['weights']

        # Check that the ensemble will fit on the fpga
        if (n_neurons * max(self.input_dimensions,
                            self.output_dimensions) > 32768):
            raise AttributeError('Maximum supported N * D is 32,768.')
        if (n_neurons > 16384):
            raise AttributeError('Maximum supported N is 16,384.')
        if (max(self.input_dimensions, self.output_dimensions) > 1024):
            raise AttributeError('Maximum supported D is 1024.')



#fpga_name= "pynq"
#in_dimension =196

#out_dimensions=10
#learning_rate=0.01
#test=host_init(fpga_name,in_dimension,out_dimensions)
#test.build_pes_network("fpen_args_140027362053704.npz")
#test.connect()
#initarr=[]
#arr=[ -0.99999982, -0.99999982, -0.99999982, -0.99999982, -0.99999982, -0.99999982 ,
# -0.99999982, -0.99999982, -0.99999982, -0.99999982, -0.99999982, -0.99999982 ,
# -0.99999982, -0.99999982, -0.99993724, -1.00001895, -1.00018394, -0.97852391 ,
# -0.97361755, -0.98755383, -0.99448031, -0.99436629, -0.99441528, -0.99412483 ,
# -0.99688542, -1.00020802, -0.99995738, -0.99999422, -1.00037062, -0.99956846 ,
# -1.000301  , -1.11846364, -1.14392531, -1.0661819 , -1.02240407, -1.02133191 ,
# -1.02200174, -1.02104914, -1.00115299, -0.99860108, -1.0003686 , -0.99997777 ,
# -0.99807757, -1.00098097, -1.00434256, -0.35019329, -0.20200004, -0.68225461 ,
# -0.93153632, -0.93776047, -0.93234223, -0.92379862, -1.01715457, -1.00645006 ,
# -0.99823505, -1.00017107, -0.99572438, -1.0100497 , -0.96687561,  0.21046254 ,
#  0.41991907,  0.60456067,  0.59101242,  0.62949377,  0.60421276,  0.63887888 ,
#  0.17215104, -1.03205812, -0.99579549, -0.99698889, -1.00026083, -0.99901474 ,
# -1.00238538, -1.0637399 , -1.08755708, -0.87971812, -0.70014888, -0.59729546 ,
# -0.7704674 ,  0.37011743,  0.30798629, -1.10766518, -0.98368192, -0.99784207 ,
# -0.99995798, -1.00023079, -0.99937618, -0.99168265, -0.98864633, -1.02984595 ,
# -1.04689217, -1.14468837, -0.69366574,  0.8370682 , -0.70495856, -1.07517719 ,
# -0.98372257, -1.00026202, -0.99999231, -1.00000846, -0.9999609 , -0.99758428 ,
# -0.99738938, -0.99225742, -0.9640761 , -1.1102016 ,  0.43997291,  0.14614365 ,
# -1.1324141 , -0.97457147, -0.99944866, -0.99995434, -0.99999982, -1.         ,
# -1.        , -0.99994928, -1.00106263, -0.97882307, -1.09130275, -0.65414655 ,
#  0.694269  , -0.8389056831, -1.04696012, -0.98874271, -1.00014889, -0.99999797 ,
# -0.99999982, -1.        , -0.9999935 , -0.99998665, -0.99338341, -1.00774539 ,
# -0.99664432,  0.66030759,  0.00442731, -1.14107478, -0.97103256, -1.00032341 ,
# -0.99993467, -1.        , -0.99999982, -1.        , -0.99999446, -1.00020993 ,
# -0.9696092 , -1.16439462,  0.04788996,  0.66432226, -0.99485326, -1.01052296 ,
# -0.99317265, -0.99997413, -0.99999952, -1.        , -0.99999982, -1.         ,
# -1.00011349, -0.98284274, -1.07314336, -0.65321428,  0.92115009, -0.57623333 ,
# -1.10393226, -0.97609288, -1.00104666, -0.99995553, -1.        , -1.         ,
# -0.99999976, -1.        , -0.99721801, -0.98630452, -1.0818249 ,  0.428691   ,
#  0.98300523, -0.83287889, -1.03282452, -0.99036288, -0.99982405, -1.         ,
# -1.        , -1.        , -0.99999988, -1.        , -0.99797207, -0.99956781 ,
# -1.02320671, -0.17812452, -0.44231874, -1.05466521, -0.98907381, -0.99921405 ,
# -0.99999088, -1.        , -1.        , -1.        ,                                 0.        ,  0.         ,
#  0.        ,  0.        ,  0.        ,  0.        ,  0.        ,  0.         ,
#  0.        ,  0. ]
#tuple(arr)
#test.udp_socket.step_call(arr)

#test.udp_socket.send_boardcommand(board_command.START)
#test.udp_socket.step_call(arr)
#test.udp_socket.step_call(arr)
#test.udp_socket.step_call(arr)
#test.udp_socket.step_call(arr)   
#test.udp_socket.step_call(arr)
##test.udp_socket.send_boardcommand(board_command.start)
#initarr=[]
#for i in range(0,206):
#   initarr.append(0.0)
#tuple(initarr)
#test.udp_socket.step_call(initarr)
#test.udp_socket.step_call(initarr)
