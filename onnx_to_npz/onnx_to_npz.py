import sys
import numpy as np
import tensorflow as tf
from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Conv2D, Flatten
import keras2onnx
import onnx
from onnx import numpy_helper

class ConvFileFormat:
	def __init__(self, npzPath, onnxPath):
		self.npzPath = npzPath
		self.onnxPath = onnxPath

	def npz_to_onnx(self):
		# load npz file
		arg_data = np.load(self.npzPath, encoding='latin1', allow_pickle=True)

		# load paramerers 
		sim_args = arg_data['sim_args'].item()
		ens_args = arg_data['ens_args'].item()
		conn_args = arg_data['conn_args'].item()

		dt = sim_args['dt']

		n_neurons = ens_args['n_neurons']
		input_dimensions = ens_args['input_dimensions']
		output_dimensions = ens_args['output_dimensions']
		neuron_type = ens_args['neuron_type']
		bias = ens_args['bias']
		scaled_encoders = ens_args['scaled_encoders']
		
		learning_rate = conn_args['learning_rate']
		weights = conn_args['weights'] # (10 ,81)

		# make other parameter array (dt, learning_rate, n_neurons ...)
		other_parameters = np.array([dt, learning_rate, n_neurons, input_dimensions, output_dimensions, 0 if neuron_type == 'RectifiedLinear' else 1,0,0,0,0]).reshape(10,)

		# Create Model
		model = Sequential()
		input_layer = tf.keras.Input(shape=(196,))
		layer_1 = tf.keras.layers.Dense(81, input_shape=(196,))
		layer_2 = tf.keras.layers.Dense(10, input_shape=(81,))

		model.add(input_layer)
		model.add(layer_1)
		model.add(layer_2)

		# setting parameters to layer	
		layer_1.set_weights([scaled_encoders.T, bias])
		layer_2.set_weights([weights.T, other_parameters])

		# Display Contents
		model.summary() 

		onnx_model = keras2onnx.convert_keras(model, self.onnxPath)
		onnx_file = open(self.onnxPath, 'wb')
		onnx_file.write(onnx_model.SerializeToString())
		onnx_file.close()

		# Check onnx model shape
		onnx_model = onnx.load_model(self.onnxPath)

		onnx_weights = onnx_model.graph.initializer

		print('** Checking ONNX weights dims... **')
		for i in onnx_weights:
			print(i.dims)
		print('** Done.... **')

	def onnx_to_npz(self):
		# load onnx model
		onnx_model = onnx.load(self.onnxPath)
		onnx_weights = onnx_model.graph.initializer

		# make dictionary
		sim_args = dict()
		ens_args = dict()
		conn_args = dict()

		# load weights
		conn_args['weights'] = numpy_helper.to_array(onnx_weights[0]).T
		other_parameters = numpy_helper.to_array(onnx_weights[1])

		# load dt, learning_rate, n_neurons ...
		sim_args['dt'] = int(other_parameters[0])
		conn_args['learning_rate'] = other_parameters[1]
		ens_args['n_neurons'] = int(other_parameters[2])
		ens_args['input_dimensions'] = int(other_parameters[3])
		ens_args['output_dimensions'] = int(other_parameters[4])
		ens_args['neuron_type'] = 'RectifiedLinear' if int(other_parameters[5]) == 0 else 'SpikingRectifiedLinear'

		# load scaled_encoders
		ens_args['scaled_encoders'] = numpy_helper.to_array(onnx_weights[2]).T

		# load bias
             ens_args['bias'] = numpy_helper.to_array(onnx_weights[3])

		# save npz file
		np.savez_compressed(self.npzPath, sim_args=sim_args, ens_args=ens_args, conn_args=conn_args)

# Usage : python3 convNpzandOnnx.py npzPath onnxPath
# True : npz -> onnx, False : onnx -> npz
npz2keras = False
if npz2keras == True:
	obj = ConvFileFormat(sys.argv[1], sys.argv[2])
	obj.npz_to_onnx()
else:
	obj = ConvFileFormat(sys.argv[1], sys.argv[2])
	obj.onnx_to_npz()
