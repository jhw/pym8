from enum import Enum, auto

class M8ParamType(Enum):
    UINT8 = auto()      # Standard 1-byte integer (0-255)
    STRING = auto()     # String type with variable length

class M8ParamsBase:
    """Base class for instrument parameter groups with support for different parameter types."""
    
    @staticmethod
    def calculate_parameter_size(param_defs):
        """Calculate the total size in bytes of all parameters"""
        total_size = 0
        for param_def in param_defs:
            param_type = param_def[2]
            if param_type == M8ParamType.UINT8:
                total_size += 1
            elif param_type == M8ParamType.STRING:
                total_size += param_def[3]  # String length
        return total_size
    
    def __init__(self, param_defs, offset, **kwargs):
        """
        Initialize the parameter group.
        
        Args:
            param_defs: List of tuples defining the parameters with format:
                For UINT8: (name, default, M8ParamType.UINT8)
                For STRING: (name, default, M8ParamType.STRING, length)
            offset: Byte offset where these parameters start in binary data
            **kwargs: Parameter values to set
        """
        # Store the offset
        self.offset = offset
        
        # Initialize parameters with defaults
        for param_def in param_defs:
            name, default = param_def[0], param_def[1]
            setattr(self, name, default)
        
        # Apply any kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def read(cls, data, offset):
        """Read parameters from binary data starting at a specific offset"""
        # Create an instance with default values
        instance = cls(offset=offset)
        
        current_offset = offset
        
        # Read values from appropriate offsets
        for param_def in instance._param_defs:
            name, _, param_type, *param_args = param_def
            
            if param_type == M8ParamType.UINT8:
                # Read a single byte
                value = data[current_offset]
                current_offset += 1
            elif param_type == M8ParamType.STRING:
                # Read a string of specified length
                string_length = param_args[0]
                string_bytes = data[current_offset:current_offset + string_length]
                
                # Convert to string, stopping at null terminator if present
                null_pos = string_bytes.find(0)
                if null_pos != -1:
                    string_bytes = string_bytes[:null_pos]
                
                value = string_bytes.decode('utf-8', errors='replace')
                current_offset += string_length
            else:
                # Default to UINT8 for unknown types
                value = data[current_offset]
                current_offset += 1
                
            setattr(instance, name, value)
        
        return instance
    
    def write(self):
        """Write parameters to binary data"""
        buffer = bytearray()
        
        for param_def in self._param_defs:
            name, _, param_type, *param_args = param_def
            value = getattr(self, name)
            
            if param_type == M8ParamType.UINT8:
                # Write a single byte
                buffer.append(value & 0xFF)
            elif param_type == M8ParamType.STRING:
                # Write a string of specified length
                string_length = param_args[0]
                
                # Convert to bytes, pad with nulls
                if isinstance(value, str):
                    encoded = value.encode('utf-8')
                    # Truncate or pad to exactly string_length bytes
                    if len(encoded) > string_length:
                        encoded = encoded[:string_length]
                    else:
                        encoded = encoded + bytes([0] * (string_length - len(encoded)))
                    
                    buffer.extend(encoded)
                else:
                    # Handle non-string values by padding with nulls
                    buffer.extend(bytes([0] * string_length))
            else:
                # Default to UINT8 for unknown types
                buffer.append(value & 0xFF)
        
        return bytes(buffer)
    
    def clone(self):
        """Create a copy of this parameter object"""
        instance = self.__class__(offset=self.offset)
        for param_def in self._param_defs:
            name = param_def[0]
            setattr(instance, name, getattr(self, name))
        return instance
    
    def as_dict(self):
        """Convert parameters to dictionary for serialization"""
        return {param_def[0]: getattr(self, param_def[0]) for param_def in self._param_defs}
    
    @classmethod
    def from_dict(cls, data, offset):
        """Create parameters from a dictionary"""
        instance = cls(offset=offset)
        
        for param_def in instance._param_defs:
            name = param_def[0]
            if name in data:
                setattr(instance, name, data[name])
            
        return instance
        
class M8FilterParams(M8ParamsBase):
    """Class to handle filter parameters shared by multiple instrument types."""
    
    _param_defs = [
        ("type", 0x0, M8ParamType.UINT8),
        ("cutoff", 0xFF, M8ParamType.UINT8),
        ("resonance", 0x0, M8ParamType.UINT8)
    ]
    
    def __init__(self, offset, **kwargs):
        super().__init__(self._param_defs, offset, **kwargs)

class M8AmpParams(M8ParamsBase):
    """Class to handle amp parameters shared by multiple instrument types."""
    
    _param_defs = [
        ("level", 0x0, M8ParamType.UINT8),
        ("limit", 0x0, M8ParamType.UINT8)
    ]
    
    def __init__(self, offset, **kwargs):
        super().__init__(self._param_defs, offset, **kwargs)

class M8MixerParams(M8ParamsBase):
    """Class to handle mixer parameters shared by multiple instrument types."""
    
    _param_defs = [
        ("pan", 0x80, M8ParamType.UINT8),
        ("dry", 0xC0, M8ParamType.UINT8),
        ("chorus", 0x0, M8ParamType.UINT8),
        ("delay", 0x0, M8ParamType.UINT8),
        ("reverb", 0x0, M8ParamType.UINT8)
    ]
    
    def __init__(self, offset, **kwargs):
        super().__init__(self._param_defs, offset, **kwargs)

