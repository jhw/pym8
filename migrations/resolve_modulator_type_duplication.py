#!/usr/bin/env python3
"""
Migration script to eliminate duplication between the modulator type definitions
in m8/enums/__init__.py (M8ModulatorType) and the type_id_map in format_config.yaml.

This script modifies the config.py module to generate the modulator type mappings dynamically 
from the M8ModulatorType enum rather than maintaining two separate definitions.
"""

import os
import sys
import yaml
import re

# Add the parent directory to sys.path so we can import the m8 package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from m8.enums import M8ModulatorType

def update_config_py():
    """Update config.py to generate modulator type mappings from the M8ModulatorType enum."""
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'm8', 'config.py'))
    
    with open(config_path, 'r') as f:
        content = f.read()

    # Add import for M8ModulatorType if it's not already imported alongside M8InstrumentType
    if 'from m8.enums import M8InstrumentType' in content and 'from m8.enums import M8InstrumentType, M8ModulatorType' not in content:
        content = content.replace('from m8.enums import M8InstrumentType', 'from m8.enums import M8InstrumentType, M8ModulatorType')
    
    # Add a new function to generate the modulator type_id_map from the enum
    if 'def generate_modulator_type_id_map():' not in content:
        new_function = """
def generate_modulator_type_id_map():
    # Generates the modulator type_id_map from the M8ModulatorType enum
    return {member.value: member.name for member in M8ModulatorType}
"""
        # Add after the generate_instrument_type_id_map function
        if 'def generate_instrument_type_id_map():' in content:
            content = content.replace('def generate_instrument_type_id_map():', 'def generate_instrument_type_id_map():' + new_function)
        else:
            # Fallback: add at the end
            content += new_function
    
    # Modify the get_modulator_types function to use the enum
    get_modulator_types_pattern = r'def get_modulator_types\(\):\s*"""[^"]*"""\s*config = load_format_config\(\)\s*result = \{\}.*?return result'
    new_get_modulator_types = """def get_modulator_types():
    # Returns a dictionary of modulator type IDs to type names
    # Generate directly from the enum for a single source of truth
    return {member.value: member.name for member in M8ModulatorType}"""
    
    # Use re.DOTALL to match across multiple lines
    content = re.sub(get_modulator_types_pattern, new_get_modulator_types, content, flags=re.DOTALL)
    
    # Update get_modulator_type_id function
    get_modulator_type_id_pattern = r'def get_modulator_type_id\(modulator_type\):.*?raise ValueError\(f"Type ID for modulator \'{modulator_type}\' not found in configuration"\)'
    new_get_modulator_type_id = """def get_modulator_type_id(modulator_type):
    # Retrieves type ID for a modulator from M8ModulatorType enum
    # If it's None, return None
    if modulator_type is None:
        return None
        
    # If it's already an integer, just return it
    if isinstance(modulator_type, int):
        return modulator_type
        
    # Try to get from the enum if it's a string
    if isinstance(modulator_type, str):
        # First check if it's a name in the M8ModulatorType enum
        try:
            return M8ModulatorType[modulator_type].value
        except KeyError:
            pass
            
        # If not in enum, look in config as fallback
        config = load_format_config()
        
        # Use the type as provided without case conversion
        if 'modulators' in config and 'types' in config['modulators'] and modulator_type in config['modulators']['types']:
            type_id = config['modulators']['types'][modulator_type]['id']
            if isinstance(type_id, str) and type_id.startswith('0x'):
                return int(type_id, 16)
            return type_id
    
    raise ValueError(f"Type ID for modulator '{modulator_type}' not found in enum or configuration")"""
    
    # Use re.DOTALL to match across multiple lines
    content = re.sub(get_modulator_type_id_pattern, new_get_modulator_type_id, content, flags=re.DOTALL)
    
    # Update get_modulator_type_id_map function
    get_modulator_type_id_map_pattern = r'def get_modulator_type_id_map\(\):.*?return id_map'
    new_get_modulator_type_id_map = """def get_modulator_type_id_map():
    # Provides a mapping of modulator type IDs to their class paths
    # Generate the mapping from the enum values
    enum_map = {member.value: member.name for member in M8ModulatorType}
    
    # Map the enum values to class paths
    # This maintains backward compatibility with code expecting class paths
    class_path_map = {}
    for type_id, type_name in enum_map.items():
        # Convert enum names to class paths (e.g., LFO -> m8.api.modulators.M8LFO)
        class_path_map[type_id] = f"m8.api.modulators.M8{type_name.title().replace('_', '')}"
    
    return class_path_map"""
    
    # Use re.DOTALL to match across multiple lines
    content = re.sub(get_modulator_type_id_map_pattern, new_get_modulator_type_id_map, content, flags=re.DOTALL)
    
    with open(config_path, 'w') as f:
        f.write(content)
    
    print(f"✓ Updated {config_path}")

def add_comment_to_modulator_enum():
    """Add a comment to M8ModulatorType in m8/enums/__init__.py to indicate it's the source of truth."""
    enums_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'm8', 'enums', '__init__.py'))
    
    with open(enums_path, 'r') as f:
        content = f.read()
    
    # Find the M8ModulatorType class definition
    modulator_type_pattern = r'class M8ModulatorType\(IntEnum\):'
    comment = """class M8ModulatorType(IntEnum):
    # Modulator types in the M8 tracker.
    # 
    # This enum is the single source of truth for modulator type IDs and is used
    # to generate the modulator type mappings used throughout the codebase."""
    
    content = re.sub(modulator_type_pattern, comment, content)
    
    with open(enums_path, 'w') as f:
        f.write(content)
    
    print(f"✓ Added source of truth comment to M8ModulatorType in {enums_path}")

def update_yaml_config():
    """Update the modulator 'id' fields in format_config.yaml to match the enum values."""
    yaml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'm8', 'format_config.yaml'))
    
    with open(yaml_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if 'modulators' in config and 'types' in config['modulators']:
        # Get the enum values to ensure consistency
        enum_values = {member.name: member.value for member in M8ModulatorType}
        
        # Update each modulator type's id to match the enum
        for mod_type_name, mod_config in config['modulators']['types'].items():
            # Find the corresponding enum name (case-insensitive match)
            for enum_name, enum_value in enum_values.items():
                if enum_name == mod_type_name:
                    mod_config['id'] = enum_value
                    break
        
        # Write back the updated config
        with open(yaml_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=True)
        
        print(f"✓ Updated modulator id fields in {yaml_path}")
    else:
        print("ℹ modulators.types not found in format_config.yaml")

def validate_changes():
    """Validate that the changes work correctly."""
    try:
        # Try importing the updated modules
        from m8.config import get_modulator_types, get_modulator_type_id
        from m8.enums import M8ModulatorType
        
        # Check that the mappings match
        enum_map = {member.value: member.name for member in M8ModulatorType}
        config_map = get_modulator_types()
        
        assert enum_map == config_map, "Enum and config maps don't match"
        
        # Check that all type_ids match
        for enum_member in M8ModulatorType:
            assert get_modulator_type_id(enum_member.name) == enum_member.value, f"Type ID mismatch for {enum_member.name}"
        
        print("✓ Validation successful: enum and config maps match")
        return True
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return False

def main():
    print("Starting migration to resolve modulator type duplication...")
    
    # Update the code
    update_config_py()
    add_comment_to_modulator_enum()
    update_yaml_config()
    
    # Validate the changes
    if validate_changes():
        print("\nMigration completed successfully!")
        print("The M8ModulatorType enum in m8/enums/__init__.py is now the single source of truth for modulator types.")
    else:
        print("\nMigration FAILED - please check the errors above.")

if __name__ == "__main__":
    main()