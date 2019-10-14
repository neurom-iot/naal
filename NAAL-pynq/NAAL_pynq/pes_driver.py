import os
import numpy as np
import datetime

from utils.paths import lib_path

class PESDriver(object):
	def __init__(self, filepath='', ens_args={}, conn_args={}):
		now = datetime.datetime.now()
		self.filepath = filepath
		self.ens_args = ens_args
		self.conn_args = conn_args

	def compressed(self):
		np.savez_compressed(self.filepath, ens_args=ens_args, conn_args=conn_args)

	def load(self, filepath):
		self.filepath = filepath
		
		# Load information from npz argument data file
		# can use npzFile.arg_data, npzFile.ens_args in other file
		arg_data = np.load(self.filepath, encoding='latin1', allow_pickle=True)
		ens_args = arg_data['ens_args'].item()
		conn_args = arg_data['conn_args'].item()

		# Various model parameters
		n_neurons = ens_args['n_neurons']
		self.input_dimensions = ens_args['input_dimensions']
		self.output_dimensions = ens_args['output_dimensions']
		neuron_type = ens_args['neuron_type']
		bias = ens_args['bias']

		learning_rate = conn_args['learning_rate']
		weights = conn_args['weights']

		# Check that the ensemble will fit on the fpga
		if (n_neurons * max(self.input_dimensions, self.output_dimensions) > 32768):
			raise AttributeError('Maximum supported N * D is 32,768.')

		if(n_neurons > 16384):
			raise AttributeError('Maximum supported N is 16,384.')
		
		if(max(self.input_dimensions, self.output_dimensions) > 1024):
			raise AttributeError('Maximum supported D is 1024.')

		# Process bistream filename based on the given neuron type
		if neuron_type == 'RectifiedLinear':
			bistream = os.path.join(lib_path, 'pes_relu_rate.bit')
			spiking = False
		elif neuron_type == 'SpikingRectifiedLinear':
			bitstream = os.path.join(lib_path, 'pes_relu_spiking.bit')
			spiking = True
		else:
			print("WARNING: Unsupported neuron type: " + neuron_type +
					". Defaulting to RectifiedLinear.")
			bitstream = os.path.join(lib_path, 'pes_relu_rate.bit')
			spiking = False

	# TEST
	def printAll(self):
		print(ens_args)
		print(conn_args)

# TEST
ens_args = {}
ens_args['n_neurons'] = 81
ens_args['input_dimensions'] = 196
ens_args['output_dimensions'] = 10
ens_args['neuron_type'] = 'SpikingRectifiedLinear'
ens_args['bias'] = [33.33333333] * ens_args['n_neurons']

conn_args = {}
conn_args['learning_rate'] = 0
conn_args['weights'] = np.random.randn(10, 81)

filepath = 'fpen_args_123456.npz'
nfile = npzFile(filepath, ens_args, conn_args)
nfile.compressed()

nfile.load(filepath)
#nfile.printAll()
