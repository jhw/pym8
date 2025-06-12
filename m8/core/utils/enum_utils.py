"""
Utilities for handling M8 enum values.

This module provides simple enum utilities for the M8 tracker library.
Clients should import enums directly and use enum.value when needed.
"""

import logging


class M8EnumValueError(Exception):
    """Exception raised when an invalid enum value is encountered."""
    def __init__(self, message, enum_class=None, value=None, param_name=None):
        self.enum_class = enum_class
        self.value = value
        self.param_name = param_name
        
        if enum_class and value is not None:
            class_name = enum_class.__name__ if hasattr(enum_class, '__name__') else str(enum_class)
            context = f" for parameter '{param_name}'" if param_name else ""
            
            valid_values = [f"{e.name} ({e.value})" for e in enum_class] if hasattr(enum_class, '__iter__') else []
            valid_values_str = ', '.join(valid_values[:10])
            if len(valid_values) > 10:
                valid_values_str += ", ..."
                
            enum_message = f"Invalid value '{value}' for enum {class_name}{context}. Valid values: {valid_values_str}"
            super().__init__(enum_message)
        else:
            super().__init__(message)


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