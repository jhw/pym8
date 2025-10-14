# FX configuration
FX_BLOCK_SIZE = 2
FX_BLOCK_COUNT = 3

# Field offsets within FX tuple
FX_KEY_OFFSET = 0
FX_VALUE_OFFSET = 1

# Constants
EMPTY_KEY = 255
DEFAULT_VALUE = 0

# Module-level constants
BLOCK_SIZE = FX_BLOCK_SIZE
BLOCK_COUNT = FX_BLOCK_COUNT

# Hardcoded FX keys for supported effects
FX_PITCH = 0x03         # PIT command (pitch)
FX_LENGTH = 0x86        # LEN command (sample length)
FX_RETRIGGER = 0x08     # RET command (retrigger)
FX_PLAY_MODE = 0x83     # PLY command (play mode)

class M8FXTuple:
    """Key-value pair for M8 effects with key (effect type) and value (effect parameter)."""

    KEY_OFFSET = FX_KEY_OFFSET
    VALUE_OFFSET = FX_VALUE_OFFSET
    EMPTY_KEY = EMPTY_KEY
    DEFAULT_VALUE = DEFAULT_VALUE
    
    def __init__(self, key=EMPTY_KEY, value=DEFAULT_VALUE):
        self._data = bytearray([0, 0])  # Initialize with zeros
        
        # Set values directly - clients should pass enum.value for enum keys
        self._data[self.KEY_OFFSET] = key
        self._data[self.VALUE_OFFSET] = value
    
    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)  # Create instance without calling __init__
        instance._data = bytearray(data[:BLOCK_SIZE])
        return instance
    
    def write(self):
        return bytes(self._data)
    
    @property
    def key(self):
        return self._data[self.KEY_OFFSET]
    
    @key.setter
    def key(self, value):
        self._data[self.KEY_OFFSET] = value
    
    @property
    def value(self):
        return self._data[self.VALUE_OFFSET]
    
    @value.setter
    def value(self, value):
        self._data[self.VALUE_OFFSET] = value
    
    def clone(self):
        """Create a copy of this FX tuple."""
        return self.__class__(
            key=self.key,
            value=self.value
        )


class M8FXTuples(list):
    """Collection of effect settings that can be applied to phrases, instruments, and chains."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize with empty FX tuples
        for _ in range(BLOCK_COUNT):
            self.append(M8FXTuple())
    
    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)  # Create instance without calling __init__
        list.__init__(instance)  # Initialize the list properly
        
        for i in range(BLOCK_COUNT):
            start = i * BLOCK_SIZE
            tuple_data = data[start:start + BLOCK_SIZE]
            instance.append(M8FXTuple.read(tuple_data))
        
        return instance
    
    def clone(self):
        instance = self.__class__()
        instance.clear()  # Remove default items
        
        for fx_tuple in self:
            if hasattr(fx_tuple, 'clone'):
                instance.append(fx_tuple.clone())
            else:
                cloned_tuple = M8FXTuple.read(fx_tuple.write())
                instance.append(cloned_tuple)
        
        return instance
    
    def write(self):
        result = bytearray()
        for fx_tuple in self:
            tuple_data = fx_tuple.write()
            result.extend(tuple_data)
        return bytes(result)