import logging

# Re-export utility functions
from m8.core.utils.bit_utils import (
    split_byte, join_nibbles, get_bits, set_bits
)
from m8.core.utils.string_utils import (
    read_fixed_string, write_fixed_string
)
from m8.core.utils.json_utils import (
    M8JSONEncoder, m8_json_decoder, json_dumps, json_loads
)
from m8.core.enums import (
    serialize_enum, deserialize_enum,
    get_enum_paths_for_instrument, load_enum_classes,
    serialize_param_enum_value, deserialize_param_enum,
    ensure_enum_int_value, clear_enum_cache
)

# exceptions
    
# ValueError removed in favor of ValidationResult approach

class M8ValidationResult:
    """Container for validation results with hierarchical error tracking."""
    
    def __init__(self, context=None):
        self.context = context or "root"
        self.errors = []
        self.valid = True
    
    def add_error(self, message, component=None):
        """Add a validation error with optional component path."""
        path = f"{self.context}.{component}" if component else self.context
        self.errors.append(f"{path}: {message}")
        self.valid = False
        return self
    
    def merge(self, other_result, component=None):
        """Merge another validation result into this one."""
        if not other_result.valid:
            self.valid = False
            
            # Add errors from other result with updated context
            for error in other_result.errors:
                if component:
                    error = error.replace(other_result.context, f"{self.context}.{component}")
                self.errors.append(error)
        
        return self
    
    def raise_if_invalid(self):
        """Raise ValueError if validation failed."""
        if not self.valid:
            error_message = "\n".join(self.errors)
            raise ValueError(error_message)
    
    def log_errors(self, logger=None):
        """Log all validation errors."""
        if not self.valid and logger:
            for error in self.errors:
                logger.error(error)

class M8UnknownTypeError(Exception):
    """Exception raised when an unknown instrument or modulator type is encountered."""
    pass



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