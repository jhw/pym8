from m8.core.format import load_format_config

# Load configuration
config = load_format_config()["chains"]

# Module-level constants for block sizes and counts
STEP_BLOCK_SIZE = config["step_size"]
STEP_COUNT = config["step_count"]
CHAIN_BLOCK_SIZE = STEP_COUNT * STEP_BLOCK_SIZE  # Total chain size in bytes
CHAIN_COUNT = config["count"]

class M8ChainStep:
    """Represents a single step in an M8 chain that references a phrase with transposition."""
    
    PHRASE_OFFSET = config["fields"]["phrase"]["offset"]
    TRANSPOSE_OFFSET = config["fields"]["transpose"]["offset"]
    EMPTY_PHRASE = config["constants"]["empty_phrase"]
    DEFAULT_TRANSPOSE = config["constants"]["default_transpose"]
    
    def __init__(self, phrase=EMPTY_PHRASE, transpose=DEFAULT_TRANSPOSE):
        self._data = bytearray([phrase, transpose])
    
    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)  # Create instance without calling __init__
        instance._data = bytearray(data[:STEP_BLOCK_SIZE])
        return instance
    
    def write(self):
        return bytes(self._data)
    
    @property
    def phrase(self):
        return self._data[self.PHRASE_OFFSET]
    
    @phrase.setter
    def phrase(self, value):
        self._data[self.PHRASE_OFFSET] = value
    
    @property
    def transpose(self):
        return self._data[self.TRANSPOSE_OFFSET]
    
    @transpose.setter
    def transpose(self, value):
        self._data[self.TRANSPOSE_OFFSET] = value
    
    def clone(self):
        return self.__class__(
            phrase=self.phrase,
            transpose=self.transpose
        )

class M8Chain(list):
    """A sequence of up to 16 chain steps for sequencing and transposing phrases."""
    
    def __init__(self):
        super().__init__()
        # Initialize with empty steps
        for _ in range(STEP_COUNT):
            self.append(M8ChainStep())
    
    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)  # Create instance without calling __init__
        list.__init__(instance)  # Initialize the list properly
        
        for i in range(STEP_COUNT):
            start = i * STEP_BLOCK_SIZE
            row_data = data[start:start + STEP_BLOCK_SIZE]
            instance.append(M8ChainStep.read(row_data))
        
        return instance
    
    def clone(self):
        instance = self.__class__()
        instance.clear()  # Remove default items
        
        for step in self:
            instance.append(step.clone())
        
        return instance
    
    def write(self):
        result = bytearray()
        for step in self:
            step_data = step.write()
            result.extend(step_data)
        return bytes(result)

class M8Chains(list):
    """Collection of up to 255 chains for song composition in the M8 tracker."""
    
    def __init__(self):
        super().__init__()
        # Initialize with empty chains
        for _ in range(CHAIN_COUNT):
            self.append(M8Chain())
    
    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)  # Create instance without calling __init__
        list.__init__(instance)  # Initialize the list properly
        
        for i in range(CHAIN_COUNT):
            start = i * CHAIN_BLOCK_SIZE
            chain_data = data[start:start + CHAIN_BLOCK_SIZE]
            instance.append(M8Chain.read(chain_data))
        
        return instance
    
    def clone(self):
        instance = self.__class__.__new__(self.__class__)  # Create without __init__
        list.__init__(instance)  # Initialize list directly
        
        for chain in self:
            instance.append(chain.clone())
        
        return instance
    
    def write(self):
        result = bytearray()
        for chain in self:
            chain_data = chain.write()
            result.extend(chain_data)
        return bytes(result)
