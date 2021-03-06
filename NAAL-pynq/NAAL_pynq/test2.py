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
#parser.add_argument(
#    '--arg_data_file', type=str, default=os.path.join(params_path, 'args.npz'),
#    help='Path to parameter arguments (for ensemble, output connection) data' +
#    'file.')



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

initarr=[]

initarr.append(0.001)
for i in range(0,206):
    initarr.append(0.0)
print(initarr)

socket_recv_value = socket_step(curr_t, fpga_driver.output)

fpga_driver.update_input_error_values(initarr)
output_value = fpga_driver.step()

print("output value = ["+str(output_value)+"]")



print("step end")

