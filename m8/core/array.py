from m8 import M8Block, NULL
from m8.core import m8_class_name

import struct

class M8Array:    
    def __init__(self):
        self._data = bytearray(self.DEFAULT_DATA)

    @classmethod
    def read(cls, data):
        instance = cls()
        instance._data = bytearray(data)
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
        return list(struct.unpack(self.TYPE * self.LENGTH, self._data))

def m8_array_class(length, fmt, default=NULL):
    name = m8_class_name("M8Array")
    block_sz = length * struct.calcsize(fmt)
    default_data = bytes([default] * block_sz)

    return type(name, (M8Array,), {
        "LENGTH": length,
        "TYPE": fmt,
        "DEFAULT_DATA": default_data,
    })


