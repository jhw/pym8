from m8 import NULL
from m8.core import auto_name_decorator

import struct

class M8Array:    
    def __init__(self):
        self._data = bytearray(self.DEFAULT_DATA)

    @classmethod
    def read(cls, data):
        required_length = cls.LENGTH * struct.calcsize(cls.TYPE)
        if len(data) < required_length:
            raise ValueError(f"Data too short: got {len(data)} bytes, need {required_length}")
        
        instance = cls()
        instance._data = bytearray(data[:required_length])  # Only take the bytes we need
        return instance
                
    def clone(self):
        return self.__class__.read(bytes(self._data))

    def is_empty(self):
        default_value = struct.unpack(self.TYPE, bytes([self.DEFAULT_DATA[0]] * struct.calcsize(self.TYPE)))[0]
        return all(item == default_value for item in self.as_list())

    def __getitem__(self, index):
        if not (0 <= index < self.LENGTH):
            raise IndexError("Index out of range")
        return struct.unpack_from(self.TYPE, self._data, index * struct.calcsize(self.TYPE))[0]

    def __setitem__(self, index, value):
        if not (0 <= index < self.LENGTH):
            raise IndexError("Index out of range")
        struct.pack_into(self.TYPE, self._data, index * struct.calcsize(self.TYPE), value)

    def write(self):
        return bytes(self._data)

    def as_list(self):
        """Convert array to list for serialization"""
        return list(struct.unpack(self.TYPE * self.LENGTH, self._data))

    def as_dict(self):
        """Convert array to dict for serialization"""
        return {
            "__class__": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "values": self.as_list()
        }
        
    @classmethod
    def from_list(cls, values):
        """Create an instance from a list of values"""
        instance = cls()
        for i, value in enumerate(values):
            if i < instance.LENGTH:
                instance[i] = value
        return instance

    @classmethod
    def from_dict(cls, data):
        """Create an instance from a dictionary"""
        if "values" in data:
            return cls.from_list(data["values"])
        return cls()

    def to_json(self, indent=None):
        """Convert array to JSON string"""
        from m8.api.serialization import to_json
        return to_json(self, indent=indent)

    @classmethod
    def from_json(cls, json_str):
        """Create an instance from a JSON string"""
        from m8.api.serialization import from_json
        return from_json(json_str, cls)

@auto_name_decorator
def m8_array_class(length, fmt, name=None, default_byte=NULL):
    block_sz = length * struct.calcsize(fmt)
    default_data = bytes([default_byte] * block_sz)

    return type(name, (M8Array,), {
        "LENGTH": length,
        "TYPE": fmt,
        "DEFAULT_DATA": default_data,
    })
