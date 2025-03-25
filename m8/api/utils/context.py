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
    2. (Future) Providing instrument type context for FX enum serialization
    """
    
    _instance = None  # Singleton instance
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance of the context manager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
        
    def __init__(self):
        """Initialize a new instrument context manager.
        
        Note: This should rarely be called directly. Instead, use get_instance().
        """
        self.project = None
        self.current_instrument_id = None
        self.current_instrument_type = None
        
    def set_project(self, project):
        """Set the current project context."""
        self.project = project
        
    def get_instrument_type(self, instrument_id=None):
        """Get instrument type for a given instrument ID or the current instrument.
        
        Args:
            instrument_id: Optional ID to look up. If not provided, uses current context.
            
        Returns:
            The instrument type string or None if not available.
        """
        # If explicit instrument ID is provided, look it up
        if instrument_id is not None:
            if self.project and 0 <= instrument_id < len(self.project.instruments):
                instrument = self.project.instruments[instrument_id]
                return getattr(instrument, 'instrument_type', None)
        # Otherwise use current context
        elif self.current_instrument_type is not None:
            return self.current_instrument_type
        elif self.current_instrument_id is not None:
            if self.project and 0 <= self.current_instrument_id < len(self.project.instruments):
                instrument = self.project.instruments[self.current_instrument_id]
                return getattr(instrument, 'instrument_type', None)
        return None
        
    def with_instrument(self, instrument_id=None, instrument_type=None):
        """Create a context block for operations with a specific instrument.
        
        Args:
            instrument_id: Optional instrument ID to use in the context block
            instrument_type: Optional explicit instrument type to use
            
        Returns:
            A context manager block that sets the instrument context
        """
        return _InstrumentContextBlock(self, instrument_id, instrument_type)
        
    def clear(self):
        """Clear all context state."""
        self.project = None
        self.current_instrument_id = None
        self.current_instrument_type = None

class _InstrumentContextBlock:
    """Context block for instrument operations."""
    
    def __init__(self, manager, instrument_id=None, instrument_type=None):
        """Initialize a context block.
        
        Args:
            manager: The parent context manager
            instrument_id: Optional instrument ID to set during the block
            instrument_type: Optional explicit instrument type to use
        """
        self.manager = manager
        self.instrument_id = instrument_id
        self.instrument_type = instrument_type
        self.previous_id = None
        self.previous_type = None
        
    def __enter__(self):
        """Enter the context block, setting instrument context."""
        self.previous_id = self.manager.current_instrument_id
        self.previous_type = self.manager.current_instrument_type
        
        # Only update the ID/type if they were explicitly provided
        if self.instrument_id is not None:
            self.manager.current_instrument_id = self.instrument_id
        
        if self.instrument_type is not None:
            self.manager.current_instrument_type = self.instrument_type
        
        return self.manager
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context block, restoring previous context."""
        self.manager.current_instrument_id = self.previous_id
        self.manager.current_instrument_type = self.previous_type