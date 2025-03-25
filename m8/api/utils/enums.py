"""
Utilities for handling M8 enum values.

This module centralizes all enum-related functionality for improved reusability
and easier maintenance.
"""

import importlib
import logging

# Global enum class cache
_ENUM_CLASS_CACHE = {}

# Main enum functions

def serialize_enum(enum_value, log_prefix=None):
    """Convert an enum instance to its string name."""
    if hasattr(enum_value, 'name'):
        return enum_value.name
    
    logger = logging.getLogger(__name__)
    prefix = f"{log_prefix} " if log_prefix else ""
    logger.warning(f"Serializing non-enum {prefix}type: {enum_value}")
    return enum_value

def deserialize_enum(enum_class, value, log_prefix=None):
    """Convert a string enum name or numeric value to enum value."""
    from m8.api import M8EnumValueError
    
    if isinstance(value, str):
        try:
            return enum_class[value].value
        except KeyError:
            raise M8EnumValueError(
                f"Invalid enum string value", 
                enum_class=enum_class, 
                value=value,
                param_name=log_prefix
            )
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
    """Get enum paths specific to an instrument type."""
    if not isinstance(enum_paths, dict) or instrument_type is None:
        return enum_paths
    
    # Create a lookup key from the instrument_type
    lookup_key = None
    
    # Handle IntEnum or any type with a .value attribute (most direct approach)
    if hasattr(instrument_type, 'value'):
        # Try direct value as a key first
        if instrument_type.value in enum_paths:
            return enum_paths.get(instrument_type.value)
            
        # Try hex format
        hex_key = f"0x{instrument_type.value:02x}"
        if hex_key in enum_paths:
            return enum_paths.get(hex_key)
            
        # For IntEnum, also try name as a fallback
        if hasattr(instrument_type, 'name') and instrument_type.name in enum_paths:
            return enum_paths.get(instrument_type.name)
            
        # Use the string value for remaining lookups
        lookup_key = str(instrument_type)
    else:
        # Non-enum type, use string representation
        lookup_key = str(instrument_type)
    
    # Direct string lookup
    if lookup_key in enum_paths:
        return enum_paths.get(lookup_key)
    
    # Try numeric conversion if possible
    if lookup_key and lookup_key.isdigit():
        # Try the numeric value directly
        numeric_key = int(lookup_key)
        if numeric_key in enum_paths:
            return enum_paths.get(numeric_key)
            
        # Try hex format of the numeric value
        hex_key = f"0x{numeric_key:02x}"
        if hex_key in enum_paths:
            return enum_paths.get(hex_key)
    
    # Get enum paths for this instrument type, returning None if not found
    return None

def load_enum_classes(enum_paths, log_context=None):
    """Dynamically load enum classes from module paths with caching support."""
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
            
        # Check if the enum class is already in the cache
        if enum_path in _ENUM_CLASS_CACHE:
            enum_classes.append(_ENUM_CLASS_CACHE[enum_path])
            continue
            
        try:
            # Special handling for hex keys like 0x00 that are in the configuration
            if enum_path.startswith('0x'):
                logger.debug(f"Skipping hex value: {enum_path}")
                continue
                
            parts = enum_path.rsplit('.', 1)
            if len(parts) != 2:
                logger.debug(f"Invalid enum path format: {enum_path}")
                continue
                
            module_name, class_name = parts
            module = importlib.import_module(module_name)
            enum_class = getattr(module, class_name)
            
            # Cache the enum class for future use
            _ENUM_CLASS_CACHE[enum_path] = enum_class
            enum_classes.append(enum_class)
        except (ImportError, AttributeError, ValueError) as e:
            context = f" for {log_context}" if log_context else ""
            logger.warning(f"Error importing enum {enum_path}{context}: {e}")
            
    return enum_classes

# Parameter-level enum functions

def serialize_param_enum_value(value, param_def, instrument_type=None, param_name=None):
    """Serialize a parameter value to its enum string representation."""
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
    """Convert parameter string enum name to numeric value."""
    from m8.api import M8EnumValueError
    
    if not isinstance(value, str):
        return value
    
    enum_paths = get_enum_paths_for_instrument(enum_paths, instrument_type)
    if not enum_paths:
        logger = logging.getLogger(__name__)
        logger.warning(f"No enum defined for instrument type {instrument_type} parameter {param_name}")
        return value
    
    enum_classes = load_enum_classes(enum_paths, param_name)
    
    if enum_classes:
        # Try each enum class to find a match
        for enum_class in enum_classes:
            try:
                return enum_class[value].value
            except KeyError:
                continue
    
    # If we reach here, the value wasn't found in any enum class
    if enum_classes:
        # Use the first enum class for error reporting
        raise M8EnumValueError(
            f"Invalid enum value", 
            enum_class=enum_classes[0],
            value=value,
            param_name=param_name,
            instrument_type=instrument_type
        )
    else:
        error_msg = f"Invalid enum string value: '{value}' - no enum classes found for {param_name}"
        raise M8EnumValueError(error_msg)
    
def ensure_enum_int_value(value, enum_paths, instrument_type=None, param_name=None):
    """Convert a value to integer enum value if it's a string enum name."""
    if not isinstance(value, str):
        return value
    
    from m8.api import M8EnumValueError
    
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
    
    # If we reach here, the value wasn't found in any enum class
    if enum_classes:
        # Use the first enum class for error reporting
        raise M8EnumValueError(
            f"Invalid enum value", 
            enum_class=enum_classes[0],
            value=value,
            param_name=param_name,
            instrument_type=instrument_type
        )
    else:
        error_msg = f"Invalid enum string value: '{value}' - no enum classes found"
        raise M8EnumValueError(error_msg)

# Clear the enum class cache
def clear_enum_cache():
    """Clear the enum class cache."""
    global _ENUM_CLASS_CACHE
    _ENUM_CLASS_CACHE.clear()

# Enum mixins and decorators

class EnumPropertyMixin:
    """Mixin to add enum support to class properties."""
    
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
    """Get a list of all valid enum names for an enum class."""
    return [e.name for e in enum_class]

def get_enum_values(enum_class):
    """Get a list of all valid enum values for an enum class."""
    return [e.value for e in enum_class]

def enum_name_to_value(enum_class, name):
    """Convert an enum name to its value."""
    return enum_class[name].value

def enum_value_to_name(enum_class, value):
    """Convert an enum value to its name."""
    return enum_class(value).name