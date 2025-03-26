"""
Context manager for tracking relationships between objects in the M8 codebase.

Currently, this module provides an instrument context manager that tracks the
current instrument and project context for operations that need to know which 
instrument they're related to, particularly for enum resolution.
"""

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