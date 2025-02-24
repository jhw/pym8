from m8 import M8Block
from m8.api.modulators.macrosynth import M8MacroSynthAHDEnvelope, M8MacroSynthADSREnvelope, M8MacroSynthLFO
from m8.core.list import m8_list_class
from m8.utils.bits import split_byte

import struct

BLOCK_SIZE = 6
BLOCK_COUNT = 4

# Update M8InstrumentBase to use the factory functions
def create_default_modulators(instrument_type):
    return [
        M8MacroSynthAHDEnvelope(),
        M8MacroSynthAHDEnvelope(),
        M8MacroSynthLFO(),
        M8MacroSynthLFO()
    ]

def create_modulator_row_class_resolver(instrument_type):
    """Factory function to create a row class resolver based on instrument type"""
    def resolver(data):
        first_byte = struct.unpack("B", data[:1])[0]
        mod_type, _ = split_byte(first_byte)
        if mod_type == 0x00:
            return M8MacroSynthAHDEnvelope
        elif mod_type == 0x01:
            return M8MacroSynthADSREnvelope
        elif mod_type == 0x03:
            return M8MacroSynthLFO
        else:
            return M8Block

    return resolver

def create_modulators_class(instrument_type):
    """Factory function to create an M8Modulators class based on instrument type"""
    row_class_resolver = create_modulator_row_class_resolver(instrument_type)
    
    return m8_list_class(
        row_size=BLOCK_SIZE,
        row_count=BLOCK_COUNT,
        row_class_resolver=row_class_resolver
    )


