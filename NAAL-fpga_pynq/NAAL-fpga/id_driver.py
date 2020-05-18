import os

from pynq import Overlay, DefaultIP

from utils.paths import lib_path


class DNAMemoryMap(DefaultIP):
    def __init__(self, description):
        super().__init__(description)

    bindto = ['ABR:user:zynq_AXI_DNA:1.0']
    # found in ip_dict above as 'type'

    # Creating 'getter' for mmio registers
    @property
    def reg0(self):
        return self.read(0x00)

    @property
    def reg1(self):
        return self.read(0x04)

    @property
    def reg2(self):
        return self.read(0x08)

    @property
    def reg3(self):
        return self.read(0x0C)


class IDDriver(object):
    def __init__(self):

        bitstream = os.path.join(lib_path, 'dna_extractor.bit')

        # Load bitstream
        ol = Overlay(os.path.join(bitstream))
        ol.download()

        # Read both 32b register containing DNA
        ID0 = ol.zynq_AXI_DNA_0.reg0
        ID1 = ol.zynq_AXI_DNA_0.reg1

        # Concatenate into a single 64b value
        self.id_bytes = (ID0.to_bytes(4, 'big') + ID1.to_bytes(4, 'big'))
        self.id_int = int.from_bytes(self.id_bytes, 'big')
