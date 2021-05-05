import os
import signal
import ctypes as ct
import numpy as np

from utils.paths import lib_path


class PESDriver(object):
    def __init__(self, nengo_data, lockstep=1):
        # Note: See nengo-de1-hw/source/host/python_dll.cpp for
        # the source of the DLL, containing documentation for the fpga
        # functions

        # Load dll
        self.fpga = ct.cdll.LoadLibrary(
            os.path.join(lib_path, "pyhost_pes.so"))

        # Set argtypes (for safety mostly, but this can actually typecast too)
        self.fpga.setup.argtypes = [
            ct.c_uint, ct.c_uint, ct.c_uint, ct.POINTER(ct.c_float),
            ct.POINTER(ct.c_float), ct.c_char_p, ct.POINTER(ct.c_float),
            ct.POINTER(ct.c_float), ct.POINTER(ct.c_float), ct.c_uint,
            ct.POINTER(ct.c_float)]
        self.fpga.step.argtypes = [
            ct.POINTER(ct.c_float), ct.POINTER(ct.c_float),
            ct.POINTER(ct.c_float), ct.POINTER(ct.c_uint)]

        self.fpga.cleanup()  # Clean up any previous data (just in case)
        self.stopped = False
        self.hw_counter = ct.c_uint32(0)
        self.lockstep = lockstep

        # Various model parameters
        dt = nengo_data.sim['dt']

        n_neurons = nengo_data.ens['n_neurons']
        input_dimensions = nengo_data.ens['input_dimensions']
        self.input_dimensions = input_dimensions

        output_dimensions = nengo_data.ens['output_dimensions']

        neuron_type = nengo_data.ens['neuron_type']
        bias = nengo_data.ens['bias']
        scaled_encoders = nengo_data.ens['scaled_encoders']

        learning_rate = nengo_data.conn['learning_rate']
        weights = nengo_data.conn['weights']

        # Stack recurrent weights if applicable
        tau = -1
        recur_dimensions = 0
        if np.any(nengo_data.recur['weights']):
            recur_dimensions = input_dimensions
            weights = np.concatenate((weights, nengo_data.recur['weights']))
            tau = nengo_data.recur['tau']

        # Check that the ensemble will fit on the fpga
        if (n_neurons > 16384):  # Not strictly necessary, for completeness
            raise AttributeError('Maximum supported N is 16,384.')

        if recur_dimensions > 0:
            if (n_neurons * max(input_dimensions,
                                output_dimensions + recur_dimensions) > 16384):
                raise AttributeError('Maximum supported N * D is 16,384.'
                                     'Where D = max(input_dimensions, '
                                     'output_dimensions + '
                                     'feedback_dimensions)')
            if (max(input_dimensions,
                    output_dimensions + recur_dimensions) > 1024):
                raise AttributeError('Maximum supported D is 1024.'
                                     'Where D = max(input_dimensions, '
                                     'output_dimensions + '
                                     'feedback_dimensions)')
        else:
            if (n_neurons * max(input_dimensions, output_dimensions) > 16384):
                raise AttributeError('Maximum supported N * D is 16,384.'
                                     'Where D = max(input_dimensions, '
                                     'output_dimensions')
            if (max(input_dimensions, output_dimensions) > 1024):
                raise AttributeError('Maximum supported D is 1024.'
                                     'Where D = max(input_dimensions, '
                                     'output_dimensions)')

        # Process AOCX filenames based on the given neuron type
        if neuron_type == "RectifiedLinear":
            aocx = os.path.join(lib_path, "pes_relu_rate")
        elif neuron_type == "SpikingRectifiedLinear":
            aocx = os.path.join(lib_path, "pes_relu_spiking")
            # Scale value for spiking (maybe make a flag for this?)
            scaled_encoders *= dt
            bias *= dt
        else:
            raise NotImplementedError(
                'Neuron type "%s" is not supported.' % neuron_type)
        
        # Must use float32, flatten array
        scaled_encoders = scaled_encoders.astype(np.float32).flatten()
        bias = bias.astype(np.float32)
        weights = weights.transpose().astype(np.float32).flatten()

        # Create c pointers
        c_scaled_encoders = scaled_encoders.ctypes.data_as(
            ct.POINTER(ct.c_float))
        c_bias = bias.ctypes.data_as(ct.POINTER(ct.c_float))
        c_weights = weights.ctypes.data_as(ct.POINTER(ct.c_float))
        # Send everything to the fpga
        self.fpga.setup(
            input_dimensions, output_dimensions, n_neurons,
            ct.byref(ct.c_float(learning_rate)),
            ct.byref(ct.c_float(dt)), ct.c_char_p(aocx.encode("ascii")),
            c_bias, c_scaled_encoders, c_weights, self.lockstep,
            ct.byref(ct.c_float(tau)))

        # Check for valid Device ID
        self.valid_id = self.fpga.check_id()

        try:
            assert self.valid_id
        except AssertionError as e:
            e.args += ('ERROR: Device and bitstream mismatched!'
                       ' Ensure you are using the correct device'
                       ' and *.aocx file pair.',)
            raise

        # C mapped input, error, output values.
        # Must be contiguous arrays for proper C memory mapping
        self.input = np.ascontiguousarray(np.zeros(input_dimensions),
                                          dtype=np.float32)
        self.error = np.ascontiguousarray(np.zeros(output_dimensions),
                                          dtype=np.float32)
        self.output = np.ascontiguousarray(np.zeros(output_dimensions),
                                           dtype=np.float32)

        # Register OS signal handler to handle SSH termination, or
        # ctrl+C termination
        signal.signal(signal.SIGINT, self.terminate)
        signal.signal(signal.SIGTERM, self.terminate)
        signal.signal(signal.SIGHUP, self.terminate)

    def step(self):
        # Do one step on the FPGA
        if not self.stopped:
            self.fpga.step(self.input.ctypes.data_as(ct.POINTER(ct.c_float)),
                           self.error.ctypes.data_as(ct.POINTER(ct.c_float)),
                           self.output.ctypes.data_as(ct.POINTER(ct.c_float)),
                           ct.byref(self.hw_counter))
        return self.output

    def stop(self):
        # Send the stop command to the FPGA (only if not already stopped)
        if not self.stopped:
            self.fpga.stop()
            self.stopped = True
        self.fpga.cleanup()

    def terminate(self):
        # Stop FPGA and cleanup
        self.stop()

    def __del__(self):
        self.terminate()

    def update_input_error_values(self, input_array):
        self.input[...] = input_array[:self.input_dimensions]
        self.error[...] = input_array[self.input_dimensions:]
