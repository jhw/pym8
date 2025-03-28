#!/usr/bin/env python3
"""
Script to validate consistency between enum definitions and format_config.yaml.

This script checks for:
1. All instrument type IDs referenced in configuration match valid values from M8InstrumentType
2. All modulator type IDs referenced in configuration match valid values from M8ModulatorType
3. Consistency in instrument type references in modulator destinations and FX enums
"""

import os
import sys
import yaml

# Add the parent directory to sys.path so we can import the m8 package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from m8.enums import M8InstrumentType, M8ModulatorType
from m8.core.validation import M8ValidationResult

def load_config():
    """Load the format_config.yaml file."""
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'm8', 'format_config.yaml'))
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def validate_instrument_types(config, result):
    """Validate instrument type IDs in configuration."""
    valid_instrument_ids = {member.value for member in M8InstrumentType}
    
    # Check instrument types defined in YAML
    if 'instruments' in config and 'types' in config['instruments']:
        for instrument_type, instrument_config in config['instruments']['types'].items():
            if 'type_id' in instrument_config:
                type_id = instrument_config['type_id']
                
                # Convert hex strings to int if needed
                if isinstance(type_id, str) and type_id.startswith('0x'):
                    type_id = int(type_id, 16)
                
                if type_id not in valid_instrument_ids:
                    result.add_error(
                        f"Invalid instrument type ID: {type_id} for {instrument_type}",
                        "instruments.types"
                    )
    
    # Check FX enums mappings
    if 'fx' in config and 'fields' in config['fx'] and 'key' in config['fx']['fields'] and 'enums' in config['fx']['fields']['key']:
        fx_enums = config['fx']['fields']['key']['enums']
        for instrument_id_str in fx_enums:
            # Convert hex strings to int
            if instrument_id_str.startswith('0x'):
                instrument_id = int(instrument_id_str, 16)
            else:
                instrument_id = int(instrument_id_str)
                
            if instrument_id not in valid_instrument_ids:
                result.add_error(
                    f"Invalid instrument ID in FX enums mapping: {instrument_id_str}",
                    "fx.fields.key.enums"
                )
    
    # Check modulator destination enums
    if 'modulators' in config and 'types' in config['modulators']:
        for mod_type, mod_config in config['modulators']['types'].items():
            if 'fields' in mod_config and 'destination' in mod_config['fields'] and 'enums' in mod_config['fields']['destination']:
                dest_enums = mod_config['fields']['destination']['enums']
                for instrument_id_str in dest_enums:
                    # Convert hex strings to int
                    if instrument_id_str.startswith('0x'):
                        instrument_id = int(instrument_id_str, 16)
                    else:
                        instrument_id = int(instrument_id_str)
                        
                    if instrument_id not in valid_instrument_ids:
                        result.add_error(
                            f"Invalid instrument ID in modulator destination enums: {instrument_id_str}",
                            f"modulators.types.{mod_type}.fields.destination.enums"
                        )
    
    return result

def validate_modulator_types(config, result):
    """Validate modulator type IDs in configuration."""
    valid_modulator_ids = {member.value for member in M8ModulatorType}
    
    # Check modulator types defined in YAML
    if 'modulators' in config and 'types' in config['modulators']:
        for mod_type, mod_config in config['modulators']['types'].items():
            if 'id' in mod_config:
                type_id = mod_config['id']
                
                # Convert hex strings to int if needed
                if isinstance(type_id, str) and type_id.startswith('0x'):
                    type_id = int(type_id, 16)
                
                if type_id not in valid_modulator_ids:
                    result.add_error(
                        f"Invalid modulator type ID: {type_id} for {mod_type}",
                        "modulators.types"
                    )
    
    # Check default_config
    if 'modulators' in config and 'default_config' in config['modulators']:
        for i, mod_type_id in enumerate(config['modulators']['default_config']):
            if mod_type_id not in valid_modulator_ids:
                result.add_error(
                    f"Invalid modulator type ID in default_config[{i}]: {mod_type_id}",
                    "modulators.default_config"
                )
    
    return result

def validate_enum_references(config, result):
    """Validate enum references in configuration."""
    # Check that all enum references point to valid enum classes
    # This is a more complex validation that would require importing and checking
    # all referenced enum paths - we could add this later if needed
    
    return result

def main():
    """Validate consistency between enums and configuration."""
    print("Validating consistency between enums and format_config.yaml...")
    
    # Load the configuration
    config = load_config()
    
    # Create a validation result
    result = M8ValidationResult(context="format_config")
    
    # Validate instrument types
    result = validate_instrument_types(config, result)
    
    # Validate modulator types
    result = validate_modulator_types(config, result)
    
    # Validate enum references
    result = validate_enum_references(config, result)
    
    # Report results
    if result.valid:
        print("✅ Validation successful! Enums and configuration are consistent.")
        return 0
    else:
        print("❌ Validation failed!")
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")
        return 1

if __name__ == "__main__":
    sys.exit(main())