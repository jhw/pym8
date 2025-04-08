"""
Utilities for handling M8 enum values.

This module centralizes all enum-related functionality for improved reusability
and easier maintenance, including the instrument context manager used for
resolving instrument-specific enums.
"""

import importlib
import logging


class M8EnumValueError(Exception):
    """Exception raised when an invalid enum value is encountered."""
    def __init__(self, message, enum_class=None, value=None, param_name=None, instrument_type=None):
        self.enum_class = enum_class
        self.value = value
        self.param_name = param_name
        self.instrument_type = instrument_type
        
        # Build detailed error message if components are provided
        if enum_class and value is not None:
            class_name = enum_class.__name__ if hasattr(enum_class, '__name__') else str(enum_class)
            details = []
            
            if param_name:
                details.append(f"parameter '{param_name}'")
            if instrument_type:
                details.append(f"instrument type '{instrument_type}'")
                
            context = f" for {' '.join(details)}" if details else ""
            
            valid_values = [f"{e.name} ({e.value})" for e in enum_class] if hasattr(enum_class, '__iter__') else []
            valid_values_str = ', '.join(valid_values[:10])
            if len(valid_values) > 10:
                valid_values_str += ", ..."
                
            enum_message = f"Invalid value '{value}' for enum {class_name}{context}. Valid values: {valid_values_str}"
            super().__init__(enum_message)
        else:
            super().__init__(message)

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
        import logging
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initializing M8InstrumentContext")
        self.project = None
        self.current_instrument_id = None
        self.current_instrument_type_id = None
        
    def set_project(self, project):
        """Set the current project context."""
        self.logger.debug(f"Setting project on context manager: {project}")
        self.project = project
        
    def get_instrument_type_id(self, instrument_id=None):
        """Get instrument type ID for a given instrument ID or the current instrument.
        
        Args:
            instrument_id: Optional ID to look up. If not provided, uses current context.
            
        Returns:
            The instrument type ID or None if not available.
        """
        self.logger.debug(f"get_instrument_type_id called with instrument_id={instrument_id}")
        self.logger.debug(f"Current context state: project={self.project is not None}, "
                        f"current_instrument_id={self.current_instrument_id}, "
                        f"current_instrument_type_id={self.current_instrument_type_id}")
        
        # If explicit instrument ID is provided, look it up
        if instrument_id is not None:
            self.logger.debug(f"Looking up instrument type for ID: {instrument_id}")
            if self.project and 0 <= instrument_id < len(self.project.instruments):
                instrument = self.project.instruments[instrument_id]
                self.logger.debug(f"Found instrument: {instrument}, class: {instrument.__class__.__name__}")
                
                # Get the numeric ID from the instrument
                if hasattr(instrument, 'instrument_type_id'):
                    result = instrument.instrument_type_id
                    self.logger.debug(f"Found instrument_type_id: {result}")
                    return result
                # If it just has instrument_type
                elif hasattr(instrument, 'instrument_type'):
                    type_val = getattr(instrument, 'instrument_type')
                    self.logger.debug(f"Found instrument_type: {type_val}, type: {type(type_val)}")
                    
                    # If it's an enum, get its value
                    if hasattr(type_val, 'value'):
                        result = type_val.value
                        self.logger.debug(f"Extracted enum value: {result}")
                        return result
                    # If it's already a numeric ID
                    elif isinstance(type_val, int):
                        self.logger.debug(f"Using numeric instrument_type: {type_val}")
                        return type_val
                    # String values should be converted before reaching here
                    elif isinstance(type_val, str):
                        self.logger.debug(f"Found string instrument_type: {type_val}, attempting conversion")
                        from m8.config import get_instrument_type_id
                        try:
                            result = get_instrument_type_id(type_val)
                            self.logger.debug(f"Converted string to ID: {result}")
                            return result
                        except ValueError:
                            self.logger.warning(f"Failed to convert string instrument_type: {type_val}")
                else:
                    self.logger.warning(f"Instrument doesn't have instrument_type or instrument_type_id attributes")
                    self.logger.debug(f"Available attributes: {dir(instrument)}")
                    
                    # Special handling for M8Block
                    if instrument.__class__.__name__ == 'M8Block':
                        self.logger.debug("Attempting to extract type from M8Block")
                        # Check if this is an instrument block with a type field
                        if hasattr(instrument, 'data') and len(instrument.data) > 0:
                            # For M8 instruments, the type is usually stored in the first byte
                            # 0 = WAVSYNTH, 1 = MACROSYNTH, 2 = SAMPLER
                            potential_type = instrument.data[0]
                            # Only use if it's a valid value and not an empty indicator (0xFF)
                            if potential_type not in (0xFF, None) and potential_type < 3:
                                self.logger.debug(f"Extracted potential type from data: {potential_type}")
                                return potential_type
                            else:
                                self.logger.debug(f"Block has first byte {potential_type}, but it doesn't look like a valid instrument type")
                        
                        # Try to detect sampler instruments specifically - they have a distinct pattern
                        # in their data with specific byte signatures
                        if hasattr(instrument, 'data') and len(instrument.data) >= 22:
                            # Check for sampler signature: byte 16-17 contains sample data length
                            if instrument.data[0] == 2:  # Type 2 = SAMPLER
                                self.logger.debug("Block matches SAMPLER signature")
                                return 2
            else:
                self.logger.warning(f"Instrument ID {instrument_id} not found in project or project is None")
        
        # Otherwise use current context
        self.logger.debug(f"Using current context instrument type ID: {self.current_instrument_type_id}")
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
        
    def with_contained_context(self, instrument_or_type):
        if hasattr(instrument_or_type, 'type'):
            type_id = get_type_id(instrument_or_type.type)
        elif hasattr(instrument_or_type, 'instrument_type'):
            type_id = get_type_id(instrument_or_type.instrument_type)
        else:
            type_id = get_type_id(instrument_or_type)
            
        return self.with_instrument(instrument_type_id=type_id)
    
    def with_referenced_context(self, instrument_id):
        if instrument_id is None or instrument_id == 0xFF:
            return self.with_instrument(instrument_type_id=None)
        
        # Look up the instrument type ID from the instrument ID
        type_id = self.get_instrument_type_id(instrument_id)
            
        # Set both the ID and the resolved type ID
        return self.with_instrument(instrument_id=instrument_id, instrument_type_id=type_id)
    
    def with_phrase_step_context(self, step):
        if not hasattr(step, 'instrument') or step.instrument == 0xFF:
            return self.with_instrument(instrument_type_id=None)
            
        return self.with_referenced_context(step.instrument)
        
    def with_instrument(self, instrument_id=None, instrument_type_id=None):
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
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"Entering context block with ID={self.instrument_id}, type_id={self.instrument_type_id}")
        logger.debug(f"Before: context.current_instrument_id={self.manager.current_instrument_id}, "
                   f"context.current_instrument_type_id={self.manager.current_instrument_type_id}")
        
        self.previous_id = self.manager.current_instrument_id
        self.previous_type_id = self.manager.current_instrument_type_id
        
        # Update the instrument ID if provided
        if self.instrument_id is not None:
            self.manager.current_instrument_id = self.instrument_id
        
        # Update the instrument type ID if provided
        if self.instrument_type_id is not None:
            self.manager.current_instrument_type_id = self.instrument_type_id
        
        logger.debug(f"After: context.current_instrument_id={self.manager.current_instrument_id}, "
                   f"context.current_instrument_type_id={self.manager.current_instrument_type_id}")
        
        return self.manager
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context block, restoring previous context."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"Exiting context block, restoring ID={self.previous_id}, type_id={self.previous_type_id}")
        logger.debug(f"Before restore: context.current_instrument_id={self.manager.current_instrument_id}, "
                   f"context.current_instrument_type_id={self.manager.current_instrument_type_id}")
        
        self.manager.current_instrument_id = self.previous_id
        self.manager.current_instrument_type_id = self.previous_type_id
        
        logger.debug(f"After restore: context.current_instrument_id={self.manager.current_instrument_id}, "
                   f"context.current_instrument_type_id={self.manager.current_instrument_type_id}")

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
    import logging
    logger = logging.getLogger(__name__)
    
    logger.debug(f"Serializing param enum value: value={value}, param_name={param_name}, "
               f"instrument_type={instrument_type}")
    
    if "enums" not in param_def:
        logger.debug(f"No enums in param_def, returning original value: {value}")
        return value
    
    # For special param types like FX keys, we could add config-based fallbacks here in the future
    # But we'll rely on proper context propagation instead of hardcoding values
    
    # Initialize instrument_type_id variable
    instrument_type_id = None
    
    # Try to get instrument_type from context if not provided
    if instrument_type is None:
        context = M8InstrumentContext.get_instance()
        
        # Get the instrument type ID first to ensure we have the raw ID
        type_id = context.get_instrument_type_id()
        if type_id is not None:
            # Convert the ID to a string instrument type for lookup
            inst_type = get_instrument_type_from_id(type_id)
            if inst_type:
                logger.info(f"Using instrument type from context: {inst_type} (ID: {type_id})")
                instrument_type = inst_type
                instrument_type_id = type_id
            else:
                # Use the ID directly
                logger.info(f"Using instrument type ID from context: {type_id}")
                instrument_type_id = type_id
                instrument_type = None
        else:
            # Check if context has a type string directly
            inst_type = context.get_instrument_type()
            if inst_type:
                logger.info(f"Using instrument type string from context: {inst_type}")
                instrument_type = inst_type
                # Also get the ID for later use
                from m8.config import get_instrument_type_id
                try:
                    instrument_type_id = get_instrument_type_id(inst_type)
                except ValueError:
                    instrument_type_id = None
            else:
                logger.debug("No instrument_type provided and none found in context")
                # For FX fields, use SAMPLER as a fallback since it's most common
                if param_name == 'key':
                    logger.info("Using SAMPLER as fallback for FX serialization")
                    instrument_type = "SAMPLER"
                    instrument_type_id = 2  # SAMPLER ID
    else:
        # Extract ID from provided instrument_type
        instrument_type_id = None
        if isinstance(instrument_type, str):
            logger.info(f"Converting string instrument_type to ID: {instrument_type}")
            from m8.config import get_instrument_type_id
            try:
                instrument_type_id = get_instrument_type_id(instrument_type)
                logger.info(f"Converted to ID: {instrument_type_id}")
            except ValueError:
                logger.warning(f"Failed to convert string instrument_type to ID: {instrument_type}")
        elif isinstance(instrument_type, int):
            instrument_type_id = instrument_type
    
    # Try multiple approaches to find enum paths, starting with most direct
    
    # 1. Try direct raw ID lookup in hex format
    enum_paths = None
    if instrument_type_id is not None:
        hex_key = f"0x{instrument_type_id:02x}"
        logger.info(f"Trying hex key format: {hex_key}")
        if isinstance(param_def["enums"], dict) and hex_key in param_def["enums"]:
            enum_paths = param_def["enums"][hex_key]
            logger.info(f"Found enum paths with hex key: {enum_paths}")
    
    # 2. Try with the ID directly
    if not enum_paths and instrument_type_id is not None:
        logger.info(f"Trying with ID directly: {instrument_type_id}")
        if isinstance(param_def["enums"], dict) and instrument_type_id in param_def["enums"]:
            enum_paths = param_def["enums"][instrument_type_id]
            logger.info(f"Found enum paths with direct ID: {enum_paths}")
    
    # 3. Try with the string type
    if not enum_paths and instrument_type is not None:
        logger.info(f"Trying with string type: {instrument_type}")
        if isinstance(param_def["enums"], dict) and instrument_type in param_def["enums"]:
            enum_paths = param_def["enums"][instrument_type]
            logger.info(f"Found enum paths with string type: {enum_paths}")
    
    # 4. Advanced lookup with helper function
    if not enum_paths:
        logger.info(f"Using helper function with {instrument_type}")
        enum_paths = get_enum_paths_for_instrument(param_def["enums"], instrument_type)
        logger.info(f"Got enum_paths: {enum_paths}")
    
    # 5. Try advanced lookup with ID if string lookup failed
    if not enum_paths and instrument_type_id is not None:
        logger.info(f"Using helper function with ID: {instrument_type_id}")
        enum_paths = get_enum_paths_for_instrument(param_def["enums"], instrument_type_id)
        logger.info(f"Got enum_paths: {enum_paths}")
    
    # 6. If all else fails, check if there's a single entry that applies to all instrument types
    if not enum_paths and isinstance(param_def["enums"], list):
        logger.info("Using generic enum paths (applies to all instruments)")
        enum_paths = param_def["enums"]
        logger.info(f"Got enum_paths: {enum_paths}")
    
    # No paths found, return original value
    if not enum_paths:
        logger.debug(f"No enum paths found, returning original value: {value}")
        return value
    
    # Load enum classes
    logger.info(f"Loading enum classes for paths: {enum_paths}")
    enum_classes = load_enum_classes(enum_paths, param_name)
    logger.info(f"Loaded enum classes: {enum_classes}")
    
    if not enum_classes:
        logger.warning(f"No enum classes found for paths: {enum_paths}")
        return value
    
    # Value is already an enum object, return its name
    if hasattr(value, 'name'):
        logger.info(f"Value is already an enum object, returning name: {value.name}")
        return value.name
    
    # Value is an integer, look up its enum name
    if isinstance(value, int):
        logger.info(f"Value is an integer: {value}, looking up enum name")
        for enum_class in enum_classes:
            try:
                enum_value = enum_class(value)
                logger.info(f"Found enum {enum_value} with name {enum_value.name}")
                return enum_value.name
            except ValueError:
                logger.info(f"Value {value} not found in enum class {enum_class.__name__}")
                continue
    
    # Couldn't convert the value, return it as-is
    logger.debug(f"Could not convert value {value} to enum name, returning as-is")
    return value

def deserialize_param_enum(enum_paths, value, param_name=None, instrument_type=None):
    """Convert parameter string enum name to numeric value."""
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
        logger.debug(f"No enum defined for instrument type {instrument_type} parameter {param_name}")
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
        logger.debug(f"No enum defined for instrument type {instrument_type}")
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

# Parameter decorator for enum string conversion
def with_enum_param(param_index=0, instrument_attr='instrument', empty_value=0xFF):
    """
    Decorator to convert string enum parameters to numeric values.
    
    Args:
        param_index: Index of the parameter to convert (default is 0, the first parameter)
        instrument_attr: Name of the attribute containing the instrument ID (default is 'instrument')
        empty_value: Value that represents an empty/invalid reference (default is 0xFF)
        
    Usage:
        @with_enum_param(param_index=0)  # Convert the first parameter (key)
        def add_fx(self, key, value):
            # key will be converted from string enum to numeric value if needed
            ...
    """
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # Convert args to list to allow modification
            args_list = list(args)
            
            # Get the parameter to convert
            if len(args_list) > param_index:
                param = args_list[param_index]
                
                # Only convert if it's a string
                if isinstance(param, str):
                    # Get instrument ID from self
                    instrument_id = getattr(self, instrument_attr, empty_value)
                    
                    # Only proceed if we have a valid instrument reference
                    if instrument_id != empty_value:
                        context = M8InstrumentContext.get_instance()
                        
                        # Use context to find appropriate enum for this instrument type
                        with context.with_referenced_context(instrument_id):
                            # Get enum classes from configuration
                            from m8.config import get_fx_keys_enum_paths
                            instrument_type_id = context.get_instrument_type_id()
                            
                            if instrument_type_id is not None:
                                # Get enum paths for this instrument type
                                enum_paths = get_fx_keys_enum_paths(instrument_type_id)
                                
                                # Load enum classes
                                enum_classes = load_enum_classes(enum_paths)
                                
                                # Try each enum class to find the key
                                for enum_class in enum_classes:
                                    try:
                                        args_list[param_index] = enum_class[param].value
                                        break
                                    except KeyError:
                                        continue
            
            # Call the original function with possibly modified args
            return func(self, *args_list, **kwargs)
        
        return wrapper
    
    return decorator

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

def with_contained_context(instrument_or_type):
    context = M8InstrumentContext.get_instance()
    return context.with_contained_context(instrument_or_type)
    
def with_referenced_context(instrument_id):
    context = M8InstrumentContext.get_instance()
    return context.with_referenced_context(instrument_id)
    
def with_phrase_step_context(step):
    context = M8InstrumentContext.get_instance()
    return context.with_phrase_step_context(step)

def with_instrument_context(obj_or_id=None):
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

# Utility functions to abstract common boilerplate patterns

def get_instrument_type_from_id(type_id):
    """Convert numeric instrument type ID to string name."""
    if type_id is None:
        return None
        
    from m8.config import get_instrument_types
    instrument_types = get_instrument_types()
    return instrument_types.get(type_id)
    
def get_instrument_type_from_context():
    """Get instrument type string from the current context."""
    context = M8InstrumentContext.get_instance()
    instrument_type_id = context.get_instrument_type_id()
    return get_instrument_type_from_id(instrument_type_id)

def get_type_id(enum_or_value):
    """Extract numeric ID from various type representations."""
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

def serialize_with_context(param_def, value, param_name=None):
    """Serialize a parameter value with automatic context handling."""
    if "enums" not in param_def:
        return value
        
    # Try with explicit instrument_type from context
    instrument_type = get_instrument_type_from_context()
    
    return serialize_param_enum_value(value, param_def, instrument_type, param_name)

def is_valid_type_id(type_id, valid_types):
    """Check if a type ID is valid."""
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