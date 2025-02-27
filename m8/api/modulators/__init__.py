from m8 import M8Block
from m8.api import load_class
from m8.utils.bits import split_byte

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
        # Include all modulators, even empty ones
        return [mod.as_dict() if hasattr(mod, "as_dict") else {"data": []} for mod in self]
    
    @classmethod
    def from_dict(cls, data, instrument_type=0x01):
        """Create modulators from a dictionary."""
        instance = cls(instrument_type=instrument_type)
        instance.clear()  # Clear default items
        
        # Set modulators
        for i, mod_data in enumerate(data):
            if i < BLOCK_COUNT:
                if isinstance(mod_data, dict) and "type" in mod_data:
                    mod_type = mod_data["type"]
                    if instrument_type in MODULATOR_TYPES and mod_type in MODULATOR_TYPES[instrument_type]:
                        ModClass = load_class(MODULATOR_TYPES[instrument_type][mod_type])
                        instance.append(ModClass.from_dict(mod_data))
                    else:
                        instance.append(M8Block())
                else:
                    instance.append(M8Block())
        
        # Fill remaining slots with empty blocks
        while len(instance) < BLOCK_COUNT:
            instance.append(M8Block())
            
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
