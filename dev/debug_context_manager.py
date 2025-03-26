#!/usr/bin/env python
"""Debug script to investigate instrument context manager serialization issues."""

import sys
import os
import yaml
import importlib
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from m8.api.instruments import M8Instrument
from m8.api.utils.enums import M8InstrumentContext
from m8.api.modulators import M8Modulator
from m8.config import get_modulator_type_field_def
from m8.api.utils.enums import get_enum_paths_for_instrument, load_enum_classes, serialize_param_enum_value

def debug_context_manager(file_path):
    """Load an instrument file and debug context manager behavior."""
    print(f"Loading instrument from {file_path}")
    
    # Load the instrument
    instrument = M8Instrument.read_from_file(file_path)
    print(f"Instrument type: {instrument.instrument_type}")
    
    # Get the context manager
    context = M8InstrumentContext.get_instance()
    print(f"Initial context state: instrument_type={context.current_instrument_type}")
    
    # Debug serialization with explicit context
    print("\n=== Using explicit context ===")
    with context.with_instrument(instrument_type=instrument.instrument_type):
        print(f"Context during block: instrument_type={context.current_instrument_type}")
        
        # Loop through non-empty modulators
        for i, mod in enumerate(instrument.modulators):
            if hasattr(mod, 'is_empty') and mod.is_empty():
                continue
                
            print(f"\nModulator {i}:")
            print(f"  Raw destination value: {mod.destination}")
            print(f"  Raw instrument_type: {mod.instrument_type}")
            
            # Debug field definition and enum paths
            field_def = get_modulator_type_field_def(mod.modulator_type, "destination")
            print(f"  Field definition: {field_def}")
            if field_def and "enums" in field_def:
                enum_paths = get_enum_paths_for_instrument(field_def["enums"], mod.instrument_type)
                print(f"  Enum paths: {enum_paths}")
                enum_classes = load_enum_classes(enum_paths)
                print(f"  Enum classes: {enum_classes}")
                
                # Manual test of serialization function
                serialized = serialize_param_enum_value(
                    mod.destination, 
                    field_def, 
                    mod.instrument_type, 
                    "destination"
                )
                print(f"  Manual serialization: {serialized}")
            
            # Test serialization inside context block
            mod_dict = mod.as_dict()
            print(f"  Serialized (inside context): {mod_dict['destination']}")
    
    # Debug serialization without context
    print("\n=== Without context ===")
    context.clear()  # Clear the context
    print(f"Context after clear: instrument_type={context.current_instrument_type}")
    
    for i, mod in enumerate(instrument.modulators):
        if hasattr(mod, 'is_empty') and mod.is_empty():
            continue
            
        print(f"\nModulator {i}:")
        print(f"  Raw destination value: {mod.destination}")
        print(f"  Raw instrument_type: {mod.instrument_type}")
        
        # Debug field definition and enum paths
        field_def = get_modulator_type_field_def(mod.modulator_type, "destination")
        print(f"  Field definition: {field_def}")
        if field_def and "enums" in field_def:
            enum_paths = get_enum_paths_for_instrument(field_def["enums"], mod.instrument_type)
            print(f"  Enum paths: {enum_paths}")
            enum_classes = load_enum_classes(enum_paths)
            print(f"  Enum classes: {enum_classes}")
        
        # Test serialization outside context block
        mod_dict = mod.as_dict()
        print(f"  Serialized (outside context): {mod_dict['destination']}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_context_manager.py <instrument_file>")
        sys.exit(1)
        
    debug_context_manager(sys.argv[1])