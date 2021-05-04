"""Top level script run on FPGA device to read device ID"""

import argparse
import socket

from nengo_pynq.id_driver import IDDriver
from nengo_pynq.utils.paths import lockfile
from nengo_pynq.utils.resource_lock import ResourceLock

# This script loads the dna_extractor bitstream, reads the Device ID, and
# sends the ID back to the host via TCP socket.

# Setup default args that match between arparse and function args
defaults = { 
    "host_ip": "local",
    "tcp_port": 50000,
}

# Driver for ID_extractor bitstream
fpga_driver = IDDriver()

id_str = "Found board ID: %#0.16X" % fpga_driver.id_int
print(id_str)


