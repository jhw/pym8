from m8.api import M8Block, load_class, split_byte, join_nibbles

BLOCK_SIZE = 6
BLOCK_COUNT = 4

# Map modulator types to their class paths
MODULATOR_TYPES = {
    0x00: "m8.api.modulators.M8AHDEnvelope",
    0x01: "m8.api.modulators.M8ADSREnvelope",
    0x03: "m8.api.modulators.M8LFO"
}

# Default modulator configurations
DEFAULT_MODULATOR_CONFIGS = [0x00, 0x00, 0x03, 0x03]  # 2 AHD envelopes, 2 LFOs

class M8ModulatorBase:
    """Base class for all M8 modulators with param_defs support."""
    
    # Common fields shared by all modulator types
    _common_defs = [
        ("destination", 0x0),  # Common parameter: modulation destination
        ("amount", 0xFF)       # Common parameter: modulation amount
    ]
    
    # Specific fields to be defined in subclasses
    _param_defs = []
    
    def __init__(self, **kwargs):
        # Set type for each modulator
        self.type = self._get_type()
        
        # Initialize parameters with defaults from _common_defs and subclass _param_defs
        for name, default in self._common_defs + self._param_defs:
            setattr(self, name, default)
        
        # Apply any provided kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def _get_type(self):
        """Get the modulator type. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _get_type()")
    
    @classmethod
    def read(cls, data):
        instance = cls()
        
        if len(data) > 0:
            type_dest = data[0]
            instance.type, instance.destination = split_byte(type_dest)
            
            # Read amount field
            if len(data) > 1:
                instance.amount = data[1]
            
            # Read specific parameters for this modulator type
            for i, (name, _) in enumerate(instance._param_defs, 2):  # Start at offset 2
                if i < len(data):
                    setattr(instance, name, data[i])
        
        return instance
    
    def write(self):
        buffer = bytearray()
        
        # Write type/destination as combined byte
        type_dest = join_nibbles(self.type, self.destination)
        buffer.append(type_dest)
        
        # Write amount
        buffer.append(self.amount)
        
        # Write specific parameters
        for name, _ in self._param_defs:
            buffer.append(getattr(self, name))
        
        # Pad to ensure proper size if needed
        while len(buffer) < BLOCK_SIZE:
            buffer.append(0x0)
        
        return bytes(buffer)
    
    def clone(self):
        instance = self.__class__()
        for name, _ in self._common_defs + self._param_defs:
            setattr(instance, name, getattr(self, name))
        # Also copy type explicitly
        instance.type = self.type
        return instance
    
    def is_empty(self):
        """Check if this modulator is empty (destination is 0)"""
        return self.destination == 0x0
    
    def as_dict(self):
        result = {}
        for name, _ in self._common_defs + self._param_defs:
            result[name] = getattr(self, name)
        # Also include type explicitly
        result["type"] = self.type
        return result
    
    @classmethod
    def from_dict(cls, data):
        instance = cls()
        for name, _ in instance._common_defs + instance._param_defs:
            if name in data:
                setattr(instance, name, data[name])
        # Also set type explicitly
        if "type" in data:
            instance.type = data["type"]
        return instance

# Specific modulator implementations

class M8AHDEnvelope(M8ModulatorBase):
    _param_defs = [
        ("attack", 0x0),
        ("hold", 0x0),
        ("decay", 0x80)
    ]
    
    def _get_type(self):
        return 0x0  # AHD envelope type

class M8ADSREnvelope(M8ModulatorBase):
    _param_defs = [
        ("attack", 0x0),
        ("decay", 0x80),
        ("sustain", 0x80),
        ("release", 0x80)
    ]
    
    def _get_type(self):
        return 0x1  # ADSR envelope type

class M8LFO(M8ModulatorBase):
    _param_defs = [
        ("shape", 0x0),
        ("trigger", 0x0),
        ("freq", 0x10),
        ("retrigger", 0x0)
    ]
    
    def _get_type(self):
        return 0x3  # LFO type

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
