import os
import yaml
from functools import lru_cache

@lru_cache(maxsize=1)
def load_format_config():
    """Loads M8 format configuration from YAML with caching to avoid disk reads."""
    config_path = os.path.join(os.path.dirname(__file__), 'format_config.yaml')
    with open(config_path, 'r') as config_file:
        return yaml.safe_load(config_file)

def get_offset(section_name):
    """Retrieves section offset from configuration, handling hex values."""
    config = load_format_config()
    if section_name in config and 'offset' in config[section_name]:
        offset_value = config[section_name]['offset']
        if isinstance(offset_value, str) and offset_value.startswith('0x'):
            return int(offset_value, 16)
        return offset_value
    raise ValueError(f"Offset for section '{section_name}' not found in configuration")

def get_count(section_name):
    """Retrieves count value for a section from configuration."""
    config = load_format_config()
    if section_name in config and 'count' in config[section_name]:
        return config[section_name]['count']
    raise ValueError(f"Count for section '{section_name}' not found in configuration")

def get_param_data(section_path, param_name):
    """Navigates nested config to retrieve parameter data at the specified path."""
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
        if modulator_type in modulator_types:
            return modulator_types[modulator_type]
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
            result[type_id] = mod_type
            
    return result

def get_modulator_type_id(modulator_type):
    """Retrieves type ID for a modulator from configuration."""
    config = load_format_config()
    if 'modulators' in config and 'types' in config['modulators'] and modulator_type in config['modulators']['types']:
        type_id = config['modulators']['types'][modulator_type]['id']
        if isinstance(type_id, str) and type_id.startswith('0x'):
            return int(type_id, 16)
        return type_id
    raise ValueError(f"Type ID for modulator '{modulator_type}' not found in configuration")

def get_instrument_type_id(instrument_type):
    """Retrieves type ID for an instrument from configuration."""
    config = load_format_config()
    if 'instruments' in config and instrument_type in config['instruments']:
        type_id = config['instruments'][instrument_type]['type_id']
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
    
    for instr_type, instr_config in config['instruments'].items():
        # Skip non-instrument sections
        if isinstance(instr_config, dict) and 'type_id' in instr_config:
            type_id = instr_config['type_id']
            # Convert hex strings to integers
            if isinstance(type_id, str) and type_id.startswith('0x'):
                type_id = int(type_id, 16)
            result[type_id] = instr_type
            
    return result

def get_instrument_common_offsets():
    """Retrieves common parameter offsets for instruments from configuration."""
    config = load_format_config()
    if 'instruments' in config and 'common_offsets' in config['instruments']:
        return config['instruments']['common_offsets']
    raise ValueError("Common offsets for instruments not found in configuration")

def get_modulator_common_offsets():
    """Retrieves common parameter offsets for modulators from configuration."""
    config = load_format_config()
    if 'modulators' in config and 'common_offsets' in config['modulators']:
        return config['modulators']['common_offsets']
    raise ValueError("Common offsets for modulators not found in configuration")