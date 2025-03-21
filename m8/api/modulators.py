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
    """Base class for all M8 modulators with param_defs support.
    
    This class provides the foundation for all modulator types in the M8 system,
    handling common functionality such as serialization, parameter management, 
    and type identification. Specific modulator types inherit from this base.
    """
    
    # Constants for byte offsets within a modulator block
    TYPE_DEST_BYTE_OFFSET = 0
    AMOUNT_OFFSET = 1
    PARAM_START_OFFSET = 2
    
    # Bit positions for type and destination in the first byte
    TYPE_NIBBLE_POS = 0  # Upper 4 bits
    DEST_NIBBLE_POS = 1  # Lower 4 bits
    
    # Default values
    DEFAULT_DESTINATION = 0x0
    DEFAULT_AMOUNT = 0xFF
    EMPTY_DESTINATION = 0x0
    
    # Common fields shared by all modulator types
    _common_defs = [
        ("destination", DEFAULT_DESTINATION),  # Common parameter: modulation destination
        ("amount", DEFAULT_AMOUNT)             # Common parameter: modulation amount
    ]
    
    # Specific fields to be defined in subclasses
    _param_defs = []
    
    def __init__(self, **kwargs):
        """Initialize a modulator with default values and optional overrides.
        
        Args:
            **kwargs: Optional parameter overrides for any attributes defined 
                     in _common_defs or _param_defs
        """
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
        """Get the modulator type. To be implemented by subclasses.
        
        Returns:
            int: The modulator type identifier (0-255)
            
        Raises:
            NotImplementedError: If not implemented by the subclass
        """
        raise NotImplementedError("Subclasses must implement _get_type()")
    
    @classmethod
    def read(cls, data):
        """Create a modulator from binary data.
        
        Args:
            data: Binary data containing modulator parameters
            
        Returns:
            M8ModulatorBase: A new instance with values from the binary data
        """
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
        """Convert the modulator to binary data.
        
        Returns:
            bytes: Binary representation of the modulator
        """
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
        """Create a deep copy of this modulator.
        
        Returns:
            M8ModulatorBase: A new instance with the same values
        """
        instance = self.__class__()
        for name, _ in self._common_defs + self._param_defs:
            setattr(instance, name, getattr(self, name))
        # Also copy type explicitly
        instance.type = self.type
        return instance
    
    def is_empty(self):
        """Check if this modulator is empty (destination is 0).
        
        Returns:
            bool: True if the modulator has an empty destination, False otherwise
        """
        return self.destination == self.EMPTY_DESTINATION
    
    def as_dict(self):
        """Convert modulator to dictionary for serialization.
        
        Returns:
            dict: Dictionary representation of all modulator parameters
        """
        result = {}
        for name, _ in self._common_defs + self._param_defs:
            result[name] = getattr(self, name)
        # Also include type explicitly
        result["type"] = self.type
        return result
    
    @classmethod
    def from_dict(cls, data):
        """Create a modulator from a dictionary.
        
        Args:
            data: Dictionary containing modulator parameters
            
        Returns:
            M8ModulatorBase: A new instance with values from the dictionary
        """
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
    """Attack-Hold-Decay (AHD) envelope modulator.
    
    A simple envelope with attack, hold, and decay stages.
    Used for controlling amplitude and other parameters over time.
    """
    # Constants for AHD envelope
    TYPE_VALUE = 0x0
    
    # Default parameter values
    DEFAULT_ATTACK = 0x0
    DEFAULT_HOLD = 0x0
    DEFAULT_DECAY = 0x80
    
    _param_defs = [
        ("attack", DEFAULT_ATTACK),
        ("hold", DEFAULT_HOLD),
        ("decay", DEFAULT_DECAY)
    ]
    
    def _get_type(self):
        """Get the modulator type identifier.
        
        Returns:
            int: The AHD envelope type value (0)
        """
        return self.TYPE_VALUE  # AHD envelope type

class M8ADSREnvelope(M8ModulatorBase):
    """Attack-Decay-Sustain-Release (ADSR) envelope modulator.
    
    A standard ADSR envelope with attack, decay, sustain, and release stages.
    Provides more control than the AHD envelope for sustained notes.
    """
    # Constants for ADSR envelope
    TYPE_VALUE = 0x1
    
    # Default parameter values
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
        """Get the modulator type identifier.
        
        Returns:
            int: The ADSR envelope type value (1)
        """
        return self.TYPE_VALUE  # ADSR envelope type

class M8DrumEnvelope(M8ModulatorBase):
    """Drum envelope modulator specialized for percussive sounds.
    
    A three-stage envelope optimized for percussive/drum sounds with
    peak, body, and decay parameters for shaping the attack and body
    characteristics of drum sounds.
    """
    # Constants for Drum envelope
    TYPE_VALUE = 0x2
    
    # Default parameter values
    DEFAULT_PEAK = 0x0
    DEFAULT_BODY = 0x10
    DEFAULT_DECAY = 0x80
    
    _param_defs = [
        ("peak", DEFAULT_PEAK),
        ("body", DEFAULT_BODY),
        ("decay", DEFAULT_DECAY)
    ]
    
    def _get_type(self):
        """Get the modulator type identifier.
        
        Returns:
            int: The Drum envelope type value (2)
        """
        return self.TYPE_VALUE  # Drum envelope type
    
class M8LFO(M8ModulatorBase):
    """Low Frequency Oscillator (LFO) modulator.
    
    A periodic waveform generator for creating cyclic modulation.
    Can be used to create vibrato, tremolo, filter sweeps, and other
    time-varying effects.
    """
    # Constants for LFO
    TYPE_VALUE = 0x3
    
    # Default parameter values
    DEFAULT_OSCILLATOR = 0x0
    DEFAULT_TRIGGER = 0x0
    DEFAULT_FREQUENCY = 0x10
    
    _param_defs = [
        ("oscillator", DEFAULT_OSCILLATOR),
        ("trigger", DEFAULT_TRIGGER),
        ("frequency", DEFAULT_FREQUENCY)
    ]
    
    def _get_type(self):
        """Get the modulator type identifier.
        
        Returns:
            int: The LFO type value (3)
        """
        return self.TYPE_VALUE  # LFO type

class M8TriggerEnvelope(M8ModulatorBase):
    """Trigger envelope modulator that responds to external triggers.
    
    An envelope that can be triggered by various sources within the M8.
    Includes attack, hold, and decay stages similar to AHD, but with
    an additional source parameter to specify the trigger source.
    """
    # Constants for Trigger envelope
    TYPE_VALUE = 0x4
    
    # Default parameter values
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
        """Get the modulator type identifier.
        
        Returns:
            int: The Trigger envelope type value (4)
        """
        return self.TYPE_VALUE  # Trigger envelope type

class M8TrackingEnvelope(M8ModulatorBase):
    """Tracking envelope that maps input values to output modulation.
    
    Creates a modulation relationship that tracks an input source,
    mapping it to an output range defined by low_value and high_value.
    Useful for keyboard tracking and other parameter mapping tasks.
    """
    # Constants for Tracking envelope
    TYPE_VALUE = 0x5
    
    # Default parameter values
    DEFAULT_SOURCE = 0x0
    DEFAULT_LOW_VALUE = 0x0
    DEFAULT_HIGH_VALUE = 0x7F
    
    _param_defs = [
        ("source", DEFAULT_SOURCE),
        ("low_value", DEFAULT_LOW_VALUE),
        ("high_value", DEFAULT_HIGH_VALUE)
    ]
    
    def _get_type(self):
        """Get the modulator type identifier.
        
        Returns:
            int: The Tracking envelope type value (5)
        """
        return self.TYPE_VALUE  # Tracking envelope type
    
class M8Modulators(list):
    """A collection of modulators for an M8 instrument.
    
    Acts as a list of modulators with M8-specific serialization/deserialization
    and type-aware handling. Each M8 instrument can have multiple modulators
    to affect various parameters.
    """
    
    def __init__(self, items=None):
        """Initialize a collection of modulators.
        
        Args:
            items: Optional list of modulators to initialize with
        """
        super().__init__()
        items = items or []
        
        for item in items:
            self.append(item)
            
        while len(self) < BLOCK_COUNT:
            self.append(M8Block())
    
    @classmethod
    def read(cls, data):
        """Create a modulators collection from binary data.
        
        Args:
            data: Binary data containing multiple modulator blocks
            
        Returns:
            M8Modulators: New collection with modulators initialized from the data
        """
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
        """Create a deep copy of this modulators collection.
        
        Returns:
            M8Modulators: New collection with cloned modulators
        """
        instance = self.__class__()
        instance.clear()
        
        for mod in self:
            if hasattr(mod, 'clone'):
                instance.append(mod.clone())
            else:
                instance.append(mod)
        
        return instance
    
    def write(self):
        """Convert all modulators to binary data.
        
        Returns:
            bytes: Binary representation of all modulators
        """
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
        """Convert modulators to list for serialization.
        
        Only includes non-empty modulators with their position indices.
        
        Returns:
            list: List of dictionaries representing modulators
        """
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
        """Create modulators from a list of dictionaries.
        
        Args:
            items: List of dictionaries with modulator parameters
            
        Returns:
            M8Modulators: New collection with modulators at their specified positions
        """
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
    """Create a list of default modulators.
    
    Creates modulators according to the default configuration
    (typically 2 AHD envelopes and 2 LFOs).
    
    Returns:
        list: List of default modulator instances
    """
    result = []
    
    for mod_type in DEFAULT_MODULATOR_CONFIGS:
        if mod_type in MODULATOR_TYPES:
            full_path = MODULATOR_TYPES[mod_type]
            ModClass = load_class(full_path)
            result.append(ModClass())
        else:
            result.append(M8Block())
    return result
