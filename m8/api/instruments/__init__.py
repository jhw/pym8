from m8 import M8Block
from m8.api import M8IndexError, load_class
from m8.api.modulators import create_modulators_class, create_default_modulators
from m8.core.list import m8_list_class

import struct

INSTRUMENT_TYPES = {
    0x01: "macro_synth"
}

BLOCK_SIZE = 215
BLOCK_COUNT = 128
SYNTH_PARAMS_SIZE = 33
MODULATORS_OFFSET = 63

def get_class_paths(base_name):
    """Get instrument and params class paths from base name"""
    # Convert snake_case to PascalCase without underscores for class names
    class_prefix = "".join(word.title() for word in base_name.split("_"))
    return (
        f"m8.api.instruments.macrosynth.M8{class_prefix}",
        f"m8.api.instruments.macrosynth.M8{class_prefix}Params"
    )

class M8InstrumentBase:
    def __init__(self, **kwargs):
        # First create the synth params
        _, params_path = get_class_paths(INSTRUMENT_TYPES[0x01])  # For now hardcoded to MacroSynth
        params_class = load_class(params_path)
        self.synth_params = params_class(**kwargs)
        
        # Now create modulators using the type from synth params
        M8Modulators = create_modulators_class(self.synth_params.type)
        default_modulators = create_default_modulators(self.synth_params.type)
        self.modulators = M8Modulators(items=default_modulators)

    @classmethod
    def read(cls, data):
        # Get the type from the first byte and validate
        instr_type = data[0]
        if instr_type not in INSTRUMENT_TYPES:
            raise ValueError(f"Unknown instrument type: {instr_type}")
            
        # Create instance and load its params
        instance = cls()
        _, params_path = get_class_paths(INSTRUMENT_TYPES[instr_type])
        params_class = load_class(params_path)
        instance.synth_params = params_class.read(data[:SYNTH_PARAMS_SIZE])
        
        # Create modulators based on the loaded params
        M8Modulators = create_modulators_class(instance.synth_params.type)
        instance.modulators = M8Modulators.read(data[MODULATORS_OFFSET:])
        
        return instance

    @property
    def available_modulator_slot(self):
        for slot_idx, mod in enumerate(self.modulators):
            if isinstance(mod, M8Block) or mod.destination == 0:
                return slot_idx
        return None

    def add_modulator(self, modulator):
        slot = self.available_modulator_slot
        if slot is None:
            raise M8IndexError("No empty modulator slots available in this instrument")
            
        self.modulators[slot] = modulator
        return slot
        
    def set_modulator(self, modulator, slot):
        if not (0 <= slot < len(self.modulators)):
            raise M8IndexError(f"Modulator slot index must be between 0 and {len(self.modulators)-1}")
            
        self.modulators[slot] = modulator

    def as_dict(self):
        return {
            "synth": self.synth_params.as_dict(),
            "modulators": [
                mod.as_dict() for mod in self.modulators 
                if isinstance(mod, M8Block) is False
                and (mod.destination != 0)
            ]
        }
    
    def write(self):
        buffer = bytearray()
        buffer.extend(self.synth_params.write())
        buffer.extend(bytes([0] * (MODULATORS_OFFSET - SYNTH_PARAMS_SIZE)))
        buffer.extend(self.modulators.write())
        return bytes(buffer)

def instrument_row_class(data):
    """Factory function to create appropriate instrument class based on type byte"""
    instr_type = struct.unpack('B', data[:1])[0]
    if instr_type in INSTRUMENT_TYPES:
        instrument_path, _ = get_class_paths(INSTRUMENT_TYPES[instr_type])
        return load_class(instrument_path)
    return M8Block

M8Instruments = m8_list_class(
    row_size=BLOCK_SIZE,
    row_count=BLOCK_COUNT,
    row_class_resolver=instrument_row_class)
