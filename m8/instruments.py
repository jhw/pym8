from m8 import M8Block, NULL, BLANK
from m8.core.object import m8_object_class
from m8.core.list import m8_list_class

from m8.modulators import M8Modulators
import struct

BLOCK_SIZE = 215
BLOCK_COUNT = 128
SYNTH_PARAMS_SIZE = 33
MODULATORS_OFFSET = 63

M8MacroSynthParams = m8_object_class(
    field_map=[
        ("type", None, 0, 1, "UINT8"),
        ("name", " ", 1, 13, "STRING"),  
        ("transpose|eq", 0x41, 13, 14, "UINT4_2"),
        ("table_tick", 0x01, 14, 15, "UINT8"),
        ("volume", NULL, 15, 16, "UINT8"), 
        ("pitch", NULL, 16, 17, "UINT8"), 
        ("fine_tune", 0x80, 17, 18, "UINT8"),
        ("shape", NULL, 18, 19, "UINT8"),
        ("timbre", 0x80, 19, 20, "UINT8"),
        ("color", 0x80, 20, 21, "UINT8"),
        ("degrade", NULL, 21, 22, "UINT8"),
        ("redux", NULL, 22, 23, "UINT8"),
        ("filter_type", NULL, 23, 24, "UINT8"),
        ("filter_cutoff", BLANK, 24, 25, "UINT8"),
        ("filter_resonance", NULL, 25, 26, "UINT8"),
        ("amp_level", NULL, 26, 27, "UINT8"),
        ("amp_limit", NULL, 27, 28, "UINT8"),
        ("mixer_pan", 0x80, 28, 29, "UINT8"),
        ("mixer_dry", 0xC0, 29, 30, "UINT8"),
        ("mixer_chorus", NULL, 30, 31, "UINT8"),
        ("mixer_delay", NULL, 31, 32, "UINT8"),
        ("mixer_reverb", NULL, 32, 33, "UINT8")
    ]
)

class M8InstrumentBase:
    TYPE = None

    def __init__(self, synth_params_class, **kwargs):
        if self.TYPE is not None:
            kwargs.setdefault("type", self.TYPE)
        self.synth_params = synth_params_class(**kwargs)
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

class M8MacroSynth(M8InstrumentBase):
    TYPE = 0x01

    def __init__(self, **kwargs):
        super().__init__(synth_params_class=M8MacroSynthParams, **kwargs)

    @classmethod
    def read(cls, data):
        return super().read(data, synth_params_class=M8MacroSynthParams)

def instrument_row_class(data):
    instr_type = struct.unpack('B', data[:1])[0]
    return M8MacroSynth if instr_type == M8MacroSynth.TYPE else M8Block

M8Instruments = m8_list_class(
    row_size=BLOCK_SIZE,
    row_count=BLOCK_COUNT,
    row_class_resolver=instrument_row_class
)


