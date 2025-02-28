from m8 import M8Block
from m8.api import load_class
from m8.utils.bits import split_byte, join_nibbles

BLOCK_SIZE = 6
BLOCK_COUNT = 4

# Map instrument types to their modulator type paths
MODULATOR_TYPES = {
    0x01: {  # MacroSynth
        0x00: "m8.api.modulators.macrosynth.M8MacroSynthAHDEnvelope",
        0x01: "m8.api.modulators.macrosynth.M8MacroSynthADSREnvelope",
        0x03: "m8.api.modulators.macrosynth.M8MacroSynthLFO"
    }
    # Add other instrument types and their modulators here as needed
}

# Default modulator configurations per instrument type
DEFAULT_MODULATOR_CONFIGS = {
    0x01: [0x00, 0x00, 0x03, 0x03]  # MacroSynth: 2 AHD envelopes, 2 LFOs
    # Add more instrument types as needed
}

class M8ModulatorBase:
    """Base class for all M8 modulators across instrument types."""
    
    def __init__(self, **kwargs):
        # All modulators need type and destination
        self.type = 0x0
        self.destination = 0x0
        self.amount = 0xFF
        
        # Apply any provided kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def read(cls, data):
        """Generic read method to be overridden by subclasses."""
        instance = cls()
        
        # Common for all modulators: first byte contains type and destination
        if len(data) > 0:
            type_dest = data[0]
            instance.type, instance.destination = split_byte(type_dest)
            
            # Amount is also common to all modulators
            if len(data) > 1:
                instance.amount = data[1]
        
        return instance
    
    def write(self):
        """Generic write method to be overridden by subclasses."""
        buffer = bytearray()
        
        # Type/destination (combined into one byte)
        type_dest = join_nibbles(self.type, self.destination)
        buffer.append(type_dest)
        
        # Amount is common to all modulators
        buffer.append(self.amount)
        
        return bytes(buffer)
    
    def is_empty(self):
        """A modulator is considered empty if its destination is 0."""
        return self.destination == 0
    
    def clone(self):
        """Create a copy of this modulator."""
        instance = self.__class__()
        for key, value in vars(self).items():
            setattr(instance, key, value)
        return instance
    
    def as_dict(self):
        """Convert modulator to dictionary for serialization."""
        return {k: v for k, v in vars(self).items() if not k.startswith('_')}
    
    @classmethod
    def from_dict(cls, data):
        """Create a modulator from a dictionary."""
        instance = cls()
        
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        return instance

class M8Modulators(list):
    """Generic class for all modulator collections."""
    
    def __init__(self, instrument_type=0x01, items=None):
        super().__init__()
        self.instrument_type = instrument_type
        items = items or []
        
        # Fill with provided items
        for item in items:
            self.append(item)
            
        # Fill remaining slots with empty blocks
        while len(self) < BLOCK_COUNT:
            self.append(M8Block())
    
    @classmethod
    def read(cls, data, instrument_type=0x01):
        """Generic read method that handles any instrument type."""
        instance = cls(instrument_type=instrument_type)
        instance.clear()  # Clear default items
        
        for i in range(BLOCK_COUNT):
            start = i * BLOCK_SIZE
            block_data = data[start:start + BLOCK_SIZE]
            
            # Only process if we have enough data
            if len(block_data) < 1:
                instance.append(M8Block())
                continue
                
            # Check the modulator type/destination byte
            first_byte = block_data[0]
            mod_type, _ = split_byte(first_byte)
            
            if instrument_type in MODULATOR_TYPES and mod_type in MODULATOR_TYPES[instrument_type]:
                # Create the specific modulator class
                ModClass = load_class(MODULATOR_TYPES[instrument_type][mod_type])
                instance.append(ModClass.read(block_data))
            else:
                # Default to M8Block for unknown types
                instance.append(M8Block.read(block_data))
        
        return instance
    
    def clone(self):
        instance = self.__class__(instrument_type=self.instrument_type)
        instance.clear()  # Clear default items
        
        for mod in self:
            if hasattr(mod, 'clone'):
                instance.append(mod.clone())
            else:
                instance.append(mod)
        
        return instance
    
    def is_empty(self):
        return all(isinstance(mod, M8Block) or mod.is_empty() for mod in self)
    
    def write(self):
        result = bytearray()
        for mod in self:
            mod_data = mod.write() if hasattr(mod, 'write') else bytes([0] * BLOCK_SIZE)
            # Ensure each modulator occupies exactly BLOCK_SIZE bytes
            if len(mod_data) < BLOCK_SIZE:
                mod_data = mod_data + bytes([0x0] * (BLOCK_SIZE - len(mod_data)))
            elif len(mod_data) > BLOCK_SIZE:
                mod_data = mod_data[:BLOCK_SIZE]
            result.extend(mod_data)
        return bytes(result)
    
    def as_dict(self):
        """Convert modulators to dictionary for serialization"""
        # Include all modulators with their indexes
        items = []
        for i, mod in enumerate(self):
            if hasattr(mod, "as_dict"):
                mod_dict = mod.as_dict()
                # Add index field to track position
                mod_dict["index"] = i
                items.append(mod_dict)
            else:
                # For M8Block instances
                items.append({"index": i, "data": []})
        
        return items
    
    @classmethod
    def from_dict(cls, data, instrument_type=0x01):
        """Create modulators from a dictionary."""
        instance = cls(instrument_type=instrument_type)
        instance.clear()  # Clear default items
        
        # Initialize with empty blocks
        for _ in range(BLOCK_COUNT):
            instance.append(M8Block())
        
        # Set modulators at their original positions
        for mod_data in data:
            # Get index from data or default to 0
            index = mod_data.get("index", 0)
            if 0 <= index < BLOCK_COUNT:
                # If the modulator has type information, create appropriate instance
                if "type" in mod_data and instrument_type in MODULATOR_TYPES:
                    mod_type = mod_data["type"]
                    if mod_type in MODULATOR_TYPES[instrument_type]:
                        # Remove index field before passing to from_dict
                        mod_dict = {k: v for k, v in mod_data.items() if k != "index"}
                        ModClass = load_class(MODULATOR_TYPES[instrument_type][mod_type])
                        instance[index] = ModClass.from_dict(mod_dict)
                    else:
                        # Unknown modulator type
                        instance[index] = M8Block()
                else:
                    # No type information, assume empty block
                    instance[index] = M8Block()
        
        return instance
    

def create_default_modulators(instrument_type):
    """Create default modulator instances for an instrument type"""
    result = []
    
    if instrument_type not in MODULATOR_TYPES or instrument_type not in DEFAULT_MODULATOR_CONFIGS:
        # Return empty modulators if type is unknown
        return [M8Block() for _ in range(BLOCK_COUNT)]
    
    for mod_type in DEFAULT_MODULATOR_CONFIGS[instrument_type]:
        # Get class path from MODULATOR_TYPES and instantiate
        if mod_type in MODULATOR_TYPES[instrument_type]:
            full_path = MODULATOR_TYPES[instrument_type][mod_type]
            ModClass = load_class(full_path)
            result.append(ModClass())
        else:
            result.append(M8Block())
    
    return result
