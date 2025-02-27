from m8 import M8Block
from m8.api import M8IndexError, load_class
from m8.api.modulators import create_modulators_class, create_default_modulators
from m8.core.list import m8_list_class
from m8.core.serialization import from_json, to_json

INSTRUMENT_TYPES = {
    0x01: "m8.api.instruments.macrosynth.M8MacroSynth"
}

BLOCK_SIZE = 215
BLOCK_COUNT = 128
SYNTH_PARAMS_SIZE = 33
MODULATORS_OFFSET = 63

class M8InstrumentBase:
    def __init__(self, **kwargs):
        # Get params class path from instrument path
        params_path = f"{INSTRUMENT_TYPES[0x01]}Params"  # For now hardcoded to MacroSynth
        params_class = load_class(params_path)
        self.synth_params = params_class(**kwargs)
        
        # Create modulators using the type from synth params
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
        params_path = f"{INSTRUMENT_TYPES[instr_type]}Params"
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
        """Convert instrument to dictionary for serialization"""
        return {
            "__class__": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "type": self.synth_params.type,
            "synth_params": self.synth_params.as_dict(),
            "modulators": [mod.as_dict() if hasattr(mod, "as_dict") else None 
                           for mod in self.modulators]
        }
    
    def write(self):
        buffer = bytearray()
        buffer.extend(self.synth_params.write())
        buffer.extend(bytes([0] * (MODULATORS_OFFSET - SYNTH_PARAMS_SIZE)))
        buffer.extend(self.modulators.write())
        return bytes(buffer)
        
    @classmethod
    def from_dict(cls, data):
        """Create an instrument from a dictionary"""
        instance = cls()
        
        # Get synth params class
        if "type" in data and "synth_params" in data:
            instr_type = data["type"]
            if instr_type in INSTRUMENT_TYPES:
                params_path = f"{INSTRUMENT_TYPES[instr_type]}Params"
                params_class = load_class(params_path)
                instance.synth_params = params_class.from_dict(data["synth_params"])
        
        # Deserialize modulators
        if "modulators" in data:
            # Create appropriate modulators class
            M8Modulators = create_modulators_class(instance.synth_params.type)
            instance.modulators = M8Modulators()
            
            from m8.api.modulators import MODULATOR_TYPES
            
            for i, mod_data in enumerate(data["modulators"]):
                if mod_data is not None and i < len(instance.modulators):
                    # Determine modulator type
                    if "type" in mod_data and instance.synth_params.type in MODULATOR_TYPES:
                        mod_type = mod_data["type"]
                        if mod_type in MODULATOR_TYPES[instance.synth_params.type]:
                            ModClass = load_class(MODULATOR_TYPES[instance.synth_params.type][mod_type])
                            instance.modulators[i] = ModClass.from_dict(mod_data)
        
        return instance
        
    def to_json(self, indent=None):
        """Convert instrument to JSON string"""
        return to_json(self, indent=indent)

    @classmethod
    def from_json(cls, json_str):
        """Create an instance from a JSON string"""
        return from_json(json_str, cls)

def instrument_row_class(data):
    """Factory function to create appropriate instrument class based on type byte"""
    instr_type = data[0]
    if instr_type in INSTRUMENT_TYPES:
        return load_class(INSTRUMENT_TYPES[instr_type])
    return M8Block

M8Instruments = m8_list_class(
    row_size=BLOCK_SIZE,
    row_count=BLOCK_COUNT,
    row_class_resolver=instrument_row_class)
