import os
import signal
import numpy as np

from pynq import Xlnk, Overlay, DefaultIP, DefaultHierarchy

from utils.paths import lib_path
from utils.functions import float2reg

import logging

class PESMemoryMap(DefaultIP):
    def __init__(self, description):
        super().__init__(description)

    bindto = ['xilinx.com:hls:pynq_pes:1.0']
    # found in ip_dict above as 'type'

    # Creating 'getter' and 'setter' for mmio signal
    # Address from Vivado axi src file
    @property
    def START(self):
        return self.read(0x00)

    @START.setter
    def START(self, value):
        self.write(0x00, value)

    @property
    def D_in(self):
        return self.read(0x10)

    @D_in.setter
    def D_in(self, value):
        self.write(0x10, value)

    @property
    def D_out(self):
        return self.read(0x18)

    @D_out.setter
    def D_out(self, value):
        self.write(0x18, value)

    @property
    def N(self):
        return self.read(0x20)

    @N.setter
    def N(self, value):
        self.write(0x20, value)

    @property
    def K(self):
        return self.read(0x28)

    @K.setter
    def K(self, value):
        self.write(0x28, value)

    @property
    def LOAD(self):
        return self.read(0x30)

    @LOAD.setter
    def LOAD(self, value):
        self.write(0x30, value)

    @property
    def ID_valid(self):
        return self.read(0x38)  # only supports 4byte reads...

    @ID_valid.setter
    def ID_valid(self, value):
        self.write(0x38, value)

    @property
    def DT(self):
        return self.read(0x40)

    @DT.setter
    def DT(self, value):
        self.write(0x40, value)

# Pes driver parameters
xlnk = Xlnk()
DTYPE = np.float32  # datatype


class PESHierarchy(DefaultHierarchy):
    def __init__(self, description):
        super().__init__(description)

    def step_pes(self, D_in, D_out, IN=None, ERR=None, N=None, K=1e-4,
                 scaled_encoders=None, bias=None, decoders=None, LOAD=0,
                 dt=1e-3, IN_buf=None, OUT_buf=None, spiking=False):
        """ Even if we don't write `N`, `D_in`, and `D_out` to hardware,
            we need them in the function here """
        # Set parameters (these should only have to be once)
        if(LOAD):
            assert N is not None

            # Get the bias information
            assert bias.shape == (N,)
            bias = np.array(bias, dtype=DTYPE)

            # Get the scaled encoder information
            assert scaled_encoders.shape == (N, D_in)
            scaled_encoders = np.array(scaled_encoders, dtype=DTYPE)

            # Get the decoder information
            if decoders is not None:
                decoders = np.array(decoders, dtype=DTYPE)
                assert decoders.shape == (D_out, N)
            else:
                decoders = np.zeros((D_out, N), dtype=DTYPE)

            # Set params
            self.relu_pes.LOAD = int(1)  # set to 1 for parameter loading
            self.relu_pes.N = int(N)
            self.relu_pes.D_in = int(D_in)
            self.relu_pes.D_out = int(D_out)
            K_scaled = K * dt / DTYPE(N)  # scale learning rate
            # Pack as integer for MMIO
            self.relu_pes.K = float2reg(DTYPE(K_scaled))

            if spiking:
                self.relu_pes.DT = float2reg(DTYPE(dt))

            # Create contiguous buffers
            with xlnk.cma_array(shape=(N,), dtype=DTYPE) as BIAS_buf,\
                    xlnk.cma_array(shape=(N, D_in), dtype=DTYPE) as ENC_buf,\
                    xlnk.cma_array(shape=(D_out, N), dtype=DTYPE) as DEC_buf:
                # Copy values to buffers
                for i in range(N):
                    BIAS_buf[i] = bias[i]
                    for j in range(D_in):
                        ENC_buf[i][j] = scaled_encoders[i][j]
                    for k in range(D_out):
                        DEC_buf[k][i] = decoders[k][i]

                # Transfer to hardware
                self.IN_dma.sendchannel.transfer(BIAS_buf)
                self.relu_pes.START = 1  # start bit to begin hardware exec

                self.IN_dma.sendchannel.wait()
                self.IN_dma.sendchannel.transfer(ENC_buf)
                self.IN_dma.sendchannel.wait()
                self.IN_dma.sendchannel.transfer(DEC_buf)
                self.IN_dma.sendchannel.wait()

            self.relu_pes.LOAD = int(0)  # Set back to 0 for normal operation

            try:
                assert self.relu_pes.ID_valid
            except AssertionError as e:
                e.args += ('ERROR: Device and bitstream mismatched!'
                           ' Ensure you are using the correct device'
                           ' and *.bit file pair.',)
                raise

            return 0

        else:  # Compute step

            # Copy inputs to buffers... there must be a better way to do this
            for i in range(D_in):
                IN_buf[i] = IN[i]
            for i in range(D_out):
                IN_buf[i + D_in] = ERR[i]

            # Begin the AXI streams to transfer data to the hardware
            self.IN_dma.sendchannel.transfer(IN_buf)
            self.OUT_dma.recvchannel.transfer(OUT_buf)  # prepare to read out
            self.relu_pes.START = 1  # start bit to begin hardware execution

            # Wait for all AXI transfers to finish
            self.IN_dma.sendchannel.wait()  # IN + ERR
            self.OUT_dma.recvchannel.wait()  # OUT

            # copy result out of buffer
            return OUT_buf.copy()

    @staticmethod
    def checkhierarchy(description):
        # check the two expected blocks exist in the hierarchy
        if 'IN_dma' in description['ip'] and \
           'OUT_dma' in description['ip'] and \
           'relu_pes' in description['ip']:
            return True

        raise RuntimeError('PESDriver checkhierarchy failed... ' +
                           'Bitstream mismatch.')


class PESDriver(object):
    def __init__(self, arg_data_filepath):
        # Simulator flags
        self.stopped = False

        # Load information from npz argument data file
        self.arg_data_filepath = arg_data_filepath
        arg_data = np.load(self.arg_data_filepath, encoding='latin1')
        sim_args = arg_data['sim_args'].item()
        ens_args = arg_data['ens_args'].item()
        conn_args = arg_data['conn_args'].item()


        # Various model parameters
        self.dt = sim_args['dt']

        n_neurons = ens_args['n_neurons']
        self.input_dimensions = ens_args['input_dimensions']
        self.output_dimensions = ens_args['output_dimensions']
        neuron_type = ens_args['neuron_type']
        bias = ens_args['bias']
        scaled_encoders = ens_args['scaled_encoders']

        learning_rate = conn_args['learning_rate']
        weights = conn_args['weights']

        # Check that the ensemble will fit on the fpga
        if (n_neurons * max(self.input_dimensions,
                            self.output_dimensions) > 32768):
            raise AttributeError('Maximum supported N * D is 32,768.')
        if (n_neurons > 16384):
            raise AttributeError('Maximum supported N is 16,384.')
        if (max(self.input_dimensions, self.output_dimensions) > 1024):
            raise AttributeError('Maximum supported D is 1024.')

        # Process bitstream filenames based on the given neuron type
        if neuron_type == "RectifiedLinear":
            bitstream = os.path.join(lib_path, 'pes_relu_rate.bit')
            spiking = False
        elif neuron_type == "SpikingRectifiedLinear":
            bitstream = os.path.join(lib_path, 'pes_relu_spiking.bit')
            spiking = True

            # Scale value for spiking (maybe make a flag for this?)
            scaled_encoders *= self.dt
            bias *= self.dt
        else:
            print("WARNING: Unsupported neuron type: " + neuron_type +
                  ". Defaulting to RectifiedLinear.")
            bitstream = os.path.join(lib_path, 'pes_relu_rate.bit')
            spiking = False

        # Load bitstream
        ol = Overlay(os.path.join(bitstream))
        ol.download()
        self.pes_heir_func = ol.pynq_pes.step_pes

        # Send everything to the fpga
        self.pes_heir_func(self.input_dimensions, self.output_dimensions,
                           dt=self.dt, N=n_neurons, K=learning_rate,
                           scaled_encoders=scaled_encoders, bias=bias,
                           decoders=weights, LOAD=1, spiking=spiking)

        # Input / output buffers and arrays
        self.input = np.ascontiguousarray(np.zeros(self.input_dimensions),
                                          dtype=np.float32)
        self.error = np.ascontiguousarray(np.zeros(self.output_dimensions),
                                          dtype=np.float32)
        self.output = np.ascontiguousarray(np.zeros(self.output_dimensions),
                                           dtype=np.float32)

        self.IN_buf = xlnk.cma_array(shape=(self.input_dimensions +
                                            self.output_dimensions,),
                                     dtype=DTYPE)
        self.OUT_buf = xlnk.cma_array(shape=(self.output_dimensions,),
                                      dtype=DTYPE)

        # Register OS signal handler to handle SSH termination, or
        # ctrl+C termination
        signal.signal(signal.SIGINT, self.terminate)
        signal.signal(signal.SIGTERM, self.terminate)
        signal.signal(signal.SIGHUP, self.terminate)

        # Close and remove the argument data file. It will be regenerated
        # when the superhost runs a new simulator.
        arg_data.close()
        # if os.path.exists(self.arg_data_filepath):
        #     os.remove(self.arg_data_filepath)

    def step(self):
        # Do one step on the FPGA
        if not self.stopped:
            self.output[...] = self.pes_heir_func(
                self.input_dimensions, self.output_dimensions,
                IN=self.input, ERR=self.error,
                IN_buf=self.IN_buf, OUT_buf=self.OUT_buf)
        return self.output

    def stop(self):
        # Set stop flag
        if not self.stopped:
            self.stopped = True

    def terminate(self):
        # Stop the simulation steppage
        self.stop()

        # Free CMA buffers
        self.IN_buf.freebuffer()
        self.OUT_buf.freebuffer()

        # Remove argument data file
        # if os.path.exists(self.arg_data_filepath):
        #     os.remove(self.arg_data_filepath)

    def __del__(self):
        self.terminate()
        # Free allocated contiguous memory

    def update_input_error_values(self, input_array):
        self.input[...] = input_array[:self.input_dimensions]
        self.error[...] = input_array[self.input_dimensions:]
