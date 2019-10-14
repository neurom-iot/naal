import socket
import os
import threading
import paramiko
import numpy as np
import config_FPGA

class host_Init(object):
 
    def __init__(self, fpga_name, max_attempts=5, timeout=5):
        self.config =config_FPGA.Is_FPGABOAD(fpga_name)
        self.timeout=timeout
        self.max_attempts=max_attempts
        self.fpganame=fpga_name

        # Make SSHClient object
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())      
        self.ssh_info_str = ''
        self.ssh_lock = False

        self.tcp_port =int(self.config['tcp_port'])
        self.tcp_init= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_init.bind(('192.168.1.30',8585))
        self.tcp_init.listen(1)
        print("listen ....");
        print('Shell_extractor ssh,tcp socket create')

    def cleanup(self):
        self.tcp_init.close()
        self.ssh_client.close()

        if self.tcp_recv is not None:
            self.tcp_recv.close()

    @property
    def ssh_string(self):

        # Generate the string to be sent over the ssh connection to run the
        # remote side ssh script (with appropriate arguments)
        ssh_str = ('python ' + self.config['test_script'] +' --host_ip="%s"' % config_FPGA.config_parser("host","ip")+' --tcp_port=%i' % self.tcp_port +'\n')

        return ssh_str

    def connect_thread_function(self,command):
        remote_ip = self.config['ip']

        # Get the SSH options from the fpga_config file     
        ssh_port = self.config['ssh_port']
        ssh_user = self.config['ssh_user']
        ssh_pwd = self.config['ssh_pwd']

        self.ssh_client.connect(remote_ip, port=ssh_port,
        username=ssh_user, password=ssh_pwd)

        # Invoke a shell in the ssh client
        ssh_channel = self.ssh_client.invoke_shell()

        if ssh_user != 'root':
            print('<%s> Script to be run with sudo. Sudoing.' %
                  remote_ip, flush=True)
            ssh_channel.send('sudo su\n')
        if command is "connect":
            send_str =self.ssh_string
        else :
            send_str=command

        # Send required ssh string
        print("send command ");
        print("<%s> Sending cmd to fpga board: \n%s" % (self.config['ip'],send_str), flush=True)
        ssh_channel.send(send_str)

        got_error = 0
        error_strs = []

        while True:
            data = ssh_channel.recv(256)

            if not data:
                ssh_channel.close()
                break

            self.process_ssh_output(data)
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

    def send_command(self,command):
        print("<%s> Open SSH connection" %
              self.config['ip'], flush=True)
        connect_thread = threading.Thread(target=self.connect_thread_function, args=(command,))
        connect_thread.start()

    def connect(self):
        print("<%s> Open SSH connection" %
              self.config['ip'], flush=True)
        command=0x00 # connect
        connect_thread = threading.Thread(target=self.connect_thread_function, args=("connect",))
        connect_thread.start()

    def recv_id(self):
        client_socket,addr = self.tcp_init.accept()
        
        self.id_bytes= client_socket.recv(8)
        self.id_int=int.from_bytes(self.id_bytes, 'big')
        id_str = "Found board ID: 0x%0.16X" % self.id_int
        print(id_str)
        

    def process_ssh_output(self, data):
        # Clean up the data stream coming back over ssh
        str_data = data.decode('latin1').replace('\r\n', '\r')
        str_data = str_data.replace('\r\r', '\r')
        str_data = str_data.replace('\r', '\n')

        # Process and dump the returned ssh data to logger. Data (strings)
        # returned over SSH are terminated by a newline, so, keep track of
        # the data and write the data to logger only when a newline is
        # received.
        self.ssh_info_str += str_data

test=host_init('pynq')
test.connect()
test.recv_id()     
