"""
Utilities for handling M8 enum values.

This module centralizes all enum-related functionality for improved reusability
and easier maintenance, including the instrument context manager used for
resolving instrument-specific enums.
"""

import importlib
import logging

# Global enum class cache
_ENUM_CLASS_CACHE = {}

# Context Manager for Instrument operations

class M8InstrumentContext:
    """Context manager for instrument-related operations.
    
    This singleton class provides a way to establish a context for operations
    that need to know about the parent instrument, without requiring explicit
    coupling between objects.
    
    Primary use cases:
    1. Providing instrument type context for modulator enum serialization
    2. Providing instrument type context for FX enum serialization
    
    Note: This context manager works exclusively with numeric IDs internally.
    """
    
    _instance = None  # Singleton instance
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance of the context manager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
        
    def __init__(self):
        """Initialize a new instrument context manager."""
        self.project = None
        self.current_instrument_id = None
        self.current_instrument_type_id = None
        
    def set_project(self, project):
        """Set the current project context."""
        self.project = project
        
    def get_instrument_type_id(self, instrument_id=None):
        """Get instrument type ID for a given instrument ID or the current instrument.
        
        Args:
            instrument_id: Optional ID to look up. If not provided, uses current context.
            
        Returns:
            The instrument type ID or None if not available.
        """
        # If explicit instrument ID is provided, look it up
        if instrument_id is not None:
            if self.project and 0 <= instrument_id < len(self.project.instruments):
                instrument = self.project.instruments[instrument_id]
                # Get the numeric ID from the instrument
                if hasattr(instrument, 'instrument_type_id'):
                    return instrument.instrument_type_id
                # If it just has instrument_type
                elif hasattr(instrument, 'instrument_type'):
                    type_val = getattr(instrument, 'instrument_type')
                    # If it's an enum, get its value
                    if hasattr(type_val, 'value'):
                        return type_val.value
                    # If it's already a numeric ID
                    elif isinstance(type_val, int):
                        return type_val
                    # String values should be converted before reaching here
        
        # Otherwise use current context
        return self.current_instrument_type_id
    
    def get_instrument_type(self):
        """Get instrument type string for compatibility with existing code.
        
        Note: This is a temporary bridge method to ease transition to the ID-based approach.
        New code should use get_instrument_type_id() instead and handle the string conversion
        at the API boundary.
        
        Returns:
            The instrument type string or None if not available.
        """
        type_id = self.get_instrument_type_id()
        if type_id is not None:
            from m8.config import get_instrument_types
            instrument_types = get_instrument_types()
            return instrument_types.get(type_id)
        return None
        
    def with_instrument(self, instrument_id=None, instrument_type_id=None):
        """Create a context block for operations with a specific instrument.
        
        Args:
            instrument_id: Optional instrument ID to use in the context block
            instrument_type_id: Optional explicit instrument type ID to use
            
        Returns:
            A context manager block that sets the instrument context
        """
        return _InstrumentContextBlock(self, instrument_id, instrument_type_id)
        
    def clear(self):
        """Clear all context state."""
        self.project = None
        self.current_instrument_id = None
        self.current_instrument_type_id = None

class _InstrumentContextBlock:
    """Context block for instrument operations."""
    
    def __init__(self, manager, instrument_id=None, instrument_type_id=None):
        """Initialize a context block.
        
        Args:
            manager: The parent context manager
            instrument_id: Optional instrument ID to set during the block
            instrument_type_id: Optional explicit instrument type ID to use
        """
        self.manager = manager
        self.instrument_id = instrument_id
        self.instrument_type_id = instrument_type_id
        self.previous_id = None
        self.previous_type_id = None
        
    def __enter__(self):
        """Enter the context block, setting instrument context."""
        self.previous_id = self.manager.current_instrument_id
        self.previous_type_id = self.manager.current_instrument_type_id
        
        # Update the instrument ID if provided
        if self.instrument_id is not None:
            self.manager.current_instrument_id = self.instrument_id
        
        # Update the instrument type ID if provided
        if self.instrument_type_id is not None:
            self.manager.current_instrument_type_id = self.instrument_type_id
        
        return self.manager
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context block, restoring previous context."""
        self.manager.current_instrument_id = self.previous_id
        self.manager.current_instrument_type_id = self.previous_type_id

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
    
    # With the improved context manager, string instrument types are 
    # properly converted to IDs there, so we no longer need a hardcoded mapping here.
    
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
    
    # Handle string instrument types by getting their ID
    instrument_type_id = None
    if isinstance(instrument_type, str):
        from m8.config import get_instrument_type_id
        try:
            instrument_type_id = get_instrument_type_id(instrument_type)
        except ValueError:
            pass
    
    # Try with the string type first
    enum_paths = get_enum_paths_for_instrument(param_def["enums"], instrument_type)
    
    # If that didn't work, try with the ID
    if not enum_paths and instrument_type_id is not None:
        enum_paths = get_enum_paths_for_instrument(param_def["enums"], instrument_type_id)
    
    if not enum_paths:
        # Last resort: Try direct hex format
        if instrument_type_id is not None:
            hex_key = f"0x{instrument_type_id:02x}"
            if isinstance(param_def["enums"], dict) and hex_key in param_def["enums"]:
                enum_paths = param_def["enums"][hex_key]
    
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
    
    # Handle string instrument types by getting their ID
    instrument_type_id = None
    if isinstance(instrument_type, str):
        from m8.config import get_instrument_type_id
        try:
            instrument_type_id = get_instrument_type_id(instrument_type)
        except ValueError:
            pass
    
    # Try with the string type first
    enum_paths_resolved = get_enum_paths_for_instrument(enum_paths, instrument_type)
    
    # If that didn't work, try with the ID
    if not enum_paths_resolved and instrument_type_id is not None:
        enum_paths_resolved = get_enum_paths_for_instrument(enum_paths, instrument_type_id)
    
    if not enum_paths_resolved:
        # Last resort: Try direct hex format
        if instrument_type_id is not None and isinstance(enum_paths, dict):
            hex_key = f"0x{instrument_type_id:02x}"
            if hex_key in enum_paths:
                enum_paths_resolved = enum_paths[hex_key]
    
    if not enum_paths_resolved:
        logger = logging.getLogger(__name__)
        logger.warning(f"No enum defined for instrument type {instrument_type} parameter {param_name}")
        return value
    
    enum_classes = load_enum_classes(enum_paths_resolved, param_name)
    
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
    
    # Handle string instrument types by getting their ID
    instrument_type_id = None
    if isinstance(instrument_type, str):
        from m8.config import get_instrument_type_id
        try:
            instrument_type_id = get_instrument_type_id(instrument_type)
        except ValueError:
            pass
    
    # Try with the string type first
    enum_paths_resolved = get_enum_paths_for_instrument(enum_paths, instrument_type)
    
    # If that didn't work, try with the ID
    if not enum_paths_resolved and instrument_type_id is not None:
        enum_paths_resolved = get_enum_paths_for_instrument(enum_paths, instrument_type_id)
    
    if not enum_paths_resolved:
        # Last resort: Try direct hex format
        if instrument_type_id is not None and isinstance(enum_paths, dict):
            hex_key = f"0x{instrument_type_id:02x}"
            if hex_key in enum_paths:
                enum_paths_resolved = enum_paths[hex_key]
    
    if not enum_paths_resolved:
        logger = logging.getLogger(__name__)
        logger.warning(f"No enum defined for instrument type {instrument_type}")
        return value
    
    enum_classes = load_enum_classes(enum_paths_resolved)
    
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

# Utility functions to abstract common boilerplate patterns

def get_instrument_type_from_id(type_id):
    """Convert numeric instrument type ID to string name.
    
    This abstracts the common pattern of converting an instrument type ID to its string representation.
    
    Args:
        type_id: The numeric instrument type ID to convert
        
    Returns:
        The string representation of the instrument type, or None if not found
    """
    if type_id is None:
        return None
        
    from m8.config import get_instrument_types
    instrument_types = get_instrument_types()
    return instrument_types.get(type_id)
    
def get_instrument_type_from_context():
    """Get instrument type string from the current context.
    
    This abstracts the common pattern of retrieving the current instrument type ID from context
    and converting it to its string representation.
    
    Returns:
        The string representation of the current instrument type, or None if not available
    """
    context = M8InstrumentContext.get_instance()
    instrument_type_id = context.get_instrument_type_id()
    return get_instrument_type_from_id(instrument_type_id)

def get_type_id(enum_or_value):
    """Extract numeric ID from various type representations.
    
    This abstracts the common pattern of extracting a numeric ID from enum objects,
    enum values, or direct integer values.
    
    Args:
        enum_or_value: An enum instance, enum value, or integer
        
    Returns:
        The numeric ID value or None if not determinable
    """
    if enum_or_value is None:
        return None
        
    # If it's an enum, get its value
    if hasattr(enum_or_value, 'value'):
        return enum_or_value.value
    
    # If it's already a numeric ID
    if isinstance(enum_or_value, int):
        return enum_or_value
        
    # If it's a string, try to convert (used rarely, prefer direct IDs)
    if isinstance(enum_or_value, str):
        from m8.config import get_instrument_type_id
        try:
            return get_instrument_type_id(enum_or_value)
        except ValueError:
            return None
            
    return None

def with_instrument_context(obj_or_id=None):
    """Create a context manager for instrument operations.
    
    This abstracts the common pattern of setting up a context block for an instrument.
    
    Args:
        obj_or_id: Either an instrument object, instrument ID, or instrument type ID
        
    Returns:
        A context manager block that sets the instrument context
    """
    context = M8InstrumentContext.get_instance()
    
    # Handle different input types
    instrument_id = None
    instrument_type_id = None
    
    if obj_or_id is None:
        # Use current context
        pass
    elif hasattr(obj_or_id, 'instrument_type'):
        # It's an instrument object
        instrument_type_id = get_type_id(obj_or_id.instrument_type)
    elif hasattr(obj_or_id, 'type'):
        # It's an instrument object with 'type' field
        instrument_type_id = get_type_id(obj_or_id.type)
    else:
        # Assume it's an ID
        instrument_type_id = get_type_id(obj_or_id)
        
    return context.with_instrument(instrument_id=instrument_id, instrument_type_id=instrument_type_id)

def serialize_with_context(param_def, value, param_name=None):
    """Serialize a parameter value with automatic context handling.
    
    This abstracts the common pattern of getting the instrument context when needed
    and using it to serialize a parameter value.
    
    Args:
        param_def: Parameter definition from config
        value: The parameter value to serialize
        param_name: Optional parameter name for logging
        
    Returns:
        The serialized value (with enum string conversion if applicable)
    """
    if "enums" not in param_def:
        return value
        
    # Try with explicit instrument_type from context
    instrument_type = get_instrument_type_from_context()
    
    return serialize_param_enum_value(value, param_def, instrument_type, param_name)

def is_valid_type_id(type_id, valid_types):
    """Check if a type ID is valid.
    
    This abstracts the common pattern of checking if a type ID is in a list of valid types.
    
    Args:
        type_id: The type ID to check
        valid_types: A dictionary or list of valid types
        
    Returns:
        True if the type ID is valid, False otherwise
    """
    if type_id is None:
        return False
        
    if isinstance(valid_types, dict):
        return type_id in valid_types
    elif isinstance(valid_types, list):
        return type_id in valid_types
    
    return False

# Original utility functions for working with enums

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