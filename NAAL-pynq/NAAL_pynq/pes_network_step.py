from __future__ import print_function
import os
import argparse

import os
import argparse
import socket
from pes_driver import PESDriver
from utils.paths import params_path
from NAAL_step import naal_socket
from NAAL_step import NAAL_UDPnetwork

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
    help='IP Address of host PC. .')
parser.add_argument(
    '--remote_ip', type=str, default='127.0.0.1',
    help='IP Address of FPGA board. Used for socket communication')
parser.add_argument(
    '--udp_port', type=int, default=500000,
    help='Port number to use for the socket communication.')
parser.add_argument(
    '--in_dimensions', type=int, default=0,
    help='.')
parser.add_argument(
    '--out_dimensions', type=int, default=0,
    help='.')    
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
print("remote_addr = "+args.host_ip)
print("listen_addr = "+args.remote_ip)
remote_addr=(args.host_ip, args.udp_port)
listen_addr=(args.remote_ip, args.udp_port)
#a=NAAL_UDPnetwork(remote_addr,listen_addr,196,10)
curr_t = 0
dt = fpga_driver.dt
print("dt value = "+str(dt))
a=NAAL_UDPnetwork(remote_addr,listen_addr,args.in_dimensions,args.out_dimensions)
while not fpga_driver.stopped:
    recv_data=a.step_call_recv(curr_t)
    print("recv_Data ==")
    print(recv_data)
    if recv_data[0] == 3:
        continue
    elif recv_data[0] == 4 :
        fpga_driver.stopped= True

    print("recv_data[1:] =")
    print(recv_data[2:])
    fpga_driver.update_input_error_values(recv_data[2:])
    output_value=fpga_driver.step()
    print("output_value")
    print(output_value)
    a.step_call_send(curr_t,output_value)

    curr_t += dt

    


# while not fpga_driver.stopped:
#     socket_recv_value = socket_step(curr_t, fpga_driver.output)
#     fpga_driver.update_input_error_values(socket_recv_value)
#     output_value = fpga_driver.step()
#     # Update the current timestamp
#     curr_t += dt
