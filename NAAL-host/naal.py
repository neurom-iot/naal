import logging
import sys
import time
import numpy as np
import os # js add
import copy # js add
from datetime import datetime
import json # js add

from Naal.naal_fpga.naal_fpga_interface import NaalFpga
from Naal.naal_loihi.naal_loihi_interface import NaalLoihi
from Naal.digital_snn.digital_snn_interface import NaalDigital
from Naal.naal_status import board_command

NAAL_logger= logging.getLogger("NAAL_log")
NAAL_logger.setLevel(logging.INFO)
NAAL_logger.info("["+str(datetime.today())+"] NAAL START")

# FOR DEBUG
json_path = './debug.json'

class Naal():
    def __init__(self, hardware=None, dt = 0.001, input_size=None, output_size=1, npz_path = None, debug_mode = False):
        self.hardware = hardware
        self.dt = dt
        self.input_size = input_size
        self.output_size = output_size
        self.npz_path = npz_path

        # FOR DEBUG
        self.step = 0 
        self.debug_mode = debug_mode # js add

        self.labels = []

        self.sim_results = []
        self.sim_result = np.empty(self.output_size)

        # FOR DEBUG
        self._sim_excution_time = 0 
        self._input = None 
        self._status = 'board_command.NONE' 
        self.naalDict = dict()
      
        # FOR DEBUG
        self.naalDict['debugInfo'] = list()

        self.debugInfo = dict()
        self.debugInfo['DATA'] = self._input
        self.debugInfo['HARDWARE'] = self.hardware
        self.debugInfo['STATUS'] = self._status
        self.debugInfo['OUTPUT'] = None
        self.debugInfo['SIM_TIME'] = 0
        self.debugInfo['C_TIME'] = 0
	
        self.writeJson()
        self.__init_hardware() 

    # FOR DEBUG
    def writeJson(self):
        if self.debug_mode is not True:
            return

        if os.path.isfile(json_path):
            with open(json_path, 'r') as f:
                self.naalDict = json.load(f)

        self.naalDict['debugInfo'].append(copy.deepcopy(self.debugInfo))	
        json.dump(self.naalDict, open(json_path, 'w'), indent=4)

    def __init_hardware(self):
        if self.hardware == 'de1' or self.hardware == 'pynq' or self.hardware == 'pynq1':
            self.sim = NaalFpga(self.input_size, self.output_size ,fpga_name = self.hardware, npz_path=self.npz_path, dt = self.dt, debug_mode = self.debug_mode)
            self.sim.NAAL_command() # INIT
            self.status = self.get_sim_status() # js add

            self.sim.NAAL_command(board_command.START) # START
            self.status = self.get_sim_status() # js add
        elif self.hardware == "loihi":
            self.sim = NaalLoihi(self.npz_path, self.dt)
        elif self.hardware == "digital_snn":
            if self.input_size != 81:
                assert "Digital_snn only support [81] input size"
                raise
            self.sim = NaalDigital()
            
        else:
            assert self.hardware is None, "Please, set hardware"
            
    def __stop_hardware(self):
        if self.hardware == 'de1' or self.hardware == 'pynq' or self.hardware == 'pynq1':
            self.sim.NAAL_command(board_command.STOP) # STOP
            self.status = self.get_sim_status() # FOR DEBUG
            return board_command.STOP.value
        elif self.hardware == "loihi":
            pass
        elif self.hardware == "digital":
            pass   
            
    def set_sim_data(self, labels, data_type = None):
        assert data_type is not None, "Please define data type (ex: data_type = img or voice)"
        self.labels = np.array(labels)
        self.data_type = data_type
        self.sim.set_sim_data(labels = labels, data_type = data_type) 
            
    def get_sim_status(self):
        return self.sim.NAAL_status()
    
    def run(self, data, sim_time=0, answer = None):
        self.input = data 

        if self.hardware == "de1" or self.hardware == "pynq" or self.hardware == "loihi":
            if answer is not None:
                self.sim.answer = answer

            sim_cnt = sim_time / self.dt

            # FOR DEBUG
            self.status = "board_command.START" 
            result, execution_time = self.sim.steps(int(sim_cnt), data)

            self.step += 1 
            #self.debugInfo['SIM_TIME'] += sim_time 
            #self.debugInfo['C_TIME'] = self.dt * self.step 
            #self.debugInfo['OUTPUT'] = result.tolist() 

            for idx in range (0, self.output_size):
                self.sim_result[idx] = result[idx]

            self.sim_results.append(copy.copy(self.sim_result))
            self.sim_excution_time = execution_time
        else:
            result, execution_time = self.sim.steps(data[0])
            
            self.sim_result = result
            self.sim_excution_time = execution_time
            self.sim_results.append(copy.copy(self.sim_result))

	    # FOR DEBUG
        if self.debug_mode is True:
            with open(json_path, 'r') as json_file:
                self.naalDict = json.load(json_file)

        self.debugInfo = copy.deepcopy(self.naalDict['debugInfo'][-1])
        #self.debugInfo['OUTPUT'] = result.tolist() 
        self.debugInfo['C_TIME'] = 0
        # PAUSE
        self.status = self.get_sim_status() # js add

    def get_result(self):
        return self.sim_result, self.sim_excution_time
    
    def probe_results(self):
        return self.sim_results
    
    def stop_hardware(self):
        self.__stop_hardware()
        for sec in range(0, 4):
            print("Stop hardware...", 3 - sec)
            time.sleep(1)
        
        return board_command.STOP.value
    
    def build_loihi(self, sim_time, input_shape, n_parallel):
        if self.hardware is not "loihi":
            assert "only support loihi"
        self.sim.build_loihi(sim_time, input_shape, n_parallel)

    # FOR DEBUG
    @property
    def input(self):
        return self._input

    @input.setter
    def input(self, value):
        self._input = value
        self.debugInfo['DATA'] = self._input
        self.writeJson()

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value
        self.debugInfo['STATUS'] = self._status
        self.writeJson()
