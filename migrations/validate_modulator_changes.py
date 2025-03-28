#!/usr/bin/env python3
"""
Script to validate that the M8ModulatorType enum is properly working as the source of truth.
"""

import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from m8.config import get_modulator_types, get_modulator_type_id, get_modulator_type_id_map
from m8.enums import M8ModulatorType

def validate_modulator_type_id_map():
    """Validate that get_modulator_type_id_map returns correct class paths."""
    id_map = get_modulator_type_id_map()
    
    # Check that all enum values have corresponding class paths
    for member in M8ModulatorType:
        type_id = member.value
        type_name = member.name
        expected_class_path = f"m8.api.modulators.M8{type_name.title().replace('_', '')}"
        
        if type_id not in id_map:
            print(f"ERROR: Type ID {type_id} ({type_name}) not found in id_map!")
            return False
            
        if id_map[type_id] != expected_class_path:
            print(f"ERROR: Incorrect class path for {type_name}!")
            print(f"  Expected: {expected_class_path}")
            print(f"  Got:      {id_map[type_id]}")
            return False
    
    print("✓ modulator_type_id_map returns correct class paths")
    return True

def validate_modulator_types():
    """Validate that get_modulator_types returns a mapping consistent with the enum."""
    enum_map = {member.value: member.name for member in M8ModulatorType}
    config_map = get_modulator_types()
    
    if enum_map != config_map:
        print("ERROR: Enum map and config map don't match!")
        print(f"  Enum map:   {enum_map}")
        print(f"  Config map: {config_map}")
        return False
        
    print("✓ modulator_types matches enum values")
    return True

def validate_type_id_lookup():
    """Validate that get_modulator_type_id correctly looks up from the enum."""
    for member in M8ModulatorType:
        type_id = member.value
        type_name = member.name
        
        # Test lookup by name
        if get_modulator_type_id(type_name) != type_id:
            print(f"ERROR: Type ID lookup failed for {type_name}!")
            return False
            
        # Test lookup by existing ID (should return the same value)
        if get_modulator_type_id(type_id) != type_id:
            print(f"ERROR: Type ID passthrough failed for {type_id}!")
            return False
    
    print("✓ type_id lookup works correctly for all types")
    return True

def main():
    """Run all validation checks."""
    print("Validating M8ModulatorType as source of truth...")
    
    success = True
    success = validate_modulator_type_id_map() and success
    success = validate_modulator_types() and success
    success = validate_type_id_lookup() and success
    
    if success:
        print("\nValidation PASSED - M8ModulatorType is correctly functioning as the source of truth!")
        return 0
    else:
        print("\nValidation FAILED - See errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())