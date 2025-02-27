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
    # Add other instrument types and their modulators here
}

# Default modulator types: 2 envelopes followed by 2 LFOs
DEFAULT_MODULATORS = [0x00, 0x00, 0x03, 0x03]

class M8ModulatorsBase(list):
    """Base class for all modulator collections."""
    
    def __init__(self, items=None):
        super().__init__()
        items = items or []
        
        # Fill with provided items
        for item in items:
            self.append(item)
            
        # Fill remaining slots with empty blocks
        while len(self) < BLOCK_COUNT:
            self.append(M8Block())
    
    @classmethod
    def read(cls, data):
        """Base read method, should be overridden by subclasses."""
        instance = cls.__new__(cls)
        list.__init__(instance)
        
        for i in range(BLOCK_COUNT):
            start = i * BLOCK_SIZE
            block_data = data[start:start + BLOCK_SIZE]
            instance.append(M8Block.read(block_data))
        
        return instance
    
    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        list.__init__(instance)
        
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
        # Only include non-empty modulators
        items = []
        for i, mod in enumerate(self):
            if not (isinstance(mod, M8Block) or (hasattr(mod, 'is_empty') and mod.is_empty())):
                item_dict = mod.as_dict() if hasattr(mod, 'as_dict') else {"__class__": "m8.M8Block"}
                items.append(item_dict)
        
        return {
            "items": items
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create modulators from a dictionary - should be overridden by subclasses."""
        instance = cls()
        return instance


class M8MacroSynthModulators(M8ModulatorsBase):
    """Modulators collection specific to MacroSynth instruments."""
    
    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)
        list.__init__(instance)
        
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
            
            if mod_type in MODULATOR_TYPES[0x01]:  # 0x01 is MacroSynth
                # Create the specific modulator class
                ModClass = load_class(MODULATOR_TYPES[0x01][mod_type])
                instance.append(ModClass.read(block_data))
            else:
                # Default to M8Block for unknown types
                instance.append(M8Block.read(block_data))
        
        return instance
    
    @classmethod
    def from_dict(cls, data):
        """Create modulators from a dictionary"""
        instance = cls()
        
        # Set modulators
        if "items" in data:
            for i, mod_data in enumerate(data["items"]):
                if i < BLOCK_COUNT:
                    if "__class__" in mod_data:
                        try:
                            # Try to get class from the class path
                            class_path = mod_data["__class__"]
                            ModClass = load_class(class_path)
                            instance[i] = ModClass.from_dict(mod_data)
                        except (ImportError, AttributeError):
                            # Fall back to M8Block
                            instance[i] = M8Block()
                    else:
                        # Default to M8Block if no class info
                        instance[i] = M8Block()
        
        return instance


# Add more modulator subclasses for other instrument types here
# Example:
# class M8WaveSynthModulators(M8ModulatorsBase):
#     ...


def get_default_modulator_set(instrument_type):
    """Get the list of default modulator classes for an instrument type"""
    if instrument_type not in MODULATOR_TYPES:
        raise ValueError(f"Unknown instrument type: {instrument_type}")
        
    result = []
    for mod_type in DEFAULT_MODULATORS:
        # Get class path from MODULATOR_TYPES and instantiate
        if mod_type in MODULATOR_TYPES[instrument_type]:
            full_path = MODULATOR_TYPES[instrument_type][mod_type]
            ModClass = load_class(full_path)
            result.append(ModClass())
        else:
            result.append(M8Block())
        
    return result


def create_default_modulators(instrument_type):
    """Create default modulator instances for an instrument type"""
    return get_default_modulator_set(instrument_type)


def get_modulators_class_for_instrument(instrument_type):
    """Returns the appropriate modulators class for an instrument type"""
    if instrument_type == 0x01:  # MacroSynth
        return M8MacroSynthModulators
    # Add more instrument types here
    # elif instrument_type == 0x02:  # WaveSynth
    #     return M8WaveSynthModulators
    
    # Default to base class if no specific class is found
    return M8ModulatorsBase


# Alias for backward compatibility
create_modulators_class = get_modulators_class_for_instrument


def create_modulator_from_dict(data, instrument_type):
    """Create a modulator instance from a dictionary based on its type"""
    if not data or "type" not in data or instrument_type not in MODULATOR_TYPES:
        return None
    
    mod_type = data["type"]
    
    # If we have explicit class information, use that
    if "__class__" in data:
        try:
            ModClass = load_class(data["__class__"])
            return ModClass.from_dict(data)
        except (ImportError, AttributeError):
            pass
    
    # Fall back to type lookup
    if mod_type in MODULATOR_TYPES[instrument_type]:
        class_path = MODULATOR_TYPES[instrument_type][mod_type]
        ModClass = load_class(class_path)
        return ModClass.from_dict(data)
    
    return None


def get_modulator_type_from_class(mod_class):
    """Get the modulator type value from its class"""
    for instr_type, mod_types in MODULATOR_TYPES.items():
        for mod_type, class_path in mod_types.items():
            if class_path == f"{mod_class.__module__}.{mod_class.__name__}":
                return mod_type
    return None
