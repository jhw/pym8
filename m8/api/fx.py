from m8.api import M8ValidationError

BLOCK_SIZE = 2
BLOCK_COUNT = 3

class M8FXTuple:
    def __init__(self, key=0xFF, value=0x0):
        self._data = bytearray([key, value])
    
    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)  # Create instance without calling __init__
        instance._data = bytearray(data[:BLOCK_SIZE])
        return instance
    
    def write(self):
        return bytes(self._data)
    
    def is_empty(self):
        return self.key == 0xFF
    
    @property
    def key(self):
        return self._data[0]
    
    @key.setter
    def key(self, value):
        self._data[0] = value
    
    @property
    def value(self):
        return self._data[1]
    
    @value.setter
    def value(self, value):
        self._data[1] = value
    
    def as_dict(self):
        """Convert FX tuple to dictionary for serialization"""
        return {
            "key": self.key,
            "value": self.value
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create an FX tuple from a dictionary"""
        return cls(
            key=data.get("key", 0xFF),
            value=data.get("value", 0x0)
        )    


class M8FXTuples(list):
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
        """Convert FX tuples to list for serialization"""
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
        """Create FX tuples from a list"""
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
    
