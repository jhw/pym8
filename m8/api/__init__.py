import json

# exceptions
    
class M8ValidationError(Exception):
    pass

class M8IndexError(IndexError):
    pass

# default class

class M8Block:
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
        """Convert block to dictionary for serialization"""
        return {
            "data": list(self.data)
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create an instance from a dictionary"""
        instance = cls()
        if "data" in data:
            instance.data = bytearray(data["data"])
        return instance

# dynamic classes

def load_class(class_path):
    module_name, class_name = class_path.rsplit('.', 1)
    module = __import__(module_name, fromlist=[class_name])
    return getattr(module, class_name)

# bit twiddling

def split_byte(byte):
    upper = (byte >> 4) & 0x0F
    lower = byte & 0x0F
    return upper, lower

def join_nibbles(upper, lower):
    return ((upper & 0x0F) << 4) | (lower & 0x0F)

def get_bits(value, start, length=1):
    mask = (1 << length) - 1
    return (value >> start) & mask

def set_bits(value, bits, start, length=1):
    mask = ((1 << length) - 1) << start
    return (value & ~mask) | ((bits & ((1 << length) - 1)) << start)

# serialisation

def json_dumps(obj, indent = 2):
    return json.dumps(obj, indent = indent)

def json_loads(json_str):
    return json.loads(json_str)
