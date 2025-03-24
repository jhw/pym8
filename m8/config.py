import os
import yaml
from functools import lru_cache

@lru_cache(maxsize=1)
def load_format_config():
    """Loads M8 format configuration from YAML with caching to avoid disk reads."""
    config_path = os.path.join(os.path.dirname(__file__), 'format_config.yaml')
    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)
        
    # Apply defaults to field definitions
    config = _apply_field_defaults(config)
    return config

def _apply_field_defaults(config):
    """
    Apply default values to field definitions throughout the config.
    For any dictionary that appears to be a field definition (has 'offset'),
    adds default values if they're missing:
    - Default size: 1
    - Default type: "UINT8"
    - Default default: 0
    
    Also handles UINT4_2 fields with nibble components.
    """
    if not isinstance(config, dict):
        return config
        
    # Process all dictionary items recursively
    for key, value in config.items():
        if isinstance(value, dict):
            # Check if this looks like a field definition
            if 'offset' in value:
                if 'size' not in value:
                    value['size'] = 1
                
                # Handle special UINT4_2 type
                if 'type' in value and value['type'] == "UINT4_2":
                    # Process components if present
                    if 'components' in value:
                        for comp_name, comp_def in value['components'].items():
                            if 'default' not in comp_def:
                                comp_def['default'] = 0
                else:
                    # Regular field handling
                    if 'type' not in value:
                        value['type'] = "UINT8"
                    if 'default' not in value:
                        value['default'] = 0
            
            # Named collections of fields
            if key == 'fields' or key == 'params':
                for field_name, field_def in value.items():
                    if isinstance(field_def, dict) and 'offset' in field_def:
                        if 'size' not in field_def:
                            field_def['size'] = 1
                        
                        # Handle special UINT4_2 type
                        if 'type' in field_def and field_def['type'] == "UINT4_2":
                            # Process components if present
                            if 'components' in field_def:
                                for comp_name, comp_def in field_def['components'].items():
                                    if 'default' not in comp_def:
                                        comp_def['default'] = 0
                        else:
                            # Regular field handling
                            if 'type' not in field_def:
                                field_def['type'] = "UINT8"
                            if 'default' not in field_def:
                                field_def['default'] = 0
            
            # Recursively process nested dictionaries
            config[key] = _apply_field_defaults(value)
    
    return config

def get_offset(section_name):
    """Gets section offset from configuration."""
    config = load_format_config()
    if section_name in config and 'offset' in config[section_name]:
        offset_value = config[section_name]['offset']
        if isinstance(offset_value, str) and offset_value.startswith('0x'):
            return int(offset_value, 16)
        return offset_value
    raise ValueError(f"Offset for section '{section_name}' not found in configuration")

def get_count(section_name):
    """Gets count value for a section from configuration."""
    config = load_format_config()
    if section_name in config and 'count' in config[section_name]:
        return config[section_name]['count']
    raise ValueError(f"Count for section '{section_name}' not found in configuration")

def get_param_data(section_path, param_name):
    """Gets parameter data at the specified path."""
    config = load_format_config()
    current = config
    
    for part in section_path:
        if part in current:
            current = current[part]
        else:
            raise ValueError(f"Section '{part}' not found in configuration path {section_path}")
            
    if param_name in current:
        return current[param_name]
    raise ValueError(f"Parameter '{param_name}' not found in section {section_path}")

def get_param_type_enum(param_type_str):
    """Maps parameter type strings to their enum values."""
    config = load_format_config()
    if 'instruments' in config and 'param_types' in config['instruments']:
        param_types = config['instruments']['param_types']
        if param_type_str in param_types:
            return param_types[param_type_str]
    return 1  # Default to UINT8 value

def get_modulator_data(modulator_type):
    """Retrieves configuration data for a specific modulator type."""
    config = load_format_config()
    if 'modulators' in config and 'types' in config['modulators']:
        modulator_types = config['modulators']['types']
        
        # Try uppercase version first
        lookup_type = modulator_type.upper() if isinstance(modulator_type, str) else modulator_type
        if lookup_type in modulator_types:
            return modulator_types[lookup_type]
            
        # Try lowercase version as fallback
        lookup_type = modulator_type.lower() if isinstance(modulator_type, str) else modulator_type
        if lookup_type in modulator_types:
            return modulator_types[lookup_type]
            
        raise ValueError(f"Modulator type '{modulator_type}' not found in configuration")
    raise ValueError("Modulators section not found in configuration")

def get_modulator_type_id_map():
    """Provides a mapping of modulator type IDs to their class paths from configuration."""
    config = load_format_config()
    # Convert string keys to integers to handle hex strings
    id_map = {}
    for key_str, value in config["modulators"]["type_id_map"].items():
        # Convert hex string keys to integers
        if isinstance(key_str, str) and key_str.startswith("0x"):
            key = int(key_str, 16)
        else:
            key = int(key_str)
        id_map[key] = value
    return id_map

def get_modulator_types():
    """Returns a dictionary of modulator type IDs to type names from configuration."""
    config = load_format_config()
    result = {}
    
    for mod_type, mod_config in config['modulators']['types'].items():
        # Skip non-modulator sections
        if isinstance(mod_config, dict) and 'id' in mod_config:
            type_id = mod_config['id']
            # Convert hex strings to integers
            if isinstance(type_id, str) and type_id.startswith('0x'):
                type_id = int(type_id, 16)
            result[type_id] = mod_type.upper()
            
    return result

def get_modulator_type_id(modulator_type):
    """Retrieves type ID for a modulator from configuration."""
    # If it's already an integer, just return it
    if isinstance(modulator_type, int):
        return modulator_type
        
    # Handle string type names
    config = load_format_config()
    
    # Try uppercase version first
    lookup_type = modulator_type.upper() if isinstance(modulator_type, str) else modulator_type
    
    if 'modulators' in config and 'types' in config['modulators'] and lookup_type in config['modulators']['types']:
        type_id = config['modulators']['types'][lookup_type]['id']
        if isinstance(type_id, str) and type_id.startswith('0x'):
            return int(type_id, 16)
        return type_id
        
    # Try lowercase version as fallback
    lookup_type = modulator_type.lower() if isinstance(modulator_type, str) else modulator_type
    
    if 'modulators' in config and 'types' in config['modulators'] and lookup_type in config['modulators']['types']:
        type_id = config['modulators']['types'][lookup_type]['id']
        if isinstance(type_id, str) and type_id.startswith('0x'):
            return int(type_id, 16)
        return type_id
        
    raise ValueError(f"Type ID for modulator '{modulator_type}' not found in configuration")

def get_instrument_type_id(instrument_type):
    """Retrieves type ID for an instrument from configuration."""
    # If it's already an integer, just return it
    if isinstance(instrument_type, int):
        return instrument_type
        
    # Handle string type names
    config = load_format_config()
    
    # Try uppercase version first
    lookup_type = instrument_type.upper() if isinstance(instrument_type, str) else instrument_type
    
    if ('instruments' in config and 'types' in config['instruments'] and 
        lookup_type in config['instruments']['types']):
        type_id = config['instruments']['types'][lookup_type]['type_id']
        if isinstance(type_id, str) and type_id.startswith('0x'):
            return int(type_id, 16)
        return type_id
        
    # Try lowercase version as fallback
    lookup_type = instrument_type.lower() if isinstance(instrument_type, str) else instrument_type
    
    if ('instruments' in config and 'types' in config['instruments'] and 
        lookup_type in config['instruments']['types']):
        type_id = config['instruments']['types'][lookup_type]['type_id']
        if isinstance(type_id, str) and type_id.startswith('0x'):
            return int(type_id, 16)
        return type_id
        
    raise ValueError(f"Type ID for instrument '{instrument_type}' not found in configuration")

def get_instrument_modulators_offset(instrument_type=None):
    """Retrieves modulators offset for instruments from configuration."""
    config = load_format_config()
    if 'instruments' in config and 'modulators_offset' in config['instruments']:
        return config['instruments']['modulators_offset']
    raise ValueError("Modulators offset not found in instruments configuration")

def get_instrument_types():
    """Returns a dictionary of instrument type IDs to type names from configuration."""
    config = load_format_config()
    result = {}
    
    if 'instruments' in config and 'types' in config['instruments']:
        for instr_type, instr_config in config['instruments']['types'].items():
            # Skip non-instrument sections
            if isinstance(instr_config, dict) and 'type_id' in instr_config:
                type_id = instr_config['type_id']
                # Convert hex strings to integers
                if isinstance(type_id, str) and type_id.startswith('0x'):
                    type_id = int(type_id, 16)
                result[type_id] = instr_type.upper()
    
    # Also add entries from type_id_map if it exists
    if 'instruments' in config and 'type_id_map' in config['instruments']:
        # This doesn't include instrument type names but could be useful in the future
        pass
            
    return result

def get_instrument_common_offsets():
    """Retrieves common parameter offsets for instruments from configuration."""
    config = load_format_config()
    if 'instruments' in config and 'common_fields' in config['instruments']:
        # Extract offsets from common_fields
        offsets = {}
        for field_name, field_config in config['instruments']['common_fields'].items():
            offsets[field_name] = field_config['offset']
            
            # Handle UINT4_2 components
            if 'type' in field_config and field_config['type'] == "UINT4_2" and 'components' in field_config:
                # Add offsets for component fields as well
                # This allows code to reference transpose and eq directly if needed
                for comp_name, comp_config in field_config['components'].items():
                    offsets[comp_name] = field_config['offset']
        
        return offsets
    raise ValueError("Common fields for instruments not found in configuration")

def get_instrument_common_defaults():
    """Retrieves common parameter defaults for instruments from configuration."""
    config = load_format_config()
    if 'instruments' in config and 'common_fields' in config['instruments']:
        # Extract defaults from common_fields
        defaults = {}
        for field_name, field_config in config['instruments']['common_fields'].items():
            # Only add default if explicitly defined
            if 'default' in field_config:
                defaults[field_name] = field_config['default']
                
            # Handle UINT4_2 components 
            if 'type' in field_config and field_config['type'] == "UINT4_2" and 'components' in field_config:
                # Add defaults for component fields
                for comp_name, comp_config in field_config['components'].items():
                    if 'default' in comp_config:
                        defaults[comp_name] = comp_config['default']
        
        return defaults
    raise ValueError("Common defaults for instruments not found in configuration")

def get_modulator_common_offsets():
    """Retrieves common parameter offsets for modulators from configuration."""
    config = load_format_config()
    if 'modulators' in config and 'fields' in config['modulators']:
        # Convert from fields structure to simple offset dictionary
        offsets = {}
        for field_name, field_config in config['modulators']['fields'].items():
            offsets[field_name] = field_config['offset']
        return offsets
    raise ValueError("Fields for modulators not found in configuration")

def get_modulator_type_field_def(modulator_type, field_name):
    """Retrieves field definition for a specific field of a modulator type."""
    config = load_format_config()
    if 'modulators' in config and 'types' in config['modulators']:
        # Try uppercase version first
        lookup_type = modulator_type.upper() if isinstance(modulator_type, str) else modulator_type
        if lookup_type in config['modulators']['types']:
            mod_data = config['modulators']['types'][lookup_type]
            if 'fields' in mod_data and field_name in mod_data['fields']:
                return mod_data['fields'][field_name]
                
        # Try lowercase version as fallback
        lookup_type = modulator_type.lower() if isinstance(modulator_type, str) else modulator_type
        if lookup_type in config['modulators']['types']:
            mod_data = config['modulators']['types'][lookup_type]
            if 'fields' in mod_data and field_name in mod_data['fields']:
                return mod_data['fields'][field_name]
    return None