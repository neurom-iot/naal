from __future__ import print_function
import os
import argparse
import atexit
import os
import argparse
import socket
from pes_driver import PESDriver
from utils.paths import params_path
from NAAL_step import naal_socket
from NAAL_step import NAAL_UDPnetwork
from NAAL_step import TCPcommandSocket
import time



from functools import wraps
import errno
import signal
# calculate time of step


class TimeoutError(Exception):
    pass

def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.setitimer(signal.ITIMER_REAL,seconds) 
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result
        return wraps(func)(wrapper)
    return decorator



def cleanup(fpga_driver):
    # Terminate the fpga driver
    fpga_driver.terminate()
print("NAAL_FPGA board start")

#time out 예제
# @timeout(1)
# def asd():
#     while True :
        
#         try :
#             time.sleep(1)
#         except Exception as e:
#             print ("time out ")

# try :
#     asd()
# except Exception as e:
#     print ("time out");




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


args = parser.parse_args()
fpga_driver = PESDriver(args.arg_data_file)
remote_addr=(args.host_ip, args.udp_port)
listen_addr=(args.remote_ip, args.udp_port)
atexit.register(cleanup, fpga_driver)
curr_t = 0
dt = fpga_driver.dt

# command socket == modifiying 
tcp_socket = TCPcommandSocket(args.remote_ip,args.host_ip,args.tcp_port)
tcp_socket.connect_host()

print("dt value = "+str(dt))
a=NAAL_UDPnetwork(remote_addr,listen_addr,args.in_dimensions,args.out_dimensions)
start_time =time.time()
fpga_driver.update_input_error_values(a.recv.vector)
output_value=fpga_driver.step()

first_time=time.time()-start_time
#output_value[1]=first_time
a.step_call_send(first_time,output_value)
while not fpga_driver.stopped:
    if tcp_socket.sim_status is 2 or tcp_socket.sim_status is 4 :
        print("curr "+curr_t+"pause");
        while True:
            if  tcp_socket.sim_status is 1:
                print("sim restart")
                break
    elif tcp_socket.sim_status is 3:
        print(tcp_socket.sim_status)
        break; 
    recv_data=a.step_call_recv(curr_t)
    if recv_data[0] == 3:
        continue
    elif recv_data[0] == 4 :
        fpga_driver.stopped= True


    start_time =time.time()
    fpga_driver.update_input_error_values(recv_data[2:])
    output_value=fpga_driver.step()
    first_time=time.time()-start_time
    curr_t += dt

    print("dt : {} step time : {}\n".format(curr_t, first_time))
    a.step_call_send(curr_t,output_value)


# while not fpga_driver.stopped:
#     socket_recv_value = socket_step(curr_t, fpga_driver.output)
#     fpga_driver.update_input_error_values(socket_recv_value)
#     output_value = fpga_driver.step()
#     # Update the current timestamp
#     curr_t += dt
