import logging

# Re-export utility functions
from m8.utils.string_utils import (
    read_fixed_string, write_fixed_string
)
from m8.utils.json_utils import (
    M8JSONEncoder, m8_json_decoder, json_dumps, json_loads
)


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

