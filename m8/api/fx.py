from m8.api import M8ValidationError

# Module-level constants
BLOCK_SIZE = 2
BLOCK_COUNT = 3

class M8FXTuple:
    """Key-value pair for M8 effects with key (effect type) and value (effect parameter)."""
    
    KEY_OFFSET = 0
    VALUE_OFFSET = 1
    EMPTY_KEY = 0xFF
    DEFAULT_VALUE = 0x0
    
    def __init__(self, key=EMPTY_KEY, value=DEFAULT_VALUE):
        self._data = bytearray([key, value])
    
    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)  # Create instance without calling __init__
        instance._data = bytearray(data[:BLOCK_SIZE])
        return instance
    
    def write(self):
        return bytes(self._data)
    
    def is_empty(self):
        return self.key == self.EMPTY_KEY
    
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
    
    def as_dict(self):
        return {
            "key": self.key,
            "value": self.value
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            key=data.get("key", cls.EMPTY_KEY),
            value=data.get("value", cls.DEFAULT_VALUE)
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
                instance.append(M8FXTuple.read(fx_tuple.write()))
        
        return instance
    
    def is_empty(self):
        return all(fx_tuple.is_empty() for fx_tuple in self)
    
    def write(self):
        result = bytearray()
        for fx_tuple in self:
            tuple_data = fx_tuple.write()
            result.extend(tuple_data)
        return bytes(result)
    
    def as_list(self):
        # Only include non-empty tuples with their position index
        tuples = []
        for i, fx_tuple in enumerate(self):
            if not fx_tuple.is_empty():
                tuple_dict = fx_tuple.as_dict()
                # Add index to track position
                tuple_dict["index"] = i
                tuples.append(tuple_dict)
        
        return tuples
        
    @classmethod
    def from_list(cls, items):
        instance = cls()
        instance.clear()  # Clear default tuples
        
        # Initialize with empty tuples
        for _ in range(BLOCK_COUNT):
            instance.append(M8FXTuple())
        
        # Set tuples at their original positions
        if items:
            for tuple_data in items:
                # Get index from data or default to 0
                index = tuple_data.get("index", 0)
                if 0 <= index < BLOCK_COUNT:
                    # Remove index field before passing to from_dict
                    tuple_dict = {k: v for k, v in tuple_data.items() if k != "index"}
                    instance[index] = M8FXTuple.from_dict(tuple_dict)
        
        return instance
