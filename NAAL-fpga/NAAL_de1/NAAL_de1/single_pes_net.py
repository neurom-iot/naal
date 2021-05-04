from __future__ import print_function
import os
import argparse
import atexit
import numpy as np

from utils.paths import params_path
from nengo_data import NengoData
from pes_driver import PESDriver
from NAAL_step import naal_socket
from NAAL_step import NAAL_UDPnetwork
from NAAL_step import TCPcommandSocket
import time


parser = argparse.ArgumentParser(
    description='Generic for running the pes network on the fpga board.')

# Socket communication arguments
parser.add_argument(
    '--host_ip', type=str, default='127.0.0.1',
    help='IP Address of host PC. .')
parser.add_argument(
    '--remote_ip', type=str, default='127.0.0.1',
    help='IP Address of FPGA board.')
parser.add_argument(
    '--udp_port', type=int, default=500000,
    help='UDP Port number to use.')
parser.add_argument(
    '--in_dimensions', type=int, default=0,
    help='.')
parser.add_argument(
    '--out_dimensions', type=int, default=0,
    help='.')    
parser.add_argument(
    '--tcp_port', type=int, default=50000,
    help='TCP Port number to use.')
parser.add_argument(
    '--board_connect_timeout', type=int, default=5,
    help='Port number to use for the socket communication.')    

parser.add_argument(
    '--arg_data_file', type=str, default=os.path.join(params_path,'args.npz'),
    help='path to npz file arguments data file ')




# Parse the arguments
args = parser.parse_args()
remote_addr=(args.host_ip, args.udp_port)
listen_addr=(args.remote_ip, args.udp_port)

# ----- Create socket for UPD socket communication -----
# Use the host, client, and port information from the command line arguments
# N.B. Make the socket blocking so that if no information is obtained from the
#      host (e.g., when the model is paused in the GUI), the nengo model
#      waits indefinitely.
# N.B. The UDP socket gets information as an array, where the first input_dim
#      dimensions is the input signal to the PESEnsembleNetwork, and the
#      remaining output_dim dimensions is the error signal to the
#      PESEnsembleNetwork.

# Load Nengo Data from file
nengo_data = NengoData(args.arg_data_file)

curr_t = 0
dt = nengo_data.dt


try:
    fpga_driver = PESDriver(nengo_data)
except:
    print ("PESDriver error")
    #socket_step.send(-1, np.zeros((nengo_data.output_dimensions)))
    raise


# Cleanup function
def cleanup(nengo_data, fpga_driver):
    # Cleanup data files
    nengo_data.cleanup()

    # Terminate the fpga driver
    fpga_driver.terminate()

# Register the cleanup function with atexit
atexit.register(cleanup, nengo_data, fpga_driver)

tcp_socket =TCPcommandSocket(args.remote_ip,args.host_ip,args.tcp_port)
tcp_socket.connect_host()

a=NAAL_UDPnetwork(remote_addr,listen_addr,args.in_dimensions,args.out_dimensions)
fpga_driver.update_input_error_values(a.recv.vector)
output_value=fpga_driver.step()
print(output_value)
a.step_call_send(curr_t,output_value)

# Variables to keep track of current simulation time

while not fpga_driver.stopped:
    # Receive values from the socket, and send over any values produced in the
    # previous "timestep"
#    socket_recv_value = socket_step(curr_t, fpga_driver.output)
    if tcp_socket.sim_status is 2 or tcp_socket.sim_status is 4 :
        while True:
            if  tcp_socket.sim_status is 1:
                print("sim restart")
                break
    elif tcp_socket.sim_status is 3:
        print(tcp_socket.sim_status)
        break; 

    start =time.time()
    recv_data=a.step_call_recv(curr_t)

    
    if recv_data[0] == 3:
        continue
    elif recv_data[0] == 4 :
        fpga_driver.stopped= True
    try:
        # Update the FPGA driver with the received input values.
        # Note: update_input_error_values function handles splitting up the
        #       single array into the respective "input" and "error" arrays
        fpga_driver.update_input_error_values(recv_data[2:])
        # Send the step command to the FPGA
        output_value = fpga_driver.step()
    except:
        # Send a UDP termination packet if an error is encountered
 #       socket_step.send(-1, np.zeros((nengo_data.output_dimensions)))
        print("exception pes learning rules")
        raise

    # Update the current timestamp
    curr_t += dt
    a.step_call_send(curr_t,output_value)
    print("time of step[{}={}]".format(curr_t,time.time()-start))

