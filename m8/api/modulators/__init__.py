from m8.api import M8Block, load_class, split_byte, join_nibbles

BLOCK_SIZE = 6
BLOCK_COUNT = 4

# Map instrument types to their modulator type paths
MODULATOR_TYPES = {
    0x01: {  # MacroSynth
        0x00: "m8.api.modulators.macrosynth.M8MacroSynthAHDEnvelope",
        0x01: "m8.api.modulators.macrosynth.M8MacroSynthADSREnvelope",
        0x03: "m8.api.modulators.macrosynth.M8MacroSynthLFO"
    }
}

# Default modulator configurations per instrument type
DEFAULT_MODULATOR_CONFIGS = {
    0x01: [0x00, 0x00, 0x03, 0x03]  # MacroSynth: 2 AHD envelopes, 2 LFOs
}

class M8ModulatorBase:
    """Base class for all M8 modulators across instrument types."""
    
    def __init__(self, **kwargs):
        self.destination = 0x0
        self.amount = 0xFF
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def read(cls, data):
        instance = cls()
        if len(data) > 0:
            type_dest = data[0]
            instance.type, instance.destination = split_byte(type_dest)
            if len(data) > 1:
                instance.amount = data[1]
        return instance
    
    def write(self):
        buffer = bytearray()
        type_dest = join_nibbles(self.type, self.destination)
        buffer.append(type_dest)
        buffer.append(self.amount)
        return bytes(buffer)
    
    def clone(self):
        instance = self.__class__()
        for key, value in vars(self).items():
            setattr(instance, key, value)
        return instance
    
    def as_dict(self):
        return {k: v for k, v in vars(self).items() if not k.startswith('_')}
    
    @classmethod
    def from_dict(cls, data):
        instance = cls()
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        return instance

class M8Modulators(list):
    def __init__(self, instrument_type=0x01, items=None):
        super().__init__()
        self.instrument_type = instrument_type
        items = items or []
        
        for item in items:
            self.append(item)
            
        while len(self) < BLOCK_COUNT:
            self.append(M8Block())
    
    @classmethod
    def read(cls, data, instrument_type=0x01):
        instance = cls(instrument_type=instrument_type)
        instance.clear()
        
        for i in range(BLOCK_COUNT):
            start = i * BLOCK_SIZE
            block_data = data[start:start + BLOCK_SIZE]
            
            if len(block_data) < 1:
                instance.append(M8Block())
                continue
                
            first_byte = block_data[0]
            mod_type, _ = split_byte(first_byte)
            
            if instrument_type in MODULATOR_TYPES and mod_type in MODULATOR_TYPES[instrument_type]:
                ModClass = load_class(MODULATOR_TYPES[instrument_type][mod_type])
                instance.append(ModClass.read(block_data))
            else:
                instance.append(M8Block.read(block_data))
        
        return instance
    
    def clone(self):
        instance = self.__class__(instrument_type=self.instrument_type)
        instance.clear()
        
        for mod in self:
            if hasattr(mod, 'clone'):
                instance.append(mod.clone())
            else:
                instance.append(mod)
        
        return instance
    
    def write(self):
        result = bytearray()
        for mod in self:
            mod_data = mod.write() if hasattr(mod, 'write') else bytes([0] * BLOCK_SIZE)
            if len(mod_data) < BLOCK_SIZE:
                mod_data = mod_data + bytes([0x0] * (BLOCK_SIZE - len(mod_data)))
            elif len(mod_data) > BLOCK_SIZE:
                mod_data = mod_data[:BLOCK_SIZE]
            result.extend(mod_data)
        return bytes(result)

    def as_dict(self):
        """Convert modulators to dictionary for serialization"""
        return [mod.as_dict() if hasattr(mod, "as_dict") else {"data": list(mod.data)} 
                for mod in self]
        
    @classmethod
    def from_dict(cls, data, instrument_type=0x01):
        """Create modulators from a dictionary"""
        instance = cls(instrument_type=instrument_type)
        instance.clear()
        
        # Always expect exactly 4 modulators worth of data
        for i in range(BLOCK_COUNT):
            if i < len(data) and data[i]:
                mod_data = data[i]
                if "type" in mod_data and instrument_type in MODULATOR_TYPES:
                    mod_type = mod_data["type"]
                    if mod_type in MODULATOR_TYPES[instrument_type]:
                        ModClass = load_class(MODULATOR_TYPES[instrument_type][mod_type])
                        instance.append(ModClass.from_dict(mod_data))
                    else:
                        instance.append(M8Block.from_dict(mod_data))
                else:
                    instance.append(M8Block.from_dict(mod_data))
            else:
                instance.append(M8Block())
        
        return instance

def create_default_modulators(instrument_type):
    result = []
    if instrument_type not in MODULATOR_TYPES or instrument_type not in DEFAULT_MODULATOR_CONFIGS:
        return [M8Block() for _ in range(BLOCK_COUNT)]
    
    for mod_type in DEFAULT_MODULATOR_CONFIGS[instrument_type]:
        if mod_type in MODULATOR_TYPES[instrument_type]:
            full_path = MODULATOR_TYPES[instrument_type][mod_type]
            ModClass = load_class(full_path)
            result.append(ModClass())
        else:
            result.append(M8Block())
    return result
