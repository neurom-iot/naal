  
import os
import sys

import logging
import configparser
import logging
import numpy as np

configfile_name ="NAAL_config"


logger = logging.getLogger(__name__)            

if sys.platform.startswith('win'):
    config_dir = os.path.expanduser(os.path.join("~", ".NAAL_FPGA"))
else:
    config_dir = os.path.expanduser(os.path.join("~", ".NAAL_FPGA", "NAAL_FPGA"))

install_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
nengo_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir))
examples_dir = os.path.join(install_dir, "examples")


fpga_config = \
    {'NAAL': os.path.join(nengo_dir, 'data', configfile_name),
     'system': os.path.join(install_dir, configfile_name),
     'user': os.path.join(config_dir, "fpga_config"),
     'project': os.path.abspath(os.path.join(os.curdir, configfile_name))}


FPGA_CONFIG_FILES = [fpga_config['NAAL'],
                     fpga_config['system'],
                     fpga_config['user'],
                     fpga_config['project']]


def Is_fpgaboard(fgpaboad_name):
    try :

        config = configparser.ConfigParser()
        config.read(FPGA_CONFIG_FILES[3])
        fpga_config = config[fgpaboad_name]
    except Exception as ex:
        print('config_FPGA config error',ex)
        exit()
    return fpga_config
def config_parser_board(key,value):
    config = configparser.ConfigParser()
    config.read(FPGA_CONFIG_FILES[3])
    try :
        key_config = config[key]
    except Exception as ex:
        return False
    return True

def config_parser(key,value):
    config = configparser.ConfigParser()
    config.read(FPGA_CONFIG_FILES[3])
    try :
        key_config = config[key]
    except Exception as ex:
        print('config_FPGA config error',ex)
        exit()
    return key_config[value]

def set_config(key,value,insert_value):
    config = configparser.ConfigParser()
    config.read(FPGA_CONFIG_FILES[3])
    try :
        key_config = config[key]
    except Exception as ex:
        print('config_FPGA config error',ex)
        exit()

    key_config[value]= str(insert_value)
    with open(FPGA_CONFIG_FILES[3],'w') as f:
        config.write(f)



    




