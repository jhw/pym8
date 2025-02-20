### classes

class M8ValidationError(Exception):
    """Exception raised for M8 project validation errors"""
    pass

class M8Block:
    def __init__(self):
        self.data = bytearray()

    @classmethod
    def read(cls, data):
        instance = cls()
        instance.data = data
        return instance

    def is_empty(self):
        return all(b == 0x00 for b in self.data)
    
    def write(self):
        return self.data

### naming

_m8_class_counter = 0

def m8_class_name(prefix="M8"):
    global _m8_class_counter
    _m8_class_counter += 1
    return f"{prefix}_{_m8_class_counter}"
    
### byte operations
    
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
