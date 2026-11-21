from m8.api.fields import ByteField, M8FixedList, M8Record, iter_fields, repr_slots, repr_steps

# Chains configuration
CHAINS_OFFSET = 39518
CHAINS_COUNT = 255
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

class M8ChainStep(M8Record):
    """Represents a single step in an M8 chain that references a phrase with transposition."""

    BYTES = STEP_BLOCK_SIZE

    phrase    = ByteField(PHRASE_OFFSET, default=EMPTY_PHRASE)
    transpose = ByteField(TRANSPOSE_OFFSET, default=DEFAULT_TRANSPOSE)

    def __init__(self, **kwargs):
        self._data = bytearray(self.BYTES)
        for _, fld in iter_fields(type(self)):
            fld.apply_default(self)
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)
        instance._data = bytearray(data[:cls.BYTES])
        return instance

    def write(self):
        return bytes(self._data)

    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        instance._data = bytearray(self._data)
        return instance

    def is_empty(self):
        return self.phrase == EMPTY_PHRASE

class M8Chain(M8FixedList):
    """A sequence of up to 16 chain steps for sequencing and transposing phrases."""

    CLEAR_HINT = "assign M8ChainStep() to a step to clear it"
    
    def __init__(self):
        super().__init__()
        # Initialize with empty steps
        for _ in range(STEP_COUNT):
            list.append(self, M8ChainStep())
    
    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)  # Create instance without calling __init__
        list.__init__(instance)  # Initialize the list properly
        
        for i in range(STEP_COUNT):
            start = i * STEP_BLOCK_SIZE
            row_data = data[start:start + STEP_BLOCK_SIZE]
            list.append(instance, M8ChainStep.read(row_data))
        
        return instance
    
    def clone(self):
        instance = self.__class__()
        list.clear(instance)  # Remove default items
        
        for step in self:
            list.append(instance, step.clone())
        
        return instance
    
    def write(self):
        result = bytearray()
        for step in self:
            step_data = step.write()
            result.extend(step_data)
        return bytes(result)

    def is_empty(self):
        return all(step.is_empty() for step in self)

    def to_dict(self):
        return [step.to_dict() for step in self]

    @classmethod
    def from_dict(cls, items):
        instance = cls()
        for i, d in enumerate(items[:STEP_COUNT]):
            instance[i] = M8ChainStep.from_dict(d)
        return instance

    def __repr__(self):
        return repr_steps(self)

class M8Chains(M8FixedList):
    """Collection of up to 255 chains for song composition in the M8 tracker."""

    CLEAR_HINT = "assign M8Chain() to a slot to clear it"
    
    def to_dict(self):
        return [c.to_dict() for c in self]

    def __repr__(self):
        return repr_slots(self, (i for i, c in enumerate(self) if not c.is_empty()))

    def __init__(self):
        super().__init__()
        # Initialize with empty chains
        for _ in range(CHAIN_COUNT):
            list.append(self, M8Chain())
    
    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)  # Create instance without calling __init__
        list.__init__(instance)  # Initialize the list properly
        
        for i in range(CHAIN_COUNT):
            start = i * CHAIN_BLOCK_SIZE
            chain_data = data[start:start + CHAIN_BLOCK_SIZE]
            list.append(instance, M8Chain.read(chain_data))
        
        return instance
    
    def clone(self):
        instance = self.__class__()
        list.clear(instance)  # Remove default items

        for chain in self:
            list.append(instance, chain.clone())

        return instance
    
    def write(self):
        result = bytearray()
        for chain in self:
            chain_data = chain.write()
            result.extend(chain_data)
        return bytes(result)

