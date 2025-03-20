from m8.api import M8Block, load_class, split_byte, join_nibbles

# Module-level constants
BLOCK_SIZE = 6
BLOCK_COUNT = 4

# Map modulator types to their class paths
MODULATOR_TYPES = {
    0x00: "m8.api.modulators.M8AHDEnvelope",
    0x02: "m8.api.modulators.M8DrumEnvelope",
    0x01: "m8.api.modulators.M8ADSREnvelope",
    0x03: "m8.api.modulators.M8LFO",
    0x04: "m8.api.modulators.M8TriggerEnvelope",
    0x05: "m8.api.modulators.M8TrackingEnvelope"
}

# Default modulator configurations
DEFAULT_MODULATOR_CONFIGS = [0x00, 0x00, 0x03, 0x03]  # 2 AHD envelopes, 2 LFOs

class M8ModulatorBase:
    """Base class for all M8 modulators with parameter management and serialization."""
    
    TYPE_DEST_BYTE_OFFSET = 0
    AMOUNT_OFFSET = 1
    PARAM_START_OFFSET = 2
    
    TYPE_NIBBLE_POS = 0  # Upper 4 bits
    DEST_NIBBLE_POS = 1  # Lower 4 bits
    
    DEFAULT_DESTINATION = 0x0
    DEFAULT_AMOUNT = 0xFF
    EMPTY_DESTINATION = 0x0
    
    _common_defs = [
        ("destination", DEFAULT_DESTINATION),  # Common parameter: modulation destination
        ("amount", DEFAULT_AMOUNT)             # Common parameter: modulation amount
    ]
    
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
        raise NotImplementedError("Subclasses must implement _get_type()")
    
    @classmethod
    def read(cls, data):
        instance = cls()
        
        if len(data) > 0:
            type_dest = data[cls.TYPE_DEST_BYTE_OFFSET]
            instance.type, instance.destination = split_byte(type_dest)
            
            # Read amount field
            if len(data) > 1:
                instance.amount = data[cls.AMOUNT_OFFSET]
            
            # Read specific parameters for this modulator type
            for i, (name, _) in enumerate(instance._param_defs, cls.PARAM_START_OFFSET):
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
        return self.destination == self.EMPTY_DESTINATION
    
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
    """Attack-Hold-Decay envelope for controlling parameters over time."""
    TYPE_VALUE = 0x0
    
    DEFAULT_ATTACK = 0x0
    DEFAULT_HOLD = 0x0
    DEFAULT_DECAY = 0x80
    
    _param_defs = [
        ("attack", DEFAULT_ATTACK),
        ("hold", DEFAULT_HOLD),
        ("decay", DEFAULT_DECAY)
    ]
    
    def _get_type(self):
        return self.TYPE_VALUE  # AHD envelope type

class M8ADSREnvelope(M8ModulatorBase):
    """Attack-Decay-Sustain-Release envelope for sustained notes."""
    TYPE_VALUE = 0x1
    
    DEFAULT_ATTACK = 0x0
    DEFAULT_DECAY = 0x80
    DEFAULT_SUSTAIN = 0x80
    DEFAULT_RELEASE = 0x80
    
    _param_defs = [
        ("attack", DEFAULT_ATTACK),
        ("decay", DEFAULT_DECAY),
        ("sustain", DEFAULT_SUSTAIN),
        ("release", DEFAULT_RELEASE)
    ]
    
    def _get_type(self):
        return self.TYPE_VALUE  # ADSR envelope type

class M8DrumEnvelope(M8ModulatorBase):
    """Three-stage envelope optimized for percussive sounds."""
    TYPE_VALUE = 0x2
    
    DEFAULT_PEAK = 0x0
    DEFAULT_BODY = 0x10
    DEFAULT_DECAY = 0x80
    
    _param_defs = [
        ("peak", DEFAULT_PEAK),
        ("body", DEFAULT_BODY),
        ("decay", DEFAULT_DECAY)
    ]
    
    def _get_type(self):
        return self.TYPE_VALUE  # Drum envelope type
    
class M8LFO(M8ModulatorBase):
    """Low Frequency Oscillator for cyclic modulation (vibrato, tremolo, etc)."""
    TYPE_VALUE = 0x3
    
    DEFAULT_OSCILLATOR = 0x0
    DEFAULT_TRIGGER = 0x0
    DEFAULT_FREQUENCY = 0x10
    
    _param_defs = [
        ("oscillator", DEFAULT_OSCILLATOR),
        ("trigger", DEFAULT_TRIGGER),
        ("frequency", DEFAULT_FREQUENCY)
    ]
    
    def _get_type(self):
        return self.TYPE_VALUE  # LFO type

class M8TriggerEnvelope(M8ModulatorBase):
    """Envelope triggered by external sources with attack, hold, and decay stages."""
    TYPE_VALUE = 0x4
    
    DEFAULT_ATTACK = 0x0
    DEFAULT_HOLD = 0x0
    DEFAULT_DECAY = 0x40
    DEFAULT_SOURCE = 0x00
    
    _param_defs = [
        ("attack", DEFAULT_ATTACK),
        ("hold", DEFAULT_HOLD),
        ("decay", DEFAULT_DECAY),
        ("source", DEFAULT_SOURCE)
    ]
    
    def _get_type(self):
        return self.TYPE_VALUE  # Trigger envelope type

class M8TrackingEnvelope(M8ModulatorBase):
    """Maps input values to output modulation for keyboard tracking and mapping."""
    TYPE_VALUE = 0x5
    
    DEFAULT_SOURCE = 0x0
    DEFAULT_LOW_VALUE = 0x0
    DEFAULT_HIGH_VALUE = 0x7F
    
    _param_defs = [
        ("source", DEFAULT_SOURCE),
        ("low_value", DEFAULT_LOW_VALUE),
        ("high_value", DEFAULT_HIGH_VALUE)
    ]
    
    def _get_type(self):
        return self.TYPE_VALUE  # Tracking envelope type
    
class M8Modulators(list):
    """Collection of modulators for an M8 instrument with type-aware handling."""
    
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
                
            first_byte = block_data[M8ModulatorBase.TYPE_DEST_BYTE_OFFSET]
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
        # Only include non-empty modulators with their position indices
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
        instance = cls()
        instance.clear()
        
        # Initialize with empty blocks
        for _ in range(BLOCK_COUNT):
            instance.append(M8Block())
        
        # Set items at their specified indexes
        if items:
            for mod_data in items:
                # Get index from data
                index = mod_data["index"]
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
    """Create a list of default modulators (2 AHD envelopes and 2 LFOs)."""
    result = []
    
    for mod_type in DEFAULT_MODULATOR_CONFIGS:
        if mod_type in MODULATOR_TYPES:
            full_path = MODULATOR_TYPES[mod_type]
            ModClass = load_class(full_path)
            result.append(ModClass())
        else:
            result.append(M8Block())
    return result
