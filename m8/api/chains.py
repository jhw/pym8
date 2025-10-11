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
    
    def is_empty(self):
        """Check if this chain step is empty.
        
        Uses a lenient approach that only checks if the phrase reference equals
        the M8 empty phrase value (0xFF). This maintains consistency with other
        emptiness checks throughout the codebase and follows the M8's concept of emptiness.
        """
        return self.phrase == self.EMPTY_PHRASE
    
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
    
    def as_dict(self):
        return {
            "phrase": self.phrase,
            "transpose": self.transpose
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            phrase=data["phrase"],
            transpose=data["transpose"]
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
    
    def is_empty(self):
        """Check if this chain is empty.
        
        A chain is considered empty if all of its steps are empty.
        This lenient approach delegates to each step's is_empty() method,
        maintaining consistency in emptiness definitions throughout the codebase.
        """
        return all(step.is_empty() for step in self)
    
    def write(self):
        result = bytearray()
        for step in self:
            step_data = step.write()
            result.extend(step_data)
        return bytes(result)
    
    @property
    def available_step_slot(self):
        for slot_idx, step in enumerate(self):
            if step.phrase == M8ChainStep.EMPTY_PHRASE:  # Empty step has 0xFF phrase
                return slot_idx
        return None
        
    def add_step(self, step):
        slot = self.available_step_slot
        if slot is None:
            raise IndexError("No empty step slots available in this chain")
            
        self[slot] = step
        return slot
        
    def set_step(self, step, slot):
        if not (0 <= slot < len(self)):
            raise IndexError(f"Step slot index must be between 0 and {len(self)-1}")
            
        self[slot] = step
            
    def as_dict(self):
        steps = []
        for i, step in enumerate(self):
            if not step.is_empty():
                step_dict = step.as_dict()
                # Add index to track position
                step_dict["index"] = i
                steps.append(step_dict)
        
        return {
            "steps": steps
        }
        
    @classmethod
    def from_dict(cls, data):
        instance = cls()
        instance.clear()  # Clear default steps
        
        # Initialize with empty steps
        for _ in range(STEP_COUNT):
            instance.append(M8ChainStep())
        
        # Add steps from dict
        if "steps" in data:
            for step_data in data["steps"]:
                # Get index from data or default to 0
                index = step_data.get("index", 0)
                if 0 <= index < STEP_COUNT:
                    # Remove index field before passing to from_dict
                    step_dict = {k: v for k, v in step_data.items() if k != "index"}
                    instance[index] = M8ChainStep.from_dict(step_dict)
        
        return instance

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
    
    def is_empty(self):
        return all(chain.is_empty() for chain in self)
    
    def write(self):
        result = bytearray()
        for chain in self:
            chain_data = chain.write()
            result.extend(chain_data)
        return bytes(result)
    
    def as_list(self):
        # Only include non-empty chains with position indices
        items = []
        for i, chain in enumerate(self):
            if not chain.is_empty():
                chain_dict = chain.as_dict()
                # Add index to track position
                chain_dict["index"] = i
                items.append(chain_dict)
        
        return items
    
    @classmethod
    def from_list(cls, items):
        instance = cls.__new__(cls)  # Create without __init__
        list.__init__(instance)  # Initialize list directly
        
        # Initialize full list with empty chains
        for _ in range(CHAIN_COUNT):
            instance.append(M8Chain())
        
        # Add chains from list
        if items:
            for chain_data in items:
                # Get index from data or default to 0
                index = chain_data.get("index", 0)
                if 0 <= index < CHAIN_COUNT:
                    # Remove index field before passing to from_dict
                    chain_dict = {k: v for k, v in chain_data.items() if k != "index"}
                    instance[index] = M8Chain.from_dict(chain_dict)
        
        return instance
