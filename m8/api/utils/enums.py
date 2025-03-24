"""
Utilities for handling M8 enum values.

This module centralizes all enum-related functionality for improved reusability
and easier maintenance.
"""

import importlib
import logging

# Main enum functions

def serialize_enum(enum_value, log_prefix=None):
    """
    Convert an enum instance to its string name representation.
    
    Args:
        enum_value: The enum value to serialize
        log_prefix: Optional prefix for log messages
        
    Returns:
        String name representation of the enum, or the original value if not an enum
    """
    if hasattr(enum_value, 'name'):
        return enum_value.name
    
    logger = logging.getLogger(__name__)
    prefix = f"{log_prefix} " if log_prefix else ""
    logger.warning(f"Serializing non-enum {prefix}type: {enum_value}")
    return enum_value

def deserialize_enum(enum_class, value, log_prefix=None):
    """
    Convert a string enum name or numeric value to its corresponding enum value.
    
    Args:
        enum_class: The enum class to use for conversion
        value: String enum name or numeric value
        log_prefix: Optional prefix for log messages
        
    Returns:
        The numeric value of the enum
        
    Raises:
        M8EnumError: If string value doesn't match any enum name
    """
    from m8.enums import M8EnumError
    
    if isinstance(value, str):
        try:
            return enum_class[value].value
        except KeyError:
            error_msg = f"Invalid enum string value: '{value}' not found in {enum_class.__name__}"
            if log_prefix:
                error_msg = f"{log_prefix}: {error_msg}"
            raise M8EnumError(error_msg)
    else:
        try:
            enum_class(value)
        except ValueError:
            logger = logging.getLogger(__name__)
            prefix = f"{log_prefix} " if log_prefix else ""
            logger.warning(f"Deserializing unknown {prefix}type ID: {value}")
        
        return value

# Instrument-specific enum functions

def get_enum_paths_for_instrument(enum_paths, instrument_type):
    """
    Get enum paths specific to an instrument type from a dict mapping.
    
    Args:
        enum_paths: String, list, or dict mapping instrument types to enum paths
        instrument_type: The instrument type ID
        
    Returns:
        Enum paths for the specified instrument type, or the original paths
    """
    if not isinstance(enum_paths, dict) or instrument_type is None:
        return enum_paths
        
    instrument_type_key = str(instrument_type)
    
    if instrument_type_key.isdigit():
        hex_key = f"0x{int(instrument_type_key):02x}"
        if hex_key in enum_paths:
            instrument_type_key = hex_key
    
    # Get enum paths for this instrument type, returning None if not found
    return enum_paths.get(instrument_type_key)

def load_enum_classes(enum_paths, log_context=None):
    """
    Dynamically load enum classes from their module paths.
    
    Args:
        enum_paths: String or list of strings with fully qualified enum class paths
        log_context: Optional context for logging
        
    Returns:
        List of enum classes
    """
    logger = logging.getLogger(__name__)
    enum_classes = []
    
    if not enum_paths:
        return enum_classes
        
    # Make sure enum_paths is iterable
    if isinstance(enum_paths, str):
        enum_paths = [enum_paths]
        
    for enum_path in enum_paths:
        # Skip empty or invalid paths
        if not enum_path or not isinstance(enum_path, str):
            continue
            
        try:
            parts = enum_path.rsplit('.', 1)
            if len(parts) != 2:
                logger.warning(f"Invalid enum path format: {enum_path}")
                continue
                
            module_name, class_name = parts
            module = importlib.import_module(module_name)
            enum_class = getattr(module, class_name)
            enum_classes.append(enum_class)
        except (ImportError, AttributeError, ValueError) as e:
            context = f" for {log_context}" if log_context else ""
            logger.warning(f"Error importing enum {enum_path}{context}: {e}")
            
    return enum_classes

# Parameter-level enum functions

def serialize_param_enum_value(value, param_def, instrument_type=None, param_name=None):
    """
    Serialize a parameter value to its enum string representation if applicable.
    
    Args:
        value: The parameter value to serialize
        param_def: Parameter definition with optional 'enums' field
        instrument_type: Optional instrument type for instrument-specific enums
        param_name: Optional parameter name for logging
        
    Returns:
        String enum name or original value
    """
    if "enums" not in param_def:
        return value
        
    enum_paths = get_enum_paths_for_instrument(param_def["enums"], instrument_type)
    if not enum_paths:
        return value
        
    enum_classes = load_enum_classes(enum_paths, param_name)
    if not enum_classes:
        return value
        
    if hasattr(value, 'name'):
        return value.name
        
    if isinstance(value, int):
        for enum_class in enum_classes:
            try:
                enum_value = enum_class(value)
                return enum_value.name
            except ValueError:
                continue
                
    return value

def deserialize_param_enum(enum_paths, value, param_name=None, instrument_type=None):
    """
    Deserialize a parameter value from string enum name to numeric value.
    
    Args:
        enum_paths: String, list, or dict of enum class paths
        value: String enum name or numeric value
        param_name: Optional parameter name for error messages
        instrument_type: Optional instrument type for instrument-specific enums
        
    Returns:
        Numeric enum value or original value
        
    Raises:
        M8EnumError: If string value doesn't match any enum name
    """
    from m8.enums import M8EnumError
    
    if not isinstance(value, str):
        return value
    
    enum_paths = get_enum_paths_for_instrument(enum_paths, instrument_type)
    if not enum_paths:
        logger = logging.getLogger(__name__)
        logger.warning(f"No enum defined for instrument type {instrument_type} parameter {param_name}")
        return value
    
    enum_classes = load_enum_classes(enum_paths, param_name)
    
    if enum_classes:
        for enum_class in enum_classes:
            try:
                return enum_class[value].value
            except KeyError:
                continue
    
    param_details = f" for parameter '{param_name}'" if param_name else ""
    error_msg = f"Invalid enum string value: '{value}' not found in any of the provided enum classes{param_details}"
    raise M8EnumError(error_msg)
    
def ensure_enum_int_value(value, enum_paths, instrument_type=None):
    """
    Ensure a value is converted to its integer enum value if it's a string enum name.
    
    Args:
        value: String enum name or numeric value
        enum_paths: Enum class paths to use for conversion
        instrument_type: Optional instrument type
        
    Returns:
        Integer enum value or original value
        
    Raises:
        M8EnumError: If string value doesn't match any enum name
    """
    if not isinstance(value, str):
        return value
    
    from m8.enums import M8EnumError
    
    enum_paths = get_enum_paths_for_instrument(enum_paths, instrument_type)
    if not enum_paths:
        logger = logging.getLogger(__name__)
        logger.warning(f"No enum defined for instrument type {instrument_type}")
        return value
    
    enum_classes = load_enum_classes(enum_paths)
    
    for enum_class in enum_classes:
        try:
            return enum_class[value].value
        except KeyError:
            continue
    
    error_msg = f"Invalid enum string value: '{value}' not found in any of the provided enum classes"
    raise M8EnumError(error_msg)

# Enum mixins and decorators

class EnumPropertyMixin:
    """
    Mixin to add enum support to class properties.
    
    This mixin adds methods to easily convert between string enum names and
    numeric enum values for class properties.
    """
    
    def _get_enum_value(self, property_name, value, default=None):
        """Get the numeric value for an enum property."""
        if hasattr(self, 'ENUM_MAPPINGS') and property_name in self.ENUM_MAPPINGS:
            mapping = self.ENUM_MAPPINGS[property_name]
            enum_class = mapping.get('enum_class')
            
            if enum_class and isinstance(value, str):
                try:
                    return enum_class[value].value
                except KeyError:
                    if default is not None:
                        return default
                    raise ValueError(f"Invalid enum value '{value}' for {property_name}")
        
        return value
    
    def _get_enum_name(self, property_name, value):
        """Get the string name for an enum property value."""
        if hasattr(self, 'ENUM_MAPPINGS') and property_name in self.ENUM_MAPPINGS:
            mapping = self.ENUM_MAPPINGS[property_name]
            enum_class = mapping.get('enum_class')
            
            if enum_class and isinstance(value, int):
                try:
                    return enum_class(value).name
                except ValueError:
                    pass
        
        return value

# Utility functions for working with enums

def get_enum_names(enum_class):
    """
    Get a list of all valid enum names for an enum class.
    
    Args:
        enum_class: The enum class
        
    Returns:
        List of string enum names
    """
    return [e.name for e in enum_class]

def get_enum_values(enum_class):
    """
    Get a list of all valid enum values for an enum class.
    
    Args:
        enum_class: The enum class
        
    Returns:
        List of integer enum values
    """
    return [e.value for e in enum_class]

def enum_name_to_value(enum_class, name):
    """
    Convert an enum name to its value.
    
    Args:
        enum_class: The enum class
        name: String enum name
        
    Returns:
        Integer enum value
        
    Raises:
        KeyError: If name is not a valid enum name
    """
    return enum_class[name].value

def enum_value_to_name(enum_class, value):
    """
    Convert an enum value to its name.
    
    Args:
        enum_class: The enum class
        value: Integer enum value
        
    Returns:
        String enum name
        
    Raises:
        ValueError: If value is not a valid enum value
    """
    return enum_class(value).name