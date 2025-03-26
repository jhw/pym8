#!/usr/bin/env python
"""Fix script for modulator destination serialization issues.

This script demonstrates the issue with the current context manager implementation
and shows how to fix it to properly serialize instrument-dependent enum values.
"""

import sys
import os
import yaml
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from m8.api.instruments import M8Instrument
from m8.api.utils.context import M8InstrumentContext
from m8.api.modulators import M8Modulator
from m8.config import get_modulator_type_field_def
from m8.api.utils.enums import get_enum_paths_for_instrument, load_enum_classes, serialize_param_enum_value

def map_instrument_type_to_id(instrument_type):
    """Map instrument type string to numeric ID for enum lookup."""
    mapping = {
        "WAVSYNTH": "0x00",
        "MACROSYNTH": "0x01",
        "SAMPLER": "0x02"
    }
    return mapping.get(instrument_type)

def fix_get_enum_paths_for_instrument(enum_paths, instrument_type):
    """Fixed version of get_enum_paths_for_instrument that properly handles string instrument types."""
    if not isinstance(enum_paths, dict) or instrument_type is None:
        return enum_paths
    
    # Additional handling for string instrument types
    if isinstance(instrument_type, str):
        # Direct lookup by upper case string
        if instrument_type.upper() in enum_paths:
            return enum_paths.get(instrument_type.upper())
        
        # Try mapping the instrument type string to its ID
        instrument_id = map_instrument_type_to_id(instrument_type)
        if instrument_id in enum_paths:
            return enum_paths.get(instrument_id)
    
    # Original implementation for other cases
    lookup_key = str(instrument_type)
    
    # Direct string lookup
    if lookup_key in enum_paths:
        return enum_paths.get(lookup_key)
    
    # Try numeric conversion if possible
    if lookup_key and lookup_key.isdigit():
        # Try the numeric value directly
        numeric_key = int(lookup_key)
        if numeric_key in enum_paths:
            return enum_paths.get(numeric_key)
        
        # Try hex format of the numeric value
        hex_key = f"0x{numeric_key:02x}"
        if hex_key in enum_paths:
            return enum_paths.get(hex_key)
    
    return None

def test_serialization_fix(file_path):
    """Test the fixed serialization with an instrument file."""
    print(f"Loading instrument from {file_path}")
    
    # Load the instrument
    instrument = M8Instrument.read_from_file(file_path)
    print(f"Instrument type: {instrument.instrument_type}")
    
    # Test with each non-empty modulator
    for i, mod in enumerate(instrument.modulators):
        if hasattr(mod, 'is_empty') and mod.is_empty():
            continue
            
        print(f"\nModulator {i}:")
        print(f"  Raw destination value: {mod.destination}")
        print(f"  Raw instrument_type: {mod.instrument_type}")
        
        # Get field definition for modulator destination
        field_def = get_modulator_type_field_def(mod.modulator_type, "destination")
        if field_def and "enums" in field_def:
            print("  Using original function:")
            enum_paths = get_enum_paths_for_instrument(field_def["enums"], mod.instrument_type)
            print(f"  - Enum paths: {enum_paths}")
            
            print("  Using fixed function:")
            enum_paths_fixed = fix_get_enum_paths_for_instrument(field_def["enums"], mod.instrument_type)
            print(f"  - Enum paths: {enum_paths_fixed}")
            
            if enum_paths_fixed:
                enum_classes = load_enum_classes(enum_paths_fixed)
                print(f"  - Enum classes: {enum_classes}")
                
                for enum_class in enum_classes:
                    try:
                        # Try to convert the numeric value to enum name
                        enum_name = enum_class(mod.destination).name
                        print(f"  - Converted to: {enum_name}")
                    except ValueError:
                        print(f"  - Value {mod.destination} not found in {enum_class}")

def apply_fix():
    """Print instructions for applying the fix."""
    print("\n=== How to fix the issue ===")
    print("1. Modify the get_enum_paths_for_instrument function in m8/api/utils/enums.py to add handling for string instrument types")
    print("2. Add a map_instrument_type_to_id helper function or integrate it directly into get_enum_paths_for_instrument")
    print("3. Make sure the fix checks both uppercase and lowercase string instrument types")
    print("4. Update tests to verify proper enum serialization")
    
    print("\nSample implementation:")
    print('''
def get_enum_paths_for_instrument(enum_paths, instrument_type):
    """Get enum paths specific to an instrument type."""
    if not isinstance(enum_paths, dict) or instrument_type is None:
        return enum_paths
    
    # Create a lookup key from the instrument_type
    lookup_key = None
    
    # Handle IntEnum or any type with a .value attribute
    if hasattr(instrument_type, 'value'):
        # Try direct value as a key first
        if instrument_type.value in enum_paths:
            return enum_paths.get(instrument_type.value)
            
        # Try hex format
        hex_key = f"0x{instrument_type.value:02x}"
        if hex_key in enum_paths:
            return enum_paths.get(hex_key)
            
        # For IntEnum, also try name as a fallback
        if hasattr(instrument_type, 'name') and instrument_type.name in enum_paths:
            return enum_paths.get(instrument_type.name)
            
        # Use the string value for remaining lookups
        lookup_key = str(instrument_type)
    else:
        # Non-enum type, use string representation
        lookup_key = str(instrument_type)
    
    # Direct string lookup
    if lookup_key in enum_paths:
        return enum_paths.get(lookup_key)
    
    # Additional handling for string instrument types
    instrument_id_map = {
        "WAVSYNTH": "0x00",
        "MACROSYNTH": "0x01", 
        "SAMPLER": "0x02"
    }
    
    if lookup_key in instrument_id_map:
        mapped_id = instrument_id_map[lookup_key]
        if mapped_id in enum_paths:
            return enum_paths.get(mapped_id)
    
    # Try uppercase version
    if lookup_key and lookup_key.upper() in instrument_id_map:
        mapped_id = instrument_id_map[lookup_key.upper()]
        if mapped_id in enum_paths:
            return enum_paths.get(mapped_id)
    
    # Try numeric conversion if possible
    if lookup_key and lookup_key.isdigit():
        # Try the numeric value directly
        numeric_key = int(lookup_key)
        if numeric_key in enum_paths:
            return enum_paths.get(numeric_key)
            
        # Try hex format of the numeric value
        hex_key = f"0x{numeric_key:02x}"
        if hex_key in enum_paths:
            return enum_paths.get(hex_key)
    
    # No enum paths found for this instrument type
    return None
''')

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fix_modulator_serialization.py <instrument_file>")
        sys.exit(1)
        
    test_serialization_fix(sys.argv[1])
    apply_fix()