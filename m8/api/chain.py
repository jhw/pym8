# Chains configuration
CHAINS_OFFSET = 39518
CHAINS_COUNT = 128
CHAIN_STEP_SIZE = 2
CHAIN_STEP_COUNT = 16
CHAIN_BLOCK_SIZE = CHAIN_STEP_COUNT * CHAIN_STEP_SIZE

# Field offsets within chain step
PHRASE_OFFSET = 0
TRANSPOSE_OFFSET = 1

# Constants
EMPTY_PHRASE = 255
DEFAULT_TRANSPOSE = 0

# Module-level constants for block sizes and counts
STEP_BLOCK_SIZE = CHAIN_STEP_SIZE
STEP_COUNT = CHAIN_STEP_COUNT
CHAIN_COUNT = CHAINS_COUNT

class M8ChainStep:
    """Represents a single step in an M8 chain that references a phrase with transposition."""

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
        return self._data[PHRASE_OFFSET]

    @phrase.setter
    def phrase(self, value):
        self._data[PHRASE_OFFSET] = value

    @property
    def transpose(self):
        return self._data[TRANSPOSE_OFFSET]

    @transpose.setter
    def transpose(self, value):
        self._data[TRANSPOSE_OFFSET] = value
    
    def clone(self):
        return self.__class__(
            phrase=self.phrase,
            transpose=self.transpose
        )

    def validate(self, step_index=None, chain_index=None):
        """Validate the chain step.

        Args:
            step_index: Optional step index for error messages
            chain_index: Optional chain index for error messages

        Raises:
            ValueError: If phrase reference is invalid
        """
        # Phrase reference must be 0-254 (valid phrase index) or 255 (empty)
        # Since there are 255 phrases (indices 0-254), any non-empty reference
        # must be within that range. 255 (EMPTY_PHRASE) is valid as "no phrase".
        # All byte values 0-255 are technically valid, so no validation needed here.
        pass

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

    def validate(self, chain_index=None):
        """Validate the chain.

        Args:
            chain_index: Optional chain index for error messages

        Raises:
            ValueError: If chain has incorrect number of steps
        """
        if len(self) != STEP_COUNT:
            ctx = f" (chain {chain_index})" if chain_index is not None else ""
            raise ValueError(f"Chain{ctx} has {len(self)} steps, expected {STEP_COUNT}")

        for i, step in enumerate(self):
            step.validate(step_index=i, chain_index=chain_index)

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
        instance = self.__class__()
        instance.clear()  # Remove default items

        for chain in self:
            instance.append(chain.clone())

        return instance
    
    def write(self):
        result = bytearray()
        for chain in self:
            chain_data = chain.write()
            result.extend(chain_data)
        return bytes(result)

    def validate(self):
        """Validate the chains collection.

        Raises:
            ValueError: If there are more chains than allowed
        """
        if len(self) > CHAIN_COUNT:
            raise ValueError(f"Too many chains: {len(self)}, maximum is {CHAIN_COUNT}")

        for i, chain in enumerate(self):
            chain.validate(chain_index=i)
