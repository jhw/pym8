from m8.api import M8ValidationError, M8Block
from m8.api.fx import M8FXTuples, M8FXTuple 

# Module-level constants
FX_BLOCK_COUNT = 3
STEP_BLOCK_SIZE = 9
STEP_COUNT = 16
PHRASE_BLOCK_SIZE = STEP_COUNT * STEP_BLOCK_SIZE
PHRASE_COUNT = 255

class M8PhraseStep:
    # Class-level constants
    NOTE_OFFSET = 0
    VELOCITY_OFFSET = 1
    INSTRUMENT_OFFSET = 2
    FX_OFFSET = 3
    
    BASE_DATA_SIZE = 3  # Size of the basic step data (note, velocity, instrument)
    
    # Values for empty steps
    EMPTY_NOTE = 0xFF
    EMPTY_VELOCITY = 0xFF
    EMPTY_INSTRUMENT = 0xFF
    
    def __init__(self, note=EMPTY_NOTE, velocity=EMPTY_VELOCITY, instrument=EMPTY_INSTRUMENT):
        # Initialize base data
        self._data = bytearray([note, velocity, instrument])
        self.fx = M8FXTuples()

    @classmethod
    def read(cls, data):
        instance = cls()
        instance._data = bytearray(data[:cls.BASE_DATA_SIZE])
        instance.fx = M8FXTuples.read(data[cls.FX_OFFSET:])
        return instance

    def clone(self):
        instance = self.__class__()
        instance._data = bytearray(self._data)  # Clone base data
        instance.fx = self.fx.clone()  # Clone fx tuples
        return instance

    def is_empty(self):
        return (self.note == self.EMPTY_NOTE and
                self.velocity == self.EMPTY_VELOCITY and
                self.instrument == self.EMPTY_INSTRUMENT and
                self.fx.is_empty())

    def write(self):
        buffer = bytearray(self._data)
        buffer.extend(self.fx.write())
        return bytes(buffer)

    @property
    def note(self):
        return self._data[self.NOTE_OFFSET]
    
    @note.setter
    def note(self, value):
        self._data[self.NOTE_OFFSET] = value
    
    @property
    def velocity(self):
        return self._data[self.VELOCITY_OFFSET]
    
    @velocity.setter
    def velocity(self, value):
        self._data[self.VELOCITY_OFFSET] = value
    
    @property
    def instrument(self):
        return self._data[self.INSTRUMENT_OFFSET]
    
    @instrument.setter
    def instrument(self, value):
        self._data[self.INSTRUMENT_OFFSET] = value

    @property
    def available_slot(self):
        for slot_idx, fx in enumerate(self.fx):
            if fx.is_empty() or (fx.key == 0xFF):
                return slot_idx
        return None
    
    def find_fx_slot(self, key):
        """
        Find an existing FX slot with the given key
        
        Args:
            key: The FX key to find
            
        Returns:
            The slot index if found, None otherwise
        """
        for slot_idx, fx in enumerate(self.fx):
            if not fx.is_empty() and fx.key == key:
                return slot_idx
        return None
    
    def add_fx(self, key, value):
        """
        Add or update an FX tuple with the given key and value
        
        If an FX tuple with the given key already exists, its value will be updated.
        Otherwise, a new FX tuple will be added to the first available slot.
        
        Args:
            key: The FX key
            value: The FX value
            
        Returns:
            The slot index where the FX tuple was added or updated
            
        Raises:
            IndexError: If no empty slots are available and no matching key was found
        """
        # First check if we already have this key
        existing_slot = self.find_fx_slot(key)
        if existing_slot is not None:
            # Update the existing FX tuple
            self.fx[existing_slot].value = value
            return existing_slot
        
        # Otherwise find an empty slot
        slot = self.available_slot
        if slot is None:
            raise IndexError("No empty FX slots available in this step")
            
        self.fx[slot] = M8FXTuple(key=key, value=value)
        return slot
        
    def set_fx(self, key, value, slot):
        """
        Set an FX tuple at a specific slot
        
        Args:
            key: The FX key
            value: The FX value
            slot: The slot index to set
            
        Raises:
            IndexError: If the slot index is out of range
        """
        if not (0 <= slot < FX_BLOCK_COUNT):
            raise IndexError(f"FX slot index must be between 0 and {FX_BLOCK_COUNT-1}")
            
        self.fx[slot] = M8FXTuple(key=key, value=value)    
    
    def get_fx(self, key):
        """
        Get the value for a specific FX key
        
        Args:
            key: The FX key to look for
            
        Returns:
            The value of the FX if found, None otherwise
        """
        slot = self.find_fx_slot(key)
        if slot is not None:
            return self.fx[slot].value
        return None
    
    def delete_fx(self, key):
        """
        Delete an FX with the specified key
        
        Replaces the FX tuple with a blank M8FXTuple
        
        Args:
            key: The FX key to delete
            
        Returns:
            True if the FX was found and deleted, False otherwise
        """
        slot = self.find_fx_slot(key)
        if slot is not None:
            # Replace with empty FX tuple
            self.fx[slot] = M8FXTuple()
            return True
        return False

    def as_dict(self):
        """Convert phrase step to dictionary for serialization"""
        result = {
            "note": self.note,
            "velocity": self.velocity,
            "instrument": self.instrument,
            "fx": self.fx.as_list()  # Use the new as_list() method
        }
        return result

    @classmethod
    def from_dict(cls, data):
        """Create a phrase step from a dictionary"""
        instance = cls(
            note=data.get("note", cls.EMPTY_NOTE),
            velocity=data.get("velocity", cls.EMPTY_VELOCITY),
            instrument=data.get("instrument", cls.EMPTY_INSTRUMENT)
        )
    
        # Deserialize FX using the FXTuples' from_list method
        if "fx" in data:
            instance.fx = M8FXTuples.from_list(data["fx"])
    
        return instance

class M8Phrase(list):
    def __init__(self):
        super().__init__()
        # Initialize with empty steps
        for _ in range(STEP_COUNT):
            self.append(M8PhraseStep())
    
    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)  # Create instance without calling __init__
        list.__init__(instance)  # Initialize the list properly
        
        for i in range(STEP_COUNT):
            start = i * STEP_BLOCK_SIZE
            step_data = data[start:start + STEP_BLOCK_SIZE]
            instance.append(M8PhraseStep.read(step_data))
        
        return instance
    
    def clone(self):
        instance = self.__class__()
        instance.clear()  # Remove default items
        
        for step in self:
            if hasattr(step, 'clone'):
                instance.append(step.clone())
            else:
                instance.append(M8PhraseStep.read(step.write()))
        
        return instance
    
    def is_empty(self):
        return all(step.is_empty() for step in self)
    
    def write(self):
        result = bytearray()
        for step in self:
            step_data = step.write()
            # Ensure each step occupies exactly STEP_BLOCK_SIZE bytes
            if len(step_data) < STEP_BLOCK_SIZE:
                step_data = step_data + bytes([0x0] * (STEP_BLOCK_SIZE - len(step_data)))
            elif len(step_data) > STEP_BLOCK_SIZE:
                step_data = step_data[:STEP_BLOCK_SIZE]
            result.extend(step_data)
        return bytes(result)

    def validate_instruments(self, instruments):
        if not self.is_empty():
            for step_idx, step in enumerate(self):
                if step.instrument != M8PhraseStep.EMPTY_INSTRUMENT and (
                    step.instrument >= len(instruments) or
                    isinstance(instruments[step.instrument], M8Block)
                ):
                    raise M8ValidationError(
                        f"Step {step_idx} references non-existent or empty "
                        f"instrument {step.instrument}"
                    )
    
    @property
    def available_step_slot(self):
        for slot_idx, step in enumerate(self):
            if step.is_empty():
                return slot_idx
        return None
        
    def add_step(self, step):
        slot = self.available_step_slot
        if slot is None:
            raise IndexError("No empty step slots available in this phrase")
            
        self[slot] = step
        return slot
        
    def set_step(self, step, slot):
        if not (0 <= slot < len(self)):
            raise IndexError(f"Step slot index must be between 0 and {len(self)-1}")
            
        self[slot] = step
            
    def as_dict(self):
        """Convert phrase to dictionary for serialization"""
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
        """Create a phrase from a dictionary"""
        instance = cls()
        instance.clear()  # Clear default steps
        
        # Initialize with empty steps
        for _ in range(STEP_COUNT):
            instance.append(M8PhraseStep())
        
        # Add steps from dict at their original positions
        if "steps" in data:
            for step_data in data["steps"]:
                # Get index from data or default to 0
                index = step_data.get("index", 0)
                if 0 <= index < STEP_COUNT:
                    # Remove index field before passing to from_dict
                    step_dict = {k: v for k, v in step_data.items() if k != "index"}
                    instance[index] = M8PhraseStep.from_dict(step_dict)
        
        return instance

class M8Phrases(list):
    def __init__(self):
        super().__init__()
        # Initialize with empty phrases
        for _ in range(PHRASE_COUNT):
            self.append(M8Phrase())
    
    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)  # Create instance without calling __init__
        list.__init__(instance)  # Initialize the list properly
        
        for i in range(PHRASE_COUNT):
            start = i * PHRASE_BLOCK_SIZE
            phrase_data = data[start:start + PHRASE_BLOCK_SIZE]
            instance.append(M8Phrase.read(phrase_data))
        
        return instance
    
    def clone(self):
        instance = self.__class__()
        instance.clear()  # Remove default items
        
        for phrase in self:
            instance.append(phrase.clone())
        
        return instance
    
    def is_empty(self):
        return all(phrase.is_empty() for phrase in self)
    
    def write(self):
        result = bytearray()
        for phrase in self:
            phrase_data = phrase.write()
            # Ensure each phrase occupies exactly PHRASE_BLOCK_SIZE bytes
            if len(phrase_data) < PHRASE_BLOCK_SIZE:
                phrase_data = phrase_data + bytes([0x0] * (PHRASE_BLOCK_SIZE - len(phrase_data)))
            elif len(phrase_data) > PHRASE_BLOCK_SIZE:
                phrase_data = phrase_data[:PHRASE_BLOCK_SIZE]
            result.extend(phrase_data)
        return bytes(result)

    def validate_instruments(self, instruments):
        for phrase_idx, phrase in enumerate(self):
            try:
                phrase.validate_instruments(instruments)
            except M8ValidationError as e:
                raise M8ValidationError(f"Phrase {phrase_idx}: {str(e)}") from e
    
    def as_list(self):
        """Convert phrases to list for serialization"""
        items = []
        for i, phrase in enumerate(self):
            if not phrase.is_empty():
                phrase_dict = phrase.as_dict()
                # Add index to track position
                phrase_dict["index"] = i
                items.append(phrase_dict)
        
        return items
        
    @classmethod
    def from_list(cls, items):
        """Create phrases from a list"""
        instance = cls.__new__(cls)  # Create without __init__
        list.__init__(instance)  # Initialize list directly
        
        # Initialize full list with empty phrases
        for _ in range(PHRASE_COUNT):
            instance.append(M8Phrase())
        
        # Add phrases from list
        if items:
            for phrase_data in items:
                # Get index from data or default to 0
                index = phrase_data.get("index", 0)
                if 0 <= index < PHRASE_COUNT:
                    # Remove index field before passing to from_dict
                    phrase_dict = {k: v for k, v in phrase_data.items() if k != "index"}
                    instance[index] = M8Phrase.from_dict(phrase_dict)
        
        return instance
