from __future__ import print_function
import os
import argparse
import atexit

import os
import argparse
import socket
from pes_driver import PESDriver
from utils.paths import params_path
from sockets import UDPSendReceiveSocket
from sockets import TCPcommandSocket

def cleanup(fpga_driver, socket_step):
    # Terminate the fpga driver
    fpga_driver.terminate()

    # Close and cleanup the UDP socket
    socket_step.close()
print("NAAL_FPGA board start")

parser = argparse.ArgumentParser(
    description='Generic for running the pes network on the fpga board.')

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
    '--udp_port', type=int, default=500000,
    help='Port number to use for the socket communication.')
parser.add_argument(
    '--socket_args', type=str, default='{}',
    help='Additional arguments used when creating the udp socket. Should be '+
    'formatted as a dictionary string.')
parser.add_argument(
    '--tcp_port', type=int, default=50000,
    help='Port number to use for the socket communication.')

parser.add_argument(
    '--arg_data_file', type=str, default=os.path.join(params_path,'args.npz'),
    help='path to npz file arguments data file ')


args = parser.parse_args()
fpga_driver = PESDriver(args.arg_data_file)
print("udp socket create")
udp_socket = UDPSendReceiveSocket(
    remote_addr=(args.host_ip, args.udp_port),
    listen_addr=(args.remote_ip, args.udp_port),
    recv_timeout=None, **eval(args.socket_args))

tcp_socket = TCPcommandSocket(args.remote_ip,args.host_ip,args.tcp_port)
tcp_socket.connect_host()


socket_step = udp_socket.make_step(
    fpga_driver.output_dimensions,
    fpga_driver.input_dimensions + fpga_driver.output_dimensions,
    fpga_driver.dt)

print("output input dimen"+str(fpga_driver.output_dimensions)+" "+str(fpga_driver.input_dimensions)+" " +" "+str(fpga_driver.dt))



print("NAAL_FPGA board socket ");
# Cleanup function



# Register the cleanup function with atexit
atexit.register(cleanup, fpga_driver, socket_step)

# Variables to keep track of current simulation time
curr_t = 0
dt = fpga_driver.dt


print("dt value = "+str(dt))
print("dt value = "+str(dt))

while not fpga_driver.stopped:
    if tcp_socket.sim_status is "pause":
        print("curr "+curr_t+"pause");
        while True:
            if  tcp_socket.sim_status is "restart":
                print("sim restart")
                break

    elif tcp_socket.sim_status is "stop":
        print(tcp_socket.sim_status)
        break; 
    
    start_time = time.time();
    socket_recv_value = socket_step(curr_t, fpga_driver.output)
    fpga_driver.update_input_error_values(socket_recv_value)
    output_value = fpga_driver.step()

    step_time = start_time - output_value
    print("dt : %s, step_time : %s\n", % str(dt), str(step_time))
    
    # Update the current timestamp
    curr_t += dt
print("step end")

# send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# send_sock.connect((args.host_ip,args.tcp_port))
# send_sock.sendall(fpga_driver.id_bytes)
# send_sock.close()
#while True:

# If we are local, then print and save ID here
#if args.host_ip == parser.get_default('host_ip'):
#    id_str = "Found board ID: %#0.16X" % fpga_driver.id_int
#    print(id_str)
#    with open("id_pynq.txt", 'w') as file:
#        file.write(id_str + '\n')

# If we havea host connection send the ID back
#else:
    # Using vanilla socket since we are only sending one val+-+--ue
 #   tcp_send = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  #  tcp_send.connect((args.host_ip, args.tcp_port))
   # tcp_send.sendall(fpga_driver.id_bytes)

    # Close socket
    #tcp_send.close()
