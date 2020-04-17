import sockets
import socket
import os
import threading
import paramiko
import numpy as np
import config_FPGA
import npzFile
import random



class host_init(object):
 
    def __init__(self, fpga_name, n_neurons, dimensions, learning_rate, socket_args={}):
        self.config =config_FPGA.Is_fpgaboard(fpga_name)
        self.fpga_name=fpga_name      
        self.tcp_port =int(config_FPGA.config_parser(self.fpga_name, 'tcp_port'))
        self.tcp_init= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_init.bind((config_FPGA.config_parser('host', 'ip'),8585))
        self.tcp_init.listen(1)
        print("command tcp listens ....")

        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_info_str = ''
        self.ssh_lock = False
        self.fpga_name = fpga_name
        self.arg_data_path = os.curdir
        self.arg_data_file = ''

        self.in_dimensions = dimensions

        self.neuron_map={
            'RectifiedLinear','SpikingRectifiedLinear'
            }

        self.learning_rate =learning_rate;
        self.udp_port = int(np.random.uniform(low=20000, high=65535))
        
        socket_kwargs = dict(socket_args)
        socket_kwargs.setdefault('recv_timeout', 0.1)
        
        self.udp_socket = sockets.UDPsendreceive_socket(
            listen_addr=(config_FPGA.config_parser('host', 'ip'), self.udp_port),
            remote_addr=(config_FPGA.config_parser(fpga_name, 'ip'), self.udp_port),**socket_kwargs, ignore_timestamp=True)
        
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
          + ' --arg_data_file="%s/%s"' %
             (config_FPGA.config_parser(self.fpga_name, 'NAAL_tmp'),
             self.arg_data_file) + '\n')
        return ssh_str

    def connect_thread_function(self,command):
#        test =self.config['ssh_user']
#        print(test)
        remote_ip = self.config['ip'] 
        ssh_port = self.config['ssh_port']
        ssh_user = self.config['ssh_user']
        ssh_pwd = self.config['ssh_pwd']
        self.ssh_client.connect(remote_ip, port=ssh_port,
        username=ssh_user, password=ssh_pwd)

                                        
        #리눅스에서 해당 명령어 안됨 수정요망 if문이안됨
        if command is "connect":         
            send_str =self.ssh_command
        else :
            send_str=command

        if ssh_pwd is not None:
            self.ssh_client.connect(remote_ip, port=ssh_port,
                                    username=ssh_user, password=ssh_pwd)
        else:
            self.ssh_client.connect(remote_ip, port=ssh_port,
                                    username=ssh_user)



        print("send command ");
        print("<%s> Sending cmd to fpga board: \n%s" % (self.config['ip'],send_str), flush=True)


        remote_data_filepath = \
            '%s/%s' % (config_FPGA.config_parser(self.fpga_name, 'NAAL_tmp'),
                       self.arg_data_file)

        print("remote_data_file path"+remote_data_filepath)

        if not os.path.exists(self.local_data_filepath):
            print("none npz file exit")
            exit()
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

    def ssh_output_string(self, data):
        str_data = data.decode('latin1').replace('\r\n', '\r')
        str_data = str_data.replace('\r\r', '\r')
        str_data = str_data.replace('\r', '\n')
        self.ssh_info_str += str_data

    def build_pes_network(self,npz_filename):
        self.npz_filename=npz_filename
        self.arg_data_file =npz_filename

    def command_socketstep_init(self):
        client_socket,addr = self.tcp_init.accept()
        self.tcp_send_sock= client_socket
        data= client_socket.recv(1024)
        print(data)
        data=str(data)
        if data.find("connect"):
            print("tcp initialization success")
        else :
            print("tcp initialization failure")
            exit()

    def send_command(self,command):
        self.tcp_send_sock.send((command).encode("utf-8"))
