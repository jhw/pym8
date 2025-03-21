import os
import yaml
from functools import lru_cache

@lru_cache(maxsize=1)
def load_format_config():
    """
    Load the M8 format configuration from the YAML file.
    Uses LRU cache to avoid repeated disk reads.
    
    Returns:
        dict: The parsed configuration
    """
    config_path = os.path.join(os.path.dirname(__file__), 'format_config.yaml')
    with open(config_path, 'r') as config_file:
        return yaml.safe_load(config_file)

def get_offset(section_name):
    """
    Get the offset for a section from the configuration.
    
    Args:
        section_name (str): The name of the section
        
    Returns:
        int: The offset value
    """
    config = load_format_config()
    if section_name in config and 'offset' in config[section_name]:
        offset_value = config[section_name]['offset']
        # Handle hex strings if needed
        if isinstance(offset_value, str) and offset_value.startswith('0x'):
            return int(offset_value, 16)
        return offset_value
    raise ValueError(f"Offset for section '{section_name}' not found in configuration")

def get_count(section_name):
    """
    Get the count for a section from the configuration.
    
    Args:
        section_name (str): The name of the section
        
    Returns:
        int: The count value
    """
    config = load_format_config()
    if section_name in config and 'count' in config[section_name]:
        return config[section_name]['count']
    raise ValueError(f"Count for section '{section_name}' not found in configuration")

def get_param_data(section_path, param_name):
    """
    Get parameter data from the nested configuration.
    
    Args:
        section_path (list): Path to the section (e.g., ['instruments', 'wavsynth', 'params'])
        param_name (str): Name of the parameter
        
    Returns:
        dict: Parameter data including offset, size, type, and default value
    """
    config = load_format_config()
    current = config
    
    # Navigate through the section path
    for part in section_path:
        if part in current:
            current = current[part]
        else:
            raise ValueError(f"Section '{part}' not found in configuration path {section_path}")
            
    # Get parameter data
    if param_name in current:
        return current[param_name]
    raise ValueError(f"Parameter '{param_name}' not found in section {section_path}")

def get_param_type_enum(param_type_str):
    """
    Convert parameter type string to corresponding enum value from M8ParamType.
    
    Args:
        param_type_str (str): String representation of parameter type (e.g., 'UINT8')
        
    Returns:
        int: The enum value corresponding to the type
    """
    config = load_format_config()
    if 'instruments' in config and 'param_types' in config['instruments']:
        param_types = config['instruments']['param_types']
        if param_type_str in param_types:
            return param_types[param_type_str]
    # Default to UINT8 if not found
    return 1  # UINT8 value

def get_modulator_data(modulator_type):
    """
    Get data for a specific modulator type.
    
    Args:
        modulator_type (str): Name of the modulator type (e.g., 'ahd_envelope')
        
    Returns:
        dict: Modulator type data including id and parameters
    """
    config = load_format_config()
    if 'modulators' in config and 'types' in config['modulators']:
        modulator_types = config['modulators']['types']
        if modulator_type in modulator_types:
            return modulator_types[modulator_type]
        raise ValueError(f"Modulator type '{modulator_type}' not found in configuration")
    raise ValueError("Modulators section not found in configuration")

def get_modulator_type_id_map():
    """
    Get a mapping of modulator type IDs to their class paths.
    
    Returns:
        dict: Mapping of type IDs to class paths
    """
    # Hard-code the mappings to match the existing class names
    return {
        0x00: "m8.api.modulators.M8AHDEnvelope",
        0x02: "m8.api.modulators.M8DrumEnvelope",
        0x01: "m8.api.modulators.M8ADSREnvelope",
        0x03: "m8.api.modulators.M8LFO",
        0x04: "m8.api.modulators.M8TriggerEnvelope",
        0x05: "m8.api.modulators.M8TrackingEnvelope"
    }

def get_instrument_type_id(instrument_type):
    """
    Get the type ID for an instrument type.
    
    Args:
        instrument_type (str): Name of the instrument type (e.g., 'wavsynth')
        
    Returns:
        int: The instrument type ID
    """
    config = load_format_config()
    if 'instruments' in config and instrument_type in config['instruments']:
        type_id = config['instruments'][instrument_type]['type_id']
        # Handle hex strings
        if isinstance(type_id, str) and type_id.startswith('0x'):
            return int(type_id, 16)
        return type_id
    raise ValueError(f"Type ID for instrument '{instrument_type}' not found in configuration")

def get_instrument_modulators_offset(instrument_type):
    """
    Get the modulators offset for an instrument type.
    
    Args:
        instrument_type (str): Name of the instrument type (e.g., 'wavsynth')
        
    Returns:
        int: The offset value
    """
    config = load_format_config()
    if ('instruments' in config and instrument_type in config['instruments'] and 
        'modulators_offset' in config['instruments'][instrument_type]):
        return config['instruments'][instrument_type]['modulators_offset']
    raise ValueError(f"Modulators offset for instrument '{instrument_type}' not found in configuration")