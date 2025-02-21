from m8 import M8Block, load_class
from m8.core.list import m8_list_class
from m8.modulators import M8Modulators

import struct

INSTRUMENT_TYPES = {
    0x01: "m8.instruments.macrosynth.M8MacroSynth"
}

BLOCK_SIZE = 215
BLOCK_COUNT = 128
SYNTH_PARAMS_SIZE = 33
MODULATORS_OFFSET = 63

class M8InstrumentBase:
    def __init__(self, synth_params_class, type, **kwargs):
        self.synth_params = synth_params_class(type=type, **kwargs)
        self.modulators = M8Modulators()

    @classmethod
    def read(cls, data, synth_params_class):
        instance = cls()
        instance.synth_params = synth_params_class.read(data[:SYNTH_PARAMS_SIZE])
        instance.modulators = M8Modulators.read(data[MODULATORS_OFFSET:])
        return instance

    def as_dict(self):
        return {
            "synth": self.synth_params.as_dict(),
            "modulators": [
                mod.as_dict() for mod in self.modulators 
                if isinstance(mod, M8Block) is False  # Skip empty modulator slots
                and (mod.destination != 0)  # Only include modulators with non-zero destination
            ]
        }
    
    def write(self):
        buffer = bytearray()
        buffer.extend(self.synth_params.write())
        # Add padding between synth params and modulators
        buffer.extend(bytes([0] * (MODULATORS_OFFSET - SYNTH_PARAMS_SIZE)))
        buffer.extend(self.modulators.write())
        return bytes(buffer)


def instrument_row_class(data):
    instr_type = struct.unpack('B', data[:1])[0]
    if instr_type in INSTRUMENT_TYPES:
        return load_class(INSTRUMENT_TYPES[instr_type])
    return M8Block

M8Instruments = m8_list_class(
    row_size=BLOCK_SIZE,
    row_count=BLOCK_COUNT,
    row_class_resolver=instrument_row_class
)
