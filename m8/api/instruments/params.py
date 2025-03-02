class M8ParamsBase:
    """Base class for instrument parameter groups."""
    
    def __init__(self, param_defs, offset, **kwargs):
        """
        Initialize the parameter group.
        
        Args:
            param_defs: List of (name, default) tuples defining the parameters
            offset: Byte offset where these parameters start in binary data
            **kwargs: Parameter values to set
        """
        # Store the offset
        self.offset = offset
        
        # Initialize parameters with defaults
        for name, default in param_defs:
            setattr(self, name, default)
        
        # Apply any kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def read(cls, data, offset=None):
        """Read parameters from binary data starting at a specific offset"""
        # Create an instance with default values
        instance = cls(offset=offset)
        
        # Read values from appropriate offsets
        for i, (name, _) in enumerate(instance._param_defs):
            setattr(instance, name, data[offset + i])
        
        return instance
    
    def write(self):
        """Write parameters to binary data"""
        buffer = bytearray()
        for name, _ in self._param_defs:
            buffer.append(getattr(self, name))
        return bytes(buffer)
    
    def clone(self):
        """Create a copy of this parameter object"""
        instance = self.__class__(offset=self.offset)
        for name, _ in self._param_defs:
            setattr(instance, name, getattr(self, name))
        return instance
    
    def as_dict(self):
        """Convert parameters to dictionary for serialization"""
        return {name: getattr(self, name) for name, _ in self._param_defs}
    
    @classmethod
    def from_dict(cls, data, offset=None):
        """Create parameters from a dictionary"""
        instance = cls(offset=offset)
        
        for name, _ in instance._param_defs:
            if name in data:
                setattr(instance, name, data[name])
            
        return instance
        
class M8FilterParams(M8ParamsBase):
    """Class to handle filter parameters shared by multiple instrument types."""
    
    _param_defs = [
        ("type", 0x0),
        ("cutoff", 0xFF),
        ("resonance", 0x0)
    ]
    
    def __init__(self, offset, **kwargs):
        super().__init__(self._param_defs, offset, **kwargs)

class M8AmpParams(M8ParamsBase):
    """Class to handle amp parameters shared by multiple instrument types."""
    
    _param_defs = [
        ("level", 0x0),
        ("limit", 0x0)
    ]
    
    def __init__(self, offset, **kwargs):
        super().__init__(self._param_defs, offset, **kwargs)

class M8MixerParams(M8ParamsBase):
    """Class to handle mixer parameters shared by multiple instrument types."""
    
    _param_defs = [
        ("pan", 0x80),
        ("dry", 0xC0),
        ("chorus", 0x0),
        ("delay", 0x0),
        ("reverb", 0x0)
    ]
    
    def __init__(self, offset, **kwargs):
        super().__init__(self._param_defs, offset, **kwargs)

