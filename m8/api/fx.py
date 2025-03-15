from m8.api import M8ValidationError

# Module-level constants
BLOCK_SIZE = 2
BLOCK_COUNT = 3

class M8FXTuple:
    """Represents a key-value pair for M8 effects.
    
    Each FX tuple contains a key (effect type) and a value (effect parameter).
    Used to define effect settings in phrases, chains, and instruments.
    """
    
    # Class-level constants
    KEY_OFFSET = 0
    VALUE_OFFSET = 1
    EMPTY_KEY = 0xFF
    DEFAULT_VALUE = 0x0
    
    def __init__(self, key=EMPTY_KEY, value=DEFAULT_VALUE):
        """Initialize an FX tuple with key and value.
        
        Args:
            key: The FX key/type (0-254, 255=empty)
            value: The FX value/parameter (0-255)
        """
        self._data = bytearray([key, value])
    
    @classmethod
    def read(cls, data):
        """Create an FX tuple from binary data.
        
        Args:
            data: Binary data containing key and value bytes
            
        Returns:
            A new M8FXTuple instance
        """
        instance = cls.__new__(cls)  # Create instance without calling __init__
        instance._data = bytearray(data[:BLOCK_SIZE])
        return instance
    
    def write(self):
        """Convert the FX tuple to binary data.
        
        Returns:
            bytes: Binary representation of the FX tuple
        """
        return bytes(self._data)
    
    def is_empty(self):
        """Check if this FX tuple is empty (has EMPTY_KEY).
        
        Returns:
            bool: True if the FX tuple is empty, False otherwise
        """
        return self.key == self.EMPTY_KEY
    
    @property
    def key(self):
        """Get the effect key/type.
        
        Returns:
            int: The effect key (0-255)
        """
        return self._data[self.KEY_OFFSET]
    
    @key.setter
    def key(self, value):
        """Set the effect key/type.
        
        Args:
            value: The new effect key (0-255)
        """
        self._data[self.KEY_OFFSET] = value
    
    @property
    def value(self):
        """Get the effect value/parameter.
        
        Returns:
            int: The effect value (0-255)
        """
        return self._data[self.VALUE_OFFSET]
    
    @value.setter
    def value(self, value):
        """Set the effect value/parameter.
        
        Args:
            value: The new effect value (0-255)
        """
        self._data[self.VALUE_OFFSET] = value
    
    def as_dict(self):
        """Convert FX tuple to dictionary for serialization.
        
        Returns:
            dict: Dictionary with key and value fields
        """
        return {
            "key": self.key,
            "value": self.value
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create an FX tuple from a dictionary.
        
        Args:
            data: Dictionary containing key and value entries
            
        Returns:
            M8FXTuple: New instance with the specified key and value
        """
        return cls(
            key=data.get("key", cls.EMPTY_KEY),
            value=data.get("value", cls.DEFAULT_VALUE)
        )    


class M8FXTuples(list):
    """A collection of M8FXTuple objects.
    
    Represents a set of effects that can be applied to a phrase step, instrument, chain, etc.
    Extends the built-in list type with M8-specific functionality.
    """
    
    def __init__(self):
        """Initialize a collection with empty FX tuples."""
        super().__init__()
        # Initialize with empty FX tuples
        for _ in range(BLOCK_COUNT):
            self.append(M8FXTuple())
    
    @classmethod
    def read(cls, data):
        """Create FX tuples collection from binary data.
        
        Args:
            data: Binary data containing multiple FX tuples
            
        Returns:
            M8FXTuples: New collection of FX tuples
        """
        instance = cls.__new__(cls)  # Create instance without calling __init__
        list.__init__(instance)  # Initialize the list properly
        
        for i in range(BLOCK_COUNT):
            start = i * BLOCK_SIZE
            tuple_data = data[start:start + BLOCK_SIZE]
            instance.append(M8FXTuple.read(tuple_data))
        
        return instance
    
    def clone(self):
        """Create a deep copy of this FX tuples collection.
        
        Returns:
            M8FXTuples: New collection with the same values
        """
        instance = self.__class__()
        instance.clear()  # Remove default items
        
        for fx_tuple in self:
            if hasattr(fx_tuple, 'clone'):
                instance.append(fx_tuple.clone())
            else:
                instance.append(M8FXTuple.read(fx_tuple.write()))
        
        return instance
    
    def is_empty(self):
        """Check if all FX tuples in the collection are empty.
        
        Returns:
            bool: True if all tuples are empty, False otherwise
        """
        return all(fx_tuple.is_empty() for fx_tuple in self)
    
    def write(self):
        """Convert all FX tuples to binary data.
        
        Returns:
            bytes: Binary representation of all FX tuples
        """
        result = bytearray()
        for fx_tuple in self:
            tuple_data = fx_tuple.write()
            result.extend(tuple_data)
        return bytes(result)
    
    def as_list(self):
        """Convert FX tuples to list for serialization.
        
        Only includes non-empty tuples with their position index.
        
        Returns:
            list: List of dictionaries with key, value, and index fields
        """
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
        """Create FX tuples from a list of dictionaries.
        
        Args:
            items: List of dictionaries with key, value, and index fields
            
        Returns:
            M8FXTuples: New collection with FX tuples at their specified positions
        """
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
