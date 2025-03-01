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
    
    def is_empty(self):
        """Check if this modulator is empty (destination is 0)"""
        return self.destination == 0x0
    
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
        items = []
        for i, mod in enumerate(self):
            # Only include non-empty modulators
            if hasattr(mod, "is_empty") and not mod.is_empty():
                mod_dict = mod.as_dict()
                # Add index to track position
                mod_dict["index"] = i
                items.append(mod_dict)
            elif isinstance(mod, M8Block) and not mod.is_empty():
                items.append({
                    "data": list(mod.data),
                    "index": i
                })
        
        return {"items": items}
        
    @classmethod
    def from_dict(cls, data, instrument_type=0x01):
        """Create modulators from a dictionary"""
        instance = cls(instrument_type=instrument_type)
        instance.clear()
        
        # Initialize with empty blocks
        for _ in range(BLOCK_COUNT):
            instance.append(M8Block())
        
        # Set items at their specified indexes
        if "items" in data:
            for mod_data in data["items"]:
                # Get index from data or default to 0
                index = mod_data.get("index", 0)
                if 0 <= index < BLOCK_COUNT:
                    # Remove index field before passing to from_dict
                    mod_dict = {k: v for k, v in mod_data.items() if k != "index"}
                    
                    if "type" in mod_dict and instrument_type in MODULATOR_TYPES:
                        mod_type = mod_dict["type"]
                        if mod_type in MODULATOR_TYPES[instrument_type]:
                            ModClass = load_class(MODULATOR_TYPES[instrument_type][mod_type])
                            instance[index] = ModClass.from_dict(mod_dict)
                        else:
                            instance[index] = M8Block.from_dict(mod_dict)
                    elif "data" in mod_dict:
                        instance[index] = M8Block.from_dict(mod_dict)
        
        return instance

def create_default_modulators(instrument_type):
    """Create a list of default modulators for a given instrument type"""
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
