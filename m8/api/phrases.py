from m8.api import M8Block
from m8.api.fx import M8FXTuples, M8FXTuple
from m8.core.format import load_format_config
from m8.core.validation import M8ValidationResult

# Load configuration
config = load_format_config()["phrases"]
fx_config = load_format_config()["fx"]

# Module-level constants
FX_BLOCK_COUNT = fx_config["block_count"]   # Number of FX slots per step
STEP_BLOCK_SIZE = config["step_size"]       # Size of each step in bytes
STEP_COUNT = config["step_count"]           # Number of steps per phrase 
PHRASE_BLOCK_SIZE = STEP_COUNT * STEP_BLOCK_SIZE  # Total phrase size in bytes
PHRASE_COUNT = config["count"]              # Maximum number of phrases

class M8PhraseStep:
    """Step in an M8 phrase with note, velocity, instrument reference, and up to three effects."""
    
    NOTE_OFFSET = config["fields"]["note"]["offset"]
    VELOCITY_OFFSET = config["fields"]["velocity"]["offset"]
    INSTRUMENT_OFFSET = config["fields"]["instrument"]["offset"]
    FX_OFFSET = config["fields"]["fx"]["offset"]
    
    BASE_DATA_SIZE = config["constants"]["base_data_size"]
    
    EMPTY_NOTE = config["constants"]["empty_note"]
    EMPTY_VELOCITY = config["constants"]["empty_velocity"]
    EMPTY_INSTRUMENT = config["constants"]["empty_instrument"]
    
    OFF_NOTE = 0x80
    
    def __init__(self, note=EMPTY_NOTE, velocity=EMPTY_VELOCITY, instrument=EMPTY_INSTRUMENT):
        # Clients should pass enum.value directly for note values
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
        """Check if this phrase step is empty."""
        # If FX is non-empty, the step is non-empty even with an empty note
        if not self.fx.is_empty():
            return False
        
        # If note is OFF_NOTE (0x80), the step is non-empty
        if self._data[self.NOTE_OFFSET] == self.OFF_NOTE:
            return False
            
        # If FX is empty, check if note/velocity/instrument are all empty
        return (self.note == self.EMPTY_NOTE and
                self.velocity == self.EMPTY_VELOCITY and
                self.instrument == self.EMPTY_INSTRUMENT)
                
    def is_complete(self):
        """Check if this phrase step is complete."""
        # If the step is completely empty, it's considered complete
        if self.is_empty():
            return True
            
        # If it's a note-off, it's considered complete by definition
        if self._data[self.NOTE_OFFSET] == self.OFF_NOTE:
            return True
            
        # For non-empty steps, check all required fields are set
        has_note = self.note != self.EMPTY_NOTE
        has_velocity = self.velocity != self.EMPTY_VELOCITY
        has_instrument = self.instrument != self.EMPTY_INSTRUMENT
        fx_complete = self.fx.is_complete()
        
        # All FX must be complete, and if there's a note, velocity and instrument must be set too
        return fx_complete and (not has_note or (has_velocity and has_instrument))

    def write(self):
        buffer = bytearray(self._data)
        buffer.extend(self.fx.write())
        return bytes(buffer)

    @property
    def note(self):
        return self._data[self.NOTE_OFFSET]
    
    @note.setter
    def note(self, value):
        # Clients should pass enum.value directly for enum note values
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
        for slot_idx, fx in enumerate(self.fx):
            if not fx.is_empty() and fx.key == key:
                return slot_idx
        return None
    
    def add_fx(self, key, value):
        """Add FX with key and value. Clients should pass enum.value for key."""
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
        """Set FX at specific slot. Clients should pass enum.value for key."""
        if not (0 <= slot < FX_BLOCK_COUNT):
            raise IndexError(f"FX slot index must be between 0 and {FX_BLOCK_COUNT-1}")
        
        self.fx[slot] = M8FXTuple(key=key, value=value)
    
    def get_fx(self, key):
        """Get FX value by key. Clients should pass enum.value for key."""
        slot = self.find_fx_slot(key)
        if slot is not None:
            return self.fx[slot].value
        return None
    
    def delete_fx(self, key):
        """Delete FX by key. Clients should pass enum.value for key."""
        slot = self.find_fx_slot(key)
        if slot is not None:
            # Replace with empty FX tuple
            self.fx[slot] = M8FXTuple()
            return True
        return False
        
    def off(self):
        self._data[self.NOTE_OFFSET] = self.OFF_NOTE
        self._data[self.VELOCITY_OFFSET] = self.EMPTY_VELOCITY
        self._data[self.INSTRUMENT_OFFSET] = self.EMPTY_INSTRUMENT
        
        for i in range(len(self.fx)):
            self.fx[i] = M8FXTuple(key=M8FXTuple.EMPTY_KEY, value=M8FXTuple.DEFAULT_VALUE)

    def as_dict(self):
        fx_list = self.fx.as_list()
        
        result = {}
        
        # Only include non-empty fields (FF values are considered empty)
        if self.note != self.EMPTY_NOTE:
            result["note"] = self.note
            
        if self.velocity != self.EMPTY_VELOCITY:
            result["velocity"] = self.velocity
            
        if self.instrument != self.EMPTY_INSTRUMENT:
            result["instrument"] = self.instrument
            
        # Always include FX list even if empty, for consistency
        result["fx"] = fx_list
        
        return result

    @classmethod
    def from_dict(cls, data):
        # Get default values for optional fields
        note = data.get("note", cls.EMPTY_NOTE)
        velocity = data.get("velocity", cls.EMPTY_VELOCITY)
        instrument = data.get("instrument", cls.EMPTY_INSTRUMENT)
        
        instance = cls(
            note=note,
            velocity=velocity,
            instrument=instrument
        )
    
        # Deserialize FX using the FXTuples' from_list method
        if "fx" in data:
            instance.fx = M8FXTuples.from_list(data["fx"])
    
        return instance

class M8Phrase(list):
    """Collection of up to 16 steps that defines a musical pattern in the M8 tracker."""
    
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
        
    def is_complete(self):
        """Check if all steps in this phrase are complete."""
        if self.is_empty():
            return True
            
        return all(step.is_complete() for step in self)
    
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

    def validate_references_instruments(self, instruments, result=None):
        if result is None:
            result = M8ValidationResult(context="phrase.instruments")
            
        if not self.is_empty():
            for step_idx, step in enumerate(self):
                if step.instrument != M8PhraseStep.EMPTY_INSTRUMENT and (
                    step.instrument >= len(instruments) or
                    isinstance(instruments[step.instrument], M8Block)
                ):
                    result.add_error(
                        f"Step {step_idx} references non-existent or empty "
                        f"instrument {step.instrument}",
                        f"step[{step_idx}]"
                    )
                    
        return result
    
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
        # Only include non-empty steps for sparse representation
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
            instance.append(M8PhraseStep())
        
        # Add steps from dict at their original positions
        if "steps" in data:
            for step_data in data["steps"]:
                # Get index from data
                index = step_data["index"]
                if 0 <= index < STEP_COUNT:
                    # Remove index field before passing to from_dict
                    step_dict = {k: v for k, v in step_data.items() if k != "index"}
                    instance[index] = M8PhraseStep.from_dict(step_dict)
        
        return instance

class M8Phrases(list):
    """Collection of up to 255 phrases that make up a complete M8 project."""
    
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
        
    def is_complete(self):
        """Check if all phrases in this collection are complete."""
        if self.is_empty():
            return True
            
        return all(phrase.is_empty() or phrase.is_complete() for phrase in self)
    
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

    def validate_references_instruments(self, instruments, result=None):
        if result is None:
            result = M8ValidationResult(context="phrases.instruments")
            
        for phrase_idx, phrase in enumerate(self):
            phrase_result = phrase.validate_references_instruments(instruments)
            if not phrase_result.valid:
                # Merge errors with the proper context
                result.merge(phrase_result, f"phrase[{phrase_idx}]")
                
        return result
    
    def as_list(self):
        # Only include non-empty phrases with position indices
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
        instance = cls.__new__(cls)  # Create without __init__
        list.__init__(instance)  # Initialize list directly
        
        # Initialize full list with empty phrases
        for _ in range(PHRASE_COUNT):
            instance.append(M8Phrase())
        
        # Add phrases from list
        if items:
            for phrase_data in items:
                # Get index from data
                index = phrase_data["index"]
                if 0 <= index < PHRASE_COUNT:
                    # Remove index field before passing to from_dict
                    phrase_dict = {k: v for k, v in phrase_data.items() if k != "index"}
                    instance[index] = M8Phrase.from_dict(phrase_dict)
        
        return instance