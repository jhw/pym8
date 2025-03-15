from m8.api import M8ValidationError

# Module-level constants for block sizes and counts
STEP_BLOCK_SIZE = 2        # Size of each chain step in bytes
STEP_COUNT = 16            # Number of steps per chain
CHAIN_BLOCK_SIZE = STEP_COUNT * STEP_BLOCK_SIZE  # Total chain size in bytes
CHAIN_COUNT = 255          # Maximum number of chains

class M8ChainStep:
    """Represents a single step in an M8 chain.
    
    Each chain step references a phrase and can apply transposition to it.
    Chain steps allow phrases to be sequenced and reused in different contexts.
    """
    
    # Class-level constants for offsets and empty values
    PHRASE_OFFSET = 0
    TRANSPOSE_OFFSET = 1
    EMPTY_PHRASE = 0xFF
    DEFAULT_TRANSPOSE = 0x0
    
    def __init__(self, phrase=EMPTY_PHRASE, transpose=DEFAULT_TRANSPOSE):
        """Initialize a chain step with optional phrase reference and transpose value.
        
        Args:
            phrase: Phrase index (0-254) or EMPTY_PHRASE (255) for no phrase
            transpose: Transposition value in semitones (-128 to 127, stored as unsigned)
        """
        # Initialize _data first
        self._data = bytearray([phrase, transpose])
        # No need to set properties, data is already initialized
    
    @classmethod
    def read(cls, data):
        """Create a chain step from binary data.
        
        Args:
            data: Binary data containing a chain step
            
        Returns:
            M8ChainStep: New instance with values from the binary data
        """
        instance = cls.__new__(cls)  # Create instance without calling __init__
        instance._data = bytearray(data[:STEP_BLOCK_SIZE])
        return instance
    
    def write(self):
        """Convert the chain step to binary data.
        
        Returns:
            bytes: Binary representation of the chain step
        """
        return bytes(self._data)
    
    def is_empty(self):
        """Check if this chain step is empty (has no phrase reference).
        
        Returns:
            bool: True if the step has no phrase, False otherwise
        """
        return self.phrase == self.EMPTY_PHRASE
    
    @property
    def phrase(self):
        """Get the phrase index (0-254, 255=empty).
        
        Returns:
            int: Phrase index or EMPTY_PHRASE
        """
        return self._data[self.PHRASE_OFFSET]
    
    @phrase.setter
    def phrase(self, value):
        """Set the phrase index.
        
        Args:
            value: Phrase index (0-254) or EMPTY_PHRASE (255)
        """
        self._data[self.PHRASE_OFFSET] = value
    
    @property
    def transpose(self):
        """Get the transpose value (-128 to 127, stored as unsigned).
        
        Returns:
            int: Transpose value in semitones
        """
        return self._data[self.TRANSPOSE_OFFSET]
    
    @transpose.setter
    def transpose(self, value):
        """Set the transpose value.
        
        Args:
            value: Transpose value in semitones (-128 to 127, stored as unsigned)
        """
        self._data[self.TRANSPOSE_OFFSET] = value
    
    def as_dict(self):
        """Convert chain step to dictionary for serialization.
        
        Returns:
            dict: Dictionary representation of the chain step
        """
        return {
            "phrase": self.phrase,
            "transpose": self.transpose
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a chain step from a dictionary.
        
        Args:
            data: Dictionary containing chain step data
            
        Returns:
            M8ChainStep: New instance with values from the dictionary
        """
        return cls(
            phrase=data.get("phrase", cls.EMPTY_PHRASE),
            transpose=data.get("transpose", cls.DEFAULT_TRANSPOSE)
        )

class M8Chain(list):
    """Represents a sequence of chain steps in the M8 tracker.
    
    A chain is a collection of up to 16 steps that can be used to
    sequence phrases. Chains allow creating longer sequences and
    can transpose phrases to create variations.
    Extends the built-in list type with M8-specific functionality.
    """
    
    def __init__(self):
        """Initialize a chain with empty steps."""
        super().__init__()
        # Initialize with empty steps
        for _ in range(STEP_COUNT):
            self.append(M8ChainStep())
    
    @classmethod
    def read(cls, data):
        """Create a chain from binary data.
        
        Args:
            data: Binary data containing a chain
            
        Returns:
            M8Chain: New instance with steps initialized from the binary data
        """
        instance = cls.__new__(cls)  # Create instance without calling __init__
        list.__init__(instance)  # Initialize the list properly
        
        for i in range(STEP_COUNT):
            start = i * STEP_BLOCK_SIZE
            row_data = data[start:start + STEP_BLOCK_SIZE]
            instance.append(M8ChainStep.read(row_data))
        
        return instance
    
    def clone(self):
        """Create a deep copy of this chain.
        
        Returns:
            M8Chain: New instance with the same steps
        """
        instance = self.__class__()
        instance.clear()  # Remove default items
        
        for step in self:
            if hasattr(step, 'clone'):
                instance.append(step.clone())
            else:
                instance.append(M8ChainStep.read(step.write()))
        
        return instance
    
    def is_empty(self):
        """Check if this chain is empty (all steps have no phrases).
        
        Returns:
            bool: True if all steps are empty, False otherwise
        """
        return all(step.is_empty() for step in self)
    
    def write(self):
        """Convert the chain to binary data.
        
        Returns:
            bytes: Binary representation of the chain
        """
        result = bytearray()
        for step in self:
            step_data = step.write()
            result.extend(step_data)
        return bytes(result)
    
    def validate_phrases(self, phrases):
        """Validate that all referenced phrases exist.
        
        Args:
            phrases: List of phrases to validate against
            
        Raises:
            M8ValidationError: If a chain step references a non-existent phrase
        """
        if not self.is_empty():
            for step_idx, step in enumerate(self):
                if step.phrase != M8ChainStep.EMPTY_PHRASE and (
                    step.phrase >= len(phrases)
                ):
                    raise M8ValidationError(
                        f"Chain step {step_idx} references non-existent or empty "
                        f"phrase {step.phrase}"
                    )
    
    @property
    def available_step_slot(self):
        """Find the first available (empty) step slot.
        
        Returns:
            int: Index of the first empty slot, or None if all slots are used
        """
        for slot_idx, step in enumerate(self):
            if step.phrase == M8ChainStep.EMPTY_PHRASE:  # Empty step has 0xFF phrase
                return slot_idx
        return None
        
    def add_step(self, step):
        """Add a step to the first available slot in the chain.
        
        Args:
            step: The chain step to add
            
        Returns:
            int: The index where the step was added
            
        Raises:
            IndexError: If no empty slots are available
        """
        slot = self.available_step_slot
        if slot is None:
            raise IndexError("No empty step slots available in this chain")
            
        self[slot] = step
        return slot
        
    def set_step(self, step, slot):
        """Set a step at a specific slot in the chain.
        
        Args:
            step: The chain step to set
            slot: The slot index to set
            
        Raises:
            IndexError: If the slot index is out of range
        """
        if not (0 <= slot < len(self)):
            raise IndexError(f"Step slot index must be between 0 and {len(self)-1}")
            
        self[slot] = step
            
    def as_dict(self):
        """Convert chain to dictionary for serialization.
        
        Only includes non-empty steps with their position indices.
        
        Returns:
            dict: Dictionary representation of the chain
        """
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
        """Create a chain from a dictionary.
        
        Args:
            data: Dictionary containing chain data
            
        Returns:
            M8Chain: New instance with steps from the dictionary
        """
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
    """Collection of chains in an M8 song.
    
    A song can have up to 255 chains that can be arranged on tracks.
    Chains are building blocks for song composition in the M8 tracker.
    Extends the built-in list type with M8-specific functionality.
    """
    
    def __init__(self):
        """Initialize a collection with empty chains."""
        super().__init__()
        # Initialize with empty chains
        for _ in range(CHAIN_COUNT):
            self.append(M8Chain())
    
    @classmethod
    def read(cls, data):
        """Create a chains collection from binary data.
        
        Args:
            data: Binary data containing multiple chains
            
        Returns:
            M8Chains: New instance with chains initialized from the binary data
        """
        instance = cls.__new__(cls)  # Create instance without calling __init__
        list.__init__(instance)  # Initialize the list properly
        
        for i in range(CHAIN_COUNT):
            start = i * CHAIN_BLOCK_SIZE
            chain_data = data[start:start + CHAIN_BLOCK_SIZE]
            instance.append(M8Chain.read(chain_data))
        
        return instance
    
    def clone(self):
        """Create a deep copy of this chains collection.
        
        Returns:
            M8Chains: New instance with cloned chains
        """
        instance = self.__class__.__new__(self.__class__)  # Create without __init__
        list.__init__(instance)  # Initialize list directly
        
        for chain in self:
            instance.append(chain.clone())
        
        return instance
    
    def is_empty(self):
        """Check if all chains in the collection are empty.
        
        Returns:
            bool: True if all chains are empty, False otherwise
        """
        return all(chain.is_empty() for chain in self)
    
    def write(self):
        """Convert all chains to binary data.
        
        Returns:
            bytes: Binary representation of all chains
        """
        result = bytearray()
        for chain in self:
            chain_data = chain.write()
            result.extend(chain_data)
        return bytes(result)
    
    def validate_phrases(self, phrases):
        """Validate that all chains reference valid phrases.
        
        Args:
            phrases: List of phrases to validate against
            
        Raises:
            M8ValidationError: If any chain references a non-existent phrase
        """
        for chain_idx, chain in enumerate(self):
            try:
                chain.validate_phrases(phrases)
            except M8ValidationError as e:
                raise M8ValidationError(f"Chain {chain_idx}: {str(e)}") from e
    
    def as_list(self):
        """Convert chains to list for serialization.
        
        Only includes non-empty chains with their position indices.
        
        Returns:
            list: List of dictionaries representing chains
        """
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
        """Create chains collection from a list of dictionaries.
        
        Args:
            items: List of dictionaries with chain data
            
        Returns:
            M8Chains: New instance with chains at their specified positions
        """
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
