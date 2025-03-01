from m8.api import M8Block, load_class, split_byte, join_nibbles

BLOCK_SIZE = 6
BLOCK_COUNT = 4

# Map modulator types to their class paths - no longer instrument-specific
MODULATOR_TYPES = {
    0x00: "m8.api.modulators.M8AHDEnvelope",
    0x01: "m8.api.modulators.M8ADSREnvelope",
    0x03: "m8.api.modulators.M8LFO"
}

# Default modulator configurations - no longer instrument-specific
DEFAULT_MODULATOR_CONFIGS = [0x00, 0x00, 0x03, 0x03]  # 2 AHD envelopes, 2 LFOs

class M8ModulatorBase:
    """Base class for all M8 modulators."""
    
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

# Specific modulator implementations

class M8AHDEnvelope(M8ModulatorBase):
    def __init__(self, **kwargs):
        # Default field values
        self.type = 0x0
        self.destination = 0x0
        self.amount = 0xFF
        self.attack = 0x0
        self.hold = 0x0
        self.decay = 0x80
        
        # Apply any provided kwargs
        super().__init__(**kwargs)
    
    @classmethod
    def read(cls, data):
        instance = super().read(data)
        
        # Read specific fields for AHD envelope
        if len(data) > 2:
            instance.attack = data[2]
        if len(data) > 3:
            instance.hold = data[3]
        if len(data) > 4:
            instance.decay = data[4]
        
        return instance
    
    def write(self):
        # Get the common header (type/dest and amount)
        buffer = bytearray(super().write())
        
        # Add AHD-specific fields
        buffer.append(self.attack)
        buffer.append(self.hold)
        buffer.append(self.decay)
        
        # Pad to ensure proper size
        while len(buffer) < 6:
            buffer.append(0x0)
        
        return bytes(buffer)

class M8ADSREnvelope(M8ModulatorBase):
    def __init__(self, **kwargs):
        # Default field values
        self.type = 0x1
        self.destination = 0x0
        self.amount = 0xFF
        self.attack = 0x0
        self.decay = 0x80
        self.sustain = 0x80
        self.release = 0x80
        
        # Apply any provided kwargs
        super().__init__(**kwargs)
    
    @classmethod
    def read(cls, data):
        instance = super().read(data)
        
        # Read specific fields for ADSR envelope
        if len(data) > 2:
            instance.attack = data[2]
        if len(data) > 3:
            instance.decay = data[3]
        if len(data) > 4:
            instance.sustain = data[4]
        if len(data) > 5:
            instance.release = data[5]
        
        return instance
    
    def write(self):
        # Get the common header (type/dest and amount)
        buffer = bytearray(super().write())
        
        # Add ADSR-specific fields
        buffer.append(self.attack)
        buffer.append(self.decay)
        buffer.append(self.sustain)
        buffer.append(self.release)
        
        return bytes(buffer)

class M8LFO(M8ModulatorBase):
    def __init__(self, **kwargs):
        # Default field values
        self.type = 0x3
        self.destination = 0x0
        self.amount = 0xFF
        self.shape = 0x0
        self.trigger = 0x0
        self.freq = 0x10
        self.retrigger = 0x0
        
        # Apply any provided kwargs
        super().__init__(**kwargs)
    
    @classmethod
    def read(cls, data):
        instance = super().read(data)
        
        # Read specific fields for LFO
        if len(data) > 2:
            instance.shape = data[2]
        if len(data) > 3:
            instance.trigger = data[3]
        if len(data) > 4:
            instance.freq = data[4]
        if len(data) > 5:
            instance.retrigger = data[5]
        
        return instance
    
    def write(self):
        # Get the common header (type/dest and amount)
        buffer = bytearray(super().write())
        
        # Add LFO-specific fields
        buffer.append(self.shape)
        buffer.append(self.trigger)
        buffer.append(self.freq)
        buffer.append(self.retrigger)
        
        return bytes(buffer)

class M8Modulators(list):
    def __init__(self, items=None):
        super().__init__()
        items = items or []
        
        for item in items:
            self.append(item)
            
        while len(self) < BLOCK_COUNT:
            self.append(M8Block())
    
    @classmethod
    def read(cls, data):
        instance = cls()
        instance.clear()
        
        for i in range(BLOCK_COUNT):
            start = i * BLOCK_SIZE
            block_data = data[start:start + BLOCK_SIZE]
            
            if len(block_data) < 1:
                instance.append(M8Block())
                continue
                
            first_byte = block_data[0]
            mod_type, _ = split_byte(first_byte)
            
            if mod_type in MODULATOR_TYPES:
                ModClass = load_class(MODULATOR_TYPES[mod_type])
                instance.append(ModClass.read(block_data))
            else:
                instance.append(M8Block.read(block_data))
        
        return instance
    
    def clone(self):
        instance = self.__class__()
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

    def as_list(self):
        """Convert modulators to list for serialization"""
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
        
        return items
            
    @classmethod
    def from_list(cls, items):
        """Create modulators from a list"""
        instance = cls()
        instance.clear()
        
        # Initialize with empty blocks
        for _ in range(BLOCK_COUNT):
            instance.append(M8Block())
        
        # Set items at their specified indexes
        if items:
            for mod_data in items:
                # Get index from data or default to 0
                index = mod_data.get("index", 0)
                if 0 <= index < BLOCK_COUNT:
                    # Remove index field before passing to from_dict
                    mod_dict = {k: v for k, v in mod_data.items() if k != "index"}
                    
                    if "type" in mod_dict and mod_dict["type"] in MODULATOR_TYPES:
                        mod_type = mod_dict["type"]
                        ModClass = load_class(MODULATOR_TYPES[mod_type])
                        instance[index] = ModClass.from_dict(mod_dict)
                    elif "data" in mod_dict:
                        instance[index] = M8Block.from_dict(mod_dict)
        
        return instance
    
def create_default_modulators():
    """Create a list of default modulators"""
    result = []
    
    for mod_type in DEFAULT_MODULATOR_CONFIGS:
        if mod_type in MODULATOR_TYPES:
            full_path = MODULATOR_TYPES[mod_type]
            ModClass = load_class(full_path)
            result.append(ModClass())
        else:
            result.append(M8Block())
    return result
