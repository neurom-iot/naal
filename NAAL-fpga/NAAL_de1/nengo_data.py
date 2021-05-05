import os
import numpy as np


class NengoData(object):
    def __init__(self, arg_data_filepath):
        # Load information from npz argument data file
        self.arg_data_filepath = arg_data_filepath
        arg_data = np.load(self.arg_data_filepath, encoding='latin1')

        self.sim = arg_data['sim_args'].item()
        self.ens = arg_data['ens_args'].item()
        self.conn = arg_data['conn_args'].item()
        self.recur = arg_data['recur_args'].item()

        # Close and remove the argument data file. It will be regenerated
        # when the superhost runs a new simulator.
        arg_data.close()
      # kicheol modify
      # if os.path.exists(self.arg_data_filepath):
       #     os.remove(self.arg_data_filepath)

    @property
    def input_dimensions(self):
        return self.ens['input_dimensions']

    @property
    def output_dimensions(self):
        return self.ens['output_dimensions']

    @property
    def dt(self):
        return self.sim['dt']

    def cleanup(self):
        print ("modify kicheol")
        # Remove argument data file
      
      # if os.path.isfile(self.arg_data_filepath):
       #     os.remove(self.arg_data_filepath)
