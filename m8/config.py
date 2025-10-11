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

