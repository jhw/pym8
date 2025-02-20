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
    
