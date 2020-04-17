import os

# nengo_de1 installation path
install_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

# Path to FPGA bitstream file
lib_path = os.path.join(install_dir, 'lib')

# Path to model-specific parameter files (these are generated on the
# "superhost" machine and sftp'd over to the FGPA board)
params_path = os.path.join(install_dir, 'params')
