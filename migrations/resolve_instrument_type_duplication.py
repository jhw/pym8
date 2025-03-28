#!/usr/bin/env python3
"""
Migration script to eliminate duplication between the instrument type definitions
in m8/enums/__init__.py (M8InstrumentType) and the type_id_map in format_config.yaml.

This script modifies the config.py module to generate the type_id_map dynamically from
the M8InstrumentType enum rather than maintaining two separate definitions.
"""

import os
import sys
import yaml
import re

# Add the parent directory to sys.path so we can import the m8 package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from m8.enums import M8InstrumentType

def update_config_py():
    """Update config.py to generate the type_id_map from the M8InstrumentType enum."""
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'm8', 'config.py'))
    
    with open(config_path, 'r') as f:
        content = f.read()

    # Add import for M8InstrumentType if it's not already there
    if 'from m8.enums import M8InstrumentType' not in content:
        import_statement = 'from m8.enums import M8InstrumentType\n'
        
        # Add after the existing imports
        if 'import yaml' in content:
            content = content.replace('import yaml', 'import yaml\nfrom m8.enums import M8InstrumentType')
        else:
            # Fallback: add at the top
            content = import_statement + content

    # Add a new function to generate the type_id_map from the enum
    if 'def generate_instrument_type_id_map():' not in content:
        new_function = """
def generate_instrument_type_id_map():
    # Generates the instrument type_id_map from the M8InstrumentType enum
    return {member.value: member.name for member in M8InstrumentType}
"""
        # Add after the last function
        content += new_function
    
    # Modify the get_instrument_types function to use the enum
    get_instrument_types_pattern = r'def get_instrument_types\(\):\s*"""[^"]*"""\s*config = load_format_config\(\)\s*result = \{\}.*?return result'
    new_get_instrument_types = """def get_instrument_types():
    # Returns a dictionary of instrument type IDs to type names from configuration
    # Generate directly from the enum for a single source of truth
    return {member.value: member.name for member in M8InstrumentType}"""
    
    # Use re.DOTALL to match across multiple lines
    content = re.sub(get_instrument_types_pattern, new_get_instrument_types, content, flags=re.DOTALL)
    
    with open(config_path, 'w') as f:
        f.write(content)
    
    print(f"✓ Updated {config_path}")

def remove_type_id_map_from_yaml():
    """Remove the type_id_map entry from format_config.yaml."""
    yaml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'm8', 'format_config.yaml'))
    
    with open(yaml_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Remove the type_id_map if it exists
    if 'instruments' in config and 'type_id_map' in config['instruments']:
        del config['instruments']['type_id_map']
        
        # Write back the updated config
        with open(yaml_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=True)
        
        print(f"✓ Removed type_id_map from {yaml_path}")
    else:
        print("ℹ type_id_map not found in format_config.yaml")

def add_comment_to_enums_init():
    """Add a comment to m8/enums/__init__.py to indicate it's the source of truth."""
    enums_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'm8', 'enums', '__init__.py'))
    
    with open(enums_path, 'r') as f:
        content = f.read()
    
    # Find the M8InstrumentType class definition
    instrument_type_pattern = r'class M8InstrumentType\(IntEnum\):'
    comment = """class M8InstrumentType(IntEnum):
    # Instrument types in the M8 tracker.
    # 
    # This enum is the single source of truth for instrument type IDs and is used
    # to generate the instrument type mappings used throughout the codebase."""
    
    content = re.sub(instrument_type_pattern, comment, content)
    
    with open(enums_path, 'w') as f:
        f.write(content)
    
    print(f"✓ Added source of truth comment to {enums_path}")

def update_get_instrument_type_id():
    """Update the get_instrument_type_id function to use the enum directly."""
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'm8', 'config.py'))
    
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Find the get_instrument_type_id function
    get_instrument_type_id_pattern = r'def get_instrument_type_id\(instrument_type\):.*?raise ValueError\(f"Type ID for instrument \'{instrument_type}\' not found in configuration"\)'
    
    new_get_instrument_type_id = """def get_instrument_type_id(instrument_type):
    # Retrieves type ID for an instrument from M8InstrumentType enum or config
    # If it's None, return None
    if instrument_type is None:
        return None
        
    # If it's already an integer, just return it
    if isinstance(instrument_type, int):
        return instrument_type
        
    # Try to get from the enum if it's a string
    if isinstance(instrument_type, str):
        # First check if it's a name in the M8InstrumentType enum
        try:
            return M8InstrumentType[instrument_type].value
        except KeyError:
            pass
            
        # If not in enum, look in config as fallback
        config = load_format_config()
        
        # Use the type as provided without case conversion
        if ('instruments' in config and 'types' in config['instruments'] and 
            instrument_type in config['instruments']['types']):
            type_id = config['instruments']['types'][instrument_type]['type_id']
            if isinstance(type_id, str) and type_id.startswith('0x'):
                return int(type_id, 16)
            return type_id
    
    raise ValueError(f"Type ID for instrument '{instrument_type}' not found in enum or configuration")"""
    
    # Use re.DOTALL to match across multiple lines
    content = re.sub(get_instrument_type_id_pattern, new_get_instrument_type_id, content, flags=re.DOTALL)
    
    with open(config_path, 'w') as f:
        f.write(content)
    
    print(f"✓ Updated get_instrument_type_id function in {config_path}")

def validate_changes():
    """Validate that the changes work correctly."""
    try:
        # Try importing the updated modules
        from m8.config import get_instrument_types
        from m8.enums import M8InstrumentType
        
        # Check that they produce the same mapping
        enum_map = {member.value: member.name for member in M8InstrumentType}
        config_map = get_instrument_types()
        
        assert enum_map == config_map, "Enum and config maps don't match"
        
        print("✓ Validation successful: enum and config maps match")
        return True
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return False

def main():
    print("Starting migration to resolve instrument type duplication...")
    
    # Update the code
    update_config_py()
    remove_type_id_map_from_yaml()
    add_comment_to_enums_init()
    update_get_instrument_type_id()
    
    # Validate the changes
    if validate_changes():
        print("\nMigration completed successfully!")
        print("The M8InstrumentType enum in m8/enums/__init__.py is now the single source of truth for instrument types.")
    else:
        print("\nMigration FAILED - please check the errors above.")

if __name__ == "__main__":
    main()