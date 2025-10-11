import os
import yaml
from functools import lru_cache

@lru_cache(maxsize=1)
def load_format_config(validate=False):
    """Loads M8 format configuration from YAML with caching to avoid disk reads."""
    config_path = os.path.join(os.path.dirname(__file__), 'format_config.yaml')
    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)
        
    # Apply defaults to field definitions
    config = _apply_field_defaults(config)
    
    # Validate if requested - separate to avoid circular imports
    if validate:
        result = validate_config()
        if not result.valid:
            result.raise_if_invalid()
            
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

def get_instrument_type_id(instrument_type):
    # Retrieves type ID for an instrument from config
    # If it's None, return None
    if instrument_type is None:
        return None

    # If it's already an integer, just return it
    if isinstance(instrument_type, int):
        return instrument_type

    # Try to get from config
    if isinstance(instrument_type, str):
        config = load_format_config()

        # Use the type as provided without case conversion
        if ('instruments' in config and 'types' in config['instruments'] and
            instrument_type in config['instruments']['types']):
            type_id = config['instruments']['types'][instrument_type]['type_id']
            if isinstance(type_id, str) and type_id.startswith('0x'):
                return int(type_id, 16)
            return type_id

    raise ValueError(f"Type ID for instrument '{instrument_type}' not found in configuration")

def get_instrument_types():
    # Returns a dictionary of instrument type IDs to type names from configuration
    config = load_format_config()
    result = {}
    if 'instruments' in config and 'types' in config['instruments']:
        for type_name, type_config in config['instruments']['types'].items():
            if 'type_id' in type_config:
                type_id = type_config['type_id']
                if isinstance(type_id, str) and type_id.startswith('0x'):
                    type_id = int(type_id, 16)
                result[type_id] = type_name
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
    
def get_fx_keys_enum_paths(instrument_type_id):
    """Get enum paths for FX keys for the given instrument type."""
    config = load_format_config()
    fx_enums = {}
    
    # Check if fx section exists with enums for key field
    if ('fx' in config and 'fields' in config['fx'] and 
        'key' in config['fx']['fields'] and 'enums' in config['fx']['fields']['key']):
        fx_enums = config['fx']['fields']['key']['enums']
    
    # Try direct lookup by ID
    if instrument_type_id in fx_enums:
        return fx_enums[instrument_type_id]
    
    # Try hex format
    hex_key = f"0x{instrument_type_id:02x}"
    if hex_key in fx_enums:
        return fx_enums[hex_key]
    
    # Try string instrument type
    instrument_types = get_instrument_types()
    if instrument_type_id in instrument_types:
        instrument_type = instrument_types[instrument_type_id]
        if instrument_type in fx_enums:
            return fx_enums[instrument_type]
    
    # Default fallback for when no specific enum is found
    return fx_enums.get("default", [])

def validate_config():
    from m8.core.validation import M8ValidationResult

    # Create a validation result
    result = M8ValidationResult(context="config")

    # Load the configuration
    config = load_format_config()

    # Get valid instrument IDs from config
    valid_instrument_ids = set()
    if 'instruments' in config and 'types' in config['instruments']:
        for type_config in config['instruments']['types'].values():
            if 'type_id' in type_config:
                type_id = type_config['type_id']
                if isinstance(type_id, str) and type_id.startswith('0x'):
                    type_id = int(type_id, 16)
                valid_instrument_ids.add(type_id)
    
    # Check instrument types in config
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
            
            # Check for duplicated or overlapping offsets in params
            if 'params' in instrument_config:
                validate_field_offsets(
                    instrument_config['params'], 
                    f"instruments.types.{instrument_type}.params",
                    result
                )
    
    # Check common fields for duplicated or overlapping offsets
    if 'instruments' in config and 'common_fields' in config['instruments']:
        validate_field_offsets(
            config['instruments']['common_fields'], 
            "instruments.common_fields",
            result
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
    
    # Check for duplicated or overlapping offsets in fx fields
    if 'fx' in config and 'fields' in config['fx']:
        validate_field_offsets(
            config['fx']['fields'], 
            "fx.fields",
            result
        )
    
    return result

def validate_field_offsets(fields, context_path, result):
    """
    Validates field offsets to ensure they are not duplicated or overlapping.
    
    Args:
        fields: Dictionary of field definitions
        context_path: The path in the config for error reporting
        result: M8ValidationResult to add errors to
    """
    if not isinstance(fields, dict):
        return
    
    # Extract field info: name, offset, and size
    field_info = []
    for field_name, field_def in fields.items():
        if isinstance(field_def, dict) and 'offset' in field_def:
            offset = field_def['offset']
            # Default size is 1 if not specified
            size = field_def.get('size', 1)
            field_info.append((field_name, offset, size))
    
    # Sort by offset
    field_info.sort(key=lambda x: x[1])
    
    # Check for duplicates and overlaps
    for i in range(len(field_info) - 1):
        current_name, current_offset, current_size = field_info[i]
        next_name, next_offset, next_size = field_info[i + 1]
        
        # Check for duplicate offsets
        if current_offset == next_offset:
            result.add_error(
                f"Duplicate offset: '{current_name}' and '{next_name}' both have offset {current_offset}",
                context_path
            )
        
        # Check for overlapping fields
        elif current_offset + current_size > next_offset:
            result.add_error(
                f"Overlapping fields: '{current_name}' (offset {current_offset}, size {current_size}) overlaps with '{next_name}' (offset {next_offset})",
                context_path
            )
