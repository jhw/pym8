from m8 import M8Block
from m8.api import load_class
from m8.core.list import m8_list_class
from m8.utils.bits import split_byte

import struct

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

def get_default_modulator_set(instrument_type):
    """Get the list of default modulator classes for an instrument type"""
    if instrument_type not in MODULATOR_TYPES:
        raise ValueError(f"Unknown instrument type: {instrument_type}")
        
    result = []
    for mod_type in DEFAULT_MODULATORS:
        # Get class path from MODULATOR_TYPES and instantiate
        full_path = MODULATOR_TYPES[instrument_type][mod_type]
        ModClass = load_class(full_path)
        result.append(ModClass())
        
    return result

def create_default_modulators(instrument_type):
    """Create default modulator instances for an instrument type"""
    return get_default_modulator_set(instrument_type)

def create_modulator_row_class_resolver(instrument_type):
    """Factory function to create a row class resolver based on instrument type"""
    if instrument_type not in MODULATOR_TYPES:
        raise ValueError(f"Unknown instrument type: {instrument_type}")
        
    def resolver(data):
        first_byte = struct.unpack("B", data[:1])[0]
        mod_type, _ = split_byte(first_byte)
        
        if mod_type in MODULATOR_TYPES[instrument_type]:
            class_path = MODULATOR_TYPES[instrument_type][mod_type]
            return load_class(class_path)
        else:
            return M8Block

    return resolver

def create_modulators_class(instrument_type):
    """Factory function to create an M8Modulators class based on instrument type"""
    row_class_resolver = create_modulator_row_class_resolver(instrument_type)
    
    M8Modulators = m8_list_class(
        row_size=BLOCK_SIZE,
        row_count=BLOCK_COUNT,
        row_class_resolver=row_class_resolver
    )
    
    return M8Modulators

def create_modulator_from_dict(data, instrument_type):
    """Create a modulator instance from a dictionary based on its type"""
    if not data or "type" not in data or instrument_type not in MODULATOR_TYPES:
        return None
    
    mod_type = data["type"]
    
    # If we have explicit class information, use that
    if "__class__" in data:
        try:
            ModClass = _get_class_from_string(data["__class__"])
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
