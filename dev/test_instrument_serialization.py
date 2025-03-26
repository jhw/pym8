#!/usr/bin/env python
"""Test script for instrument serialization with our fixed enum handling."""

import sys
import os
import yaml

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from m8.api.instruments import M8Instrument

def test_instrument_serialization(file_path):
    """Test proper serialization of instrument modulators."""
    print(f"Loading instrument from {file_path}")
    
    # Check if it's an .m8s file (song) or .m8i file (instrument)
    if file_path.lower().endswith('.m8s'):
        print("Song file detected. Looking for instruments...")
        # For song files we'd need to extract instruments, which is more complex
        # Since we're just testing enum serialization, let's use a known instrument file
        test_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                'tests/api/instruments/fixtures/303.m8i')
        print(f"Using test instrument instead: {test_file}")
        instrument = M8Instrument.read_from_file(test_file)
    else:
        # Load the instrument
        instrument = M8Instrument.read_from_file(file_path)
    
    print(f"Instrument type: {instrument.instrument_type}")
    
    # Convert to dict and dump YAML
    instrument_dict = instrument.as_dict()
    yaml_output = yaml.dump(instrument_dict, default_flow_style=False, sort_keys=True)
    
    print("\nInstrument YAML representation:")
    print(yaml_output)
    
    # Check for modulator destinations in the YAML output
    have_modulators = False
    have_string_destinations = False
    
    for i, mod in enumerate(instrument.modulators):
        if hasattr(mod, 'is_empty') and mod.is_empty():
            continue
            
        have_modulators = True
        mod_dict = mod.as_dict()
        destination = mod_dict.get('destination')
        
        print(f"\nModulator {i}:")
        print(f"  Raw destination value: {mod.destination}")
        print(f"  Serialized destination: {destination}")
        
        if isinstance(destination, str) and not destination.isdigit():
            have_string_destinations = True
    
    if not have_modulators:
        print("\n⚠️ Warning: No non-empty modulators found to test serialization.")
    elif have_string_destinations:
        print("\n✅ Success: Modulator destinations are properly serialized to enum names!")
    else:
        print("\n❌ Error: Modulator destinations are not properly serialized to enum names.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_instrument_serialization.py <instrument_file>")
        sys.exit(1)
        
    test_instrument_serialization(sys.argv[1])