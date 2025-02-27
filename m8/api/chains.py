from m8.api import M8ValidationError, M8IndexError

STEP_BLOCK_SIZE = 2
STEP_COUNT = 16
CHAIN_BLOCK_SIZE = STEP_COUNT * STEP_BLOCK_SIZE
CHAIN_COUNT = 255

class M8ChainStep:
    def __init__(self, phrase=0xFF, transpose=0x0):
        # Initialize _data first
        self._data = bytearray([phrase, transpose])
        # No need to set properties, data is already initialized
    
    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)  # Create instance without calling __init__
        instance._data = bytearray(data[:STEP_BLOCK_SIZE])
        return instance
    
    def write(self):
        return bytes(self._data)
    
    def is_empty(self):
        return self.phrase == 0xFF
    
    @property
    def phrase(self):
        return self._data[0]
    
    @phrase.setter
    def phrase(self, value):
        self._data[0] = value
    
    @property
    def transpose(self):
        return self._data[1]
    
    @transpose.setter
    def transpose(self, value):
        self._data[1] = value
    
    def as_dict(self):
        """Convert chain step to dictionary for serialization"""
        return {
            "__class__": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "phrase": self.phrase,
            "transpose": self.transpose
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a chain step from a dictionary"""
        return cls(
            phrase=data.get("phrase", 0xFF),
            transpose=data.get("transpose", 0x0)
        )
    
class M8Chain(list):
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
            if hasattr(step, 'clone'):
                instance.append(step.clone())
            else:
                instance.append(M8ChainStep.read(step.write()))
        
        return instance
    
    def is_empty(self):
        return all(step.is_empty() for step in self)
    
    def write(self):
        result = bytearray()
        for step in self:
            step_data = step.write()
            result.extend(step_data)
        return bytes(result)
    
    def validate_phrases(self, phrases):
        if not self.is_empty():
            for step_idx, step in enumerate(self):
                if step.phrase != 0xFF and (
                    step.phrase >= len(phrases) or 
                    phrases[step.phrase].is_empty()
                ):
                    raise M8ValidationError(
                        f"Chain step {step_idx} references non-existent or empty "
                        f"phrase {step.phrase}"
                    )
    
    @property
    def available_step_slot(self):
        for slot_idx, step in enumerate(self):
            if step.phrase == 0xFF:  # Empty step has 0xFF phrase
                return slot_idx
        return None
        
    def add_step(self, step):
        slot = self.available_step_slot
        if slot is None:
            raise M8IndexError("No empty step slots available in this chain")
            
        self[slot] = step
        return slot
        
    def set_step(self, step, slot):
        if not (0 <= slot < len(self)):
            raise M8IndexError(f"Step slot index must be between 0 and {len(self)-1}")
            
        self[slot] = step
            
    def as_dict(self):
        """Convert chain to dictionary for serialization"""
        result = {
            "__class__": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "steps": [step.as_dict() for step in self if step.phrase != 0xFF]
        }
        return result
        
    @classmethod
    def from_dict(cls, data):
        """Create a chain from a dictionary"""
        instance = cls()
        instance.clear()  # Clear default steps
        
        # Add steps from dict
        if "steps" in data:
            # First add the non-empty steps
            for step_data in data["steps"]:
                instance.append(M8ChainStep.from_dict(step_data))
                
            # Fill remaining slots with empty steps
            while len(instance) < STEP_COUNT:
                instance.append(M8ChainStep())
        else:
            # Fill with empty steps if no steps in data
            for _ in range(STEP_COUNT):
                instance.append(M8ChainStep())
        
        return instance
        
class M8Chains(list):
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
    
    def validate_phrases(self, phrases):
        for chain_idx, chain in enumerate(self):
            try:
                chain.validate_phrases(phrases)
            except M8ValidationError as e:
                raise M8ValidationError(f"Chain {chain_idx}: {str(e)}") from e
    
    def as_dict(self):
        """Convert chains to dictionary for serialization"""
        return {
            "__class__": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "items": [chain.as_dict() for chain in self if not chain.is_empty()]
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create chains from a dictionary"""
        instance = cls.__new__(cls)  # Create without __init__
        list.__init__(instance)  # Initialize list directly
        
        # Create a dictionary to track which indices have been filled
        filled_indices = set()
        
        # Add chains from dict
        if "items" in data:
            for i, chain_data in enumerate(data["items"]):
                if i < CHAIN_COUNT:
                    instance.append(M8Chain.from_dict(chain_data))
                    filled_indices.add(i)
        
        # Fill remaining slots with empty chains
        while len(instance) < CHAIN_COUNT:
            instance.append(M8Chain())
        
        return instance
    
