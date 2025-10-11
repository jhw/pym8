from m8.config import load_format_config

# Load configuration
config = load_format_config()["fx"]

# Module-level constants
BLOCK_SIZE = config["block_size"]
BLOCK_COUNT = config["block_count"]

# Hardcoded FX keys for supported effects
FX_PITCH = 0x03         # PIT command (pitch)
FX_NOTE_LENGTH = 0x07   # NTH command (note length)
FX_RETRIGGER = 0x0C     # RTG command (repeat/retrigger)
FX_PLAY_MODE = 0x83     # PLY command (play mode)

class M8FXTuple:
    """Key-value pair for M8 effects with key (effect type) and value (effect parameter)."""
    
    KEY_OFFSET = config["fields"]["key"]["offset"]
    VALUE_OFFSET = config["fields"]["value"]["offset"]
    EMPTY_KEY = config["constants"]["empty_key"]
    DEFAULT_VALUE = config["constants"]["default_value"]
    
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
    
    def is_empty(self):
        """Check if this FX tuple is empty."""
        return self._data[self.KEY_OFFSET] == self.EMPTY_KEY
        
    def is_complete(self):
        """Check if this FX tuple is complete."""
        return self._data[self.KEY_OFFSET] != self.EMPTY_KEY
    
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
    
    def as_dict(self):
        return {
            "key": self.key,
            "value": self.value
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            key=data["key"],
            value=data["value"]
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
    
    def is_empty(self):
        return all(fx_tuple.is_empty() for fx_tuple in self)
        
    def is_complete(self):
        """Check if all non-empty FX tuples are complete."""
        if self.is_empty():
            return True
            
        # For each tuple, either it's empty or it's complete
        return all(fx_tuple.is_empty() or fx_tuple.is_complete() for fx_tuple in self)
    
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
                # Get index from data
                index = tuple_data["index"]
                if 0 <= index < BLOCK_COUNT:
                    # Remove index field before passing to from_dict
                    tuple_dict = {k: v for k, v in tuple_data.items() if k != "index"}
                    instance[index] = M8FXTuple.from_dict(tuple_dict)
        
        return instance