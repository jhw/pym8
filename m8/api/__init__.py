import logging

# Re-export utility functions
from m8.api.utils.bit_utils import (
    split_byte, join_nibbles, get_bits, set_bits
)
from m8.api.utils.string_utils import (
    read_fixed_string, write_fixed_string
)
from m8.api.utils.json_utils import (
    M8JSONEncoder, m8_json_decoder, json_dumps, json_loads
)
from m8.api.utils.enums import (
    serialize_enum, deserialize_enum,
    get_enum_paths_for_instrument, load_enum_classes,
    serialize_param_enum_value, deserialize_param_enum,
    ensure_enum_int_value, clear_enum_cache
)

# exceptions
    
class M8ValidationError(Exception):
    """Exception for M8 data validation errors when parameters don't meet constraints."""
    pass

class M8UnknownTypeError(Exception):
    """Exception raised when an unknown instrument or modulator type is encountered."""
    pass

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

# default class

class M8Block:
    """Base class for M8 data blocks providing binary serialization functionality."""
    
    def __init__(self):
        self.data = bytearray()

    @classmethod
    def read(cls, data):
        instance = cls()
        instance.data = data
        return instance

    def is_empty(self):
        return all(b == 0x0 for b in self.data)
    
    def write(self):
        return self.data

    def as_dict(self):
        return {
            "data": list(self.data)
        }
    
    @classmethod
    def from_dict(cls, data):
        instance = cls()
        if "data" in data:
            instance.data = bytearray(data["data"])
        return instance

# dynamic classes

def load_class(class_path):
    """Dynamically load a class by its fully qualified path."""
    module_name, class_name = class_path.rsplit('.', 1)
    module = __import__(module_name, fromlist=[class_name])
    return getattr(module, class_name)