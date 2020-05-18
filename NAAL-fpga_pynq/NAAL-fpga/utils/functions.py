import struct
import numpy as np


def reg2float(reg_val):
    ''' pack reg val (int) into bytes, then unpack as float'''
    return struct.unpack('>f', struct.pack('>i', reg_val))[0]


def float2reg(float_val):
    ''' pack float into bytes, then unpack as reg val (int) '''
    return struct.unpack('<i', struct.pack('<f', float_val))[0]


def pack(floatlist):
    ''' pack 2 float32 into one 64b packet'''
    return struct.pack('2f', *floatlist)


def unpack(packet):
    ''' unpack 64b packet into 2 float32'''
    return np.array(struct.unpack('2f', packet))
