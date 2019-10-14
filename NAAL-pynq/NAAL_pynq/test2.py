import os
import argparse
import socket
from id_driver import IDDriver

print("NAAL_FPGA board start")

parser = argparse.ArgumentParser(
    description='Generic script for running the ID Extractor on the ' +
    'FPGA board.')

# Socket communication arguments
parser.add_argument(
    '--host_ip', type=str, default='127.0.0.1',
    help='IP Address of host PC. Used for socket communication between the ' +
    'nengo models.')
parser.add_argument(
    '--remote_ip', type=str, default='127.0.0.1',
    help='IP Address of FPGA board. Used for socket communication' +
    'between nengo models.')
parser.add_argument(
    '--udp_ip', type=int, default=500000,
    help='Port number to use for the socket communication.')
parser.add_argument(
    '--socket_args', type=str, default='{}',
    help='Additional arguments used when creating the udp socket. Should be '+
    'formatted as a dictionary string.')
parser.add_argument(
    '--tcp_port', type=int, default=50000,
    help='Port number to use for the socket communication.')
#parser.add_argument(
#    '--arg_data_file', type=str, default=os.path.join(params_path, 'args.npz'),
#    help='Path to parameter arguments (for ensemble, output connection) data' +
#    'file.')

# Parse the arguments
args = parser.parse_args()
print(args.host_ip)

# Driver for ID_extractor bitstream
fpga_driver = IDDriver()

id_str = "Found board ID:" + str(fpga_driver.id_bytes)
print(id_str)
#send_sock= sockets.UDPSendSocket('192.168.1.30',5001)
#send_sock.send("test")

#tcp_init=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
#tcp_init.bind(("",8080))
#tcp_init.listen(1)
#print("server start")
#tcp_init.accept()
#print("join");

print("NAAL_FPGA board socket ");

send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

send_sock.connect(('192.168.1.30',8585))

send_sock.sendall(fpga_driver.id_bytes)

send_sock.close()
#while True:

# If we are local, then print and save ID here
#if args.host_ip == parser.get_default('host_ip'):
#    id_str = "Found board ID: %#0.16X" % fpga_driver.id_int
#    print(id_str)
#    with open("id_pynq.txt", 'w') as file:
#        file.write(id_str + '\n')

# If we havea host connection send the ID back
#else:
    # Using vanilla socket since we are only sending one value
 #   tcp_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  #  tcp_send.connect((args.host_ip, args.tcp_port))
   # tcp_send.sendall(fpga_driver.id_bytes)

    # Close socket
    #tcp_send.close()
