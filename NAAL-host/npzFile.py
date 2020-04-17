import os
import numpy as np
import datetime
from utils.paths import lib_path

class npzFile(object):
	def __init__(self, filepath='', ens_args={}, conn_args={}):
		now = datetime.datetime.now()
		self.filepath = filepath
		self.ens_args = ens_args
		self.conn_args = conn_args
	def filepath(self):
		return self.filepath

	def compressed(self):
		np.savez_compressed(self.filepath, ens_args=ens_args, conn_args=conn_args)

	def load(self, filepath):
		self.filepath = filepath

		arg_data = np.load(self.filepath, encoding='latin1', allow_pickle=True)
		ens_args = arg_data['ens_args'].item()
		conn_args = arg_data['conn_args'].item()

		n_neurons = ens_args['n_neurons']
		self.in_dimensions = ens_args['in_dimensions']
		self.output_dimensions = ens_args['output_dimensions']
		neuron_type = ens_args['neuron_type']
		bias = ens_args['bias']

		learning_rate = conn_args['learning_rate']
		weights = conn_args['weights']

		if (n_neurons * max(self.in_dimensions, self.output_dimensions) > 32768):
			raise AttributeError('Maximum supported N * D is 32,768.')

		if(n_neurons > 16384):
			raise AttributeError('Maximum supported N is 16,384.')
		
		if(max(self.in_dimensions, self.output_dimensions) > 1024):
			raise AttributeError('Maximum supported D is 1024.')

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

	def printAll(self):
		print(ens_args)
		print(conn_args)
