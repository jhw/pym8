import os
import yaml
from m8.enums import M8InstrumentType, M8ModulatorType
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

def get_modulator_data(modulator_type):
    """Retrieves configuration data for a specific modulator type."""
    config = load_format_config()
    if 'modulators' in config and 'types' in config['modulators']:
        modulator_types = config['modulators']['types']
        
        # Use the type as provided without case conversion
        if modulator_type in modulator_types:
            return modulator_types[modulator_type]
            
        raise ValueError(f"Modulator type '{modulator_type}' not found in configuration")
    raise ValueError("Modulators section not found in configuration")

def get_modulator_type_id_map():
    # Provides a mapping of modulator type IDs to their class paths
    # Generate the mapping from the enum values
    enum_map = {member.value: member.name for member in M8ModulatorType}
    
    # Map the enum values to class paths
    # This maintains backward compatibility with code expecting class paths
    class_path_map = {}
    for type_id, type_name in enum_map.items():
        # Convert enum names to class paths (e.g., LFO -> m8.api.modulators.M8LFO)
        class_path_map[type_id] = f"m8.api.modulators.M8{type_name.title().replace('_', '')}"
    
    return class_path_map

def get_modulator_types():
    # Returns a dictionary of modulator type IDs to type names
    # Generate directly from the enum for a single source of truth
    return {member.value: member.name for member in M8ModulatorType}

def get_modulator_type_id(modulator_type):
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
    
    raise ValueError(f"Type ID for modulator '{modulator_type}' not found in enum or configuration")

def get_instrument_type_id(instrument_type):
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
    
    raise ValueError(f"Type ID for instrument '{instrument_type}' not found in enum or configuration")

def get_instrument_modulators_offset(instrument_type=None):
    """Retrieves modulators offset for instruments from configuration."""
    config = load_format_config()
    if 'instruments' in config and 'modulators_offset' in config['instruments']:
        return config['instruments']['modulators_offset']
    raise ValueError("Modulators offset not found in instruments configuration")

def get_instrument_types():
    # Returns a dictionary of instrument type IDs to type names from configuration
    # Generate directly from the enum for a single source of truth
    return {member.value: member.name for member in M8InstrumentType}

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
        # Use the type as provided without case conversion
        if modulator_type in config['modulators']['types']:
            mod_data = config['modulators']['types'][modulator_type]
            if 'fields' in mod_data and field_name in mod_data['fields']:
                return mod_data['fields'][field_name]
    return None
def generate_instrument_type_id_map():
    # Generates the instrument type_id_map from the M8InstrumentType enum
    return {member.value: member.name for member in M8InstrumentType}

def generate_modulator_type_id_map():
    # Generates the modulator type_id_map from the M8ModulatorType enum
    return {member.value: member.name for member in M8ModulatorType}

def validate_config():
    from m8.core.validation import M8ValidationResult
    
    # Create a validation result
    result = M8ValidationResult(context="config")
    
    # Load the configuration
    config = load_format_config()
    
    # Get valid IDs from enums
    valid_instrument_ids = {member.value for member in M8InstrumentType}
    valid_modulator_ids = {member.value for member in M8ModulatorType}
    
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
    
    # Check modulator types
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
