from m8.api import M8ValidationError, M8Block
from m8.api.fx import M8FXTuples, M8FXTuple
from m8.core.enums import EnumPropertyMixin, serialize_param_enum_value, deserialize_param_enum, M8InstrumentContext
from m8.config import load_format_config

# Load configuration
config = load_format_config()["phrases"]
fx_config = load_format_config()["fx"]

# Module-level constants
FX_BLOCK_COUNT = fx_config["block_count"]   # Number of FX slots per step
STEP_BLOCK_SIZE = config["step_size"]       # Size of each step in bytes
STEP_COUNT = config["step_count"]           # Number of steps per phrase 
PHRASE_BLOCK_SIZE = STEP_COUNT * STEP_BLOCK_SIZE  # Total phrase size in bytes
PHRASE_COUNT = config["count"]              # Maximum number of phrases

class M8PhraseStep(EnumPropertyMixin):
    """Step in an M8 phrase with note, velocity, instrument reference, and up to three effects."""
    
    NOTE_OFFSET = config["fields"]["note"]["offset"]
    VELOCITY_OFFSET = config["fields"]["velocity"]["offset"]
    INSTRUMENT_OFFSET = config["fields"]["instrument"]["offset"]
    FX_OFFSET = config["fields"]["fx"]["offset"]
    
    BASE_DATA_SIZE = config["constants"]["base_data_size"]
    
    EMPTY_NOTE = config["constants"]["empty_note"]
    EMPTY_VELOCITY = config["constants"]["empty_velocity"]
    EMPTY_INSTRUMENT = config["constants"]["empty_instrument"]
    
    def __init__(self, note=EMPTY_NOTE, velocity=EMPTY_VELOCITY, instrument=EMPTY_INSTRUMENT):
        # Process note value - convert from string enum if needed
        if isinstance(note, str) and note != self.EMPTY_NOTE:
            if "enums" in config["fields"]["note"]:
                note = deserialize_param_enum(
                    config["fields"]["note"]["enums"],
                    note,
                    "note",
                    None
                )
            else:
                note = int(note)  # Try direct conversion
                
        self._data = bytearray([note, velocity, instrument])
        self.fx = M8FXTuples()

    @classmethod
    def read(cls, data):
        instance = cls()
        instance._data = bytearray(data[:cls.BASE_DATA_SIZE])
        
        # Set up context for FX serialization based on the instrument
        instrument_id = instance._data[cls.INSTRUMENT_OFFSET]
        if instrument_id != cls.EMPTY_INSTRUMENT:
            context = M8InstrumentContext.get_instance()
            with context.with_instrument(instrument_id=instrument_id):
                instance.fx = M8FXTuples.read(data[cls.FX_OFFSET:])
        else:
            instance.fx = M8FXTuples.read(data[cls.FX_OFFSET:])
            
        return instance

    def clone(self):
        instance = self.__class__()
        instance._data = bytearray(self._data)  # Clone base data
        instance.fx = self.fx.clone()  # Clone fx tuples
        return instance

    def is_empty(self):
        """Check if this phrase step is empty.
        
        Uses a lenient approach that checks if note, velocity and instrument equal their
        M8 empty values (typically 0xFF), rather than validating notes against enums.
        This approach is preferable because:
        1. It focuses on the M8's definition of emptiness
        2. It's more performant by avoiding enum lookups
        3. It's less coupled to enum implementations
        4. It maintains separation between emptiness checks and validity checks
        """
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
        # Get the underlying byte value
        numeric_value = self._data[self.NOTE_OFFSET]
        
        # If empty note, just return it as-is
        if numeric_value == self.EMPTY_NOTE:
            return numeric_value
            
        # If there are enum mappings, convert to string
        if "enums" in config["fields"]["note"]:
            string_value = serialize_param_enum_value(
                numeric_value,
                config["fields"]["note"],
                None,
                "note"
            )
            return string_value
        
        return numeric_value
    
    @note.setter
    def note(self, value):
        # Convert string enum to numeric value if needed
        if isinstance(value, str) and value != self.EMPTY_NOTE:
            if "enums" in config["fields"]["note"]:
                value = deserialize_param_enum(
                    config["fields"]["note"]["enums"],
                    value,
                    "note",
                    None
                )
        
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
        
        # Set instrument context for FX if there's a valid instrument
        instrument_id = self.instrument
        if instrument_id != self.EMPTY_INSTRUMENT:
            context = M8InstrumentContext.get_instance()
            with context.with_instrument(instrument_id=instrument_id):
                self.fx[slot] = M8FXTuple(key=key, value=value)
        else:
            self.fx[slot] = M8FXTuple(key=key, value=value)
            
        return slot
        
    def set_fx(self, key, value, slot):
        if not (0 <= slot < FX_BLOCK_COUNT):
            raise IndexError(f"FX slot index must be between 0 and {FX_BLOCK_COUNT-1}")
        
        # Set instrument context for FX if there's a valid instrument
        instrument_id = self.instrument
        if instrument_id != self.EMPTY_INSTRUMENT:
            context = M8InstrumentContext.get_instance()
            with context.with_instrument(instrument_id=instrument_id):
                self.fx[slot] = M8FXTuple(key=key, value=value)
        else:
            self.fx[slot] = M8FXTuple(key=key, value=value)
    
    def get_fx(self, key):
        slot = self.find_fx_slot(key)
        if slot is not None:
            return self.fx[slot].value
        return None
    
    def delete_fx(self, key):
        slot = self.find_fx_slot(key)
        if slot is not None:
            # Replace with empty FX tuple
            self.fx[slot] = M8FXTuple()
            return True
        return False

    def as_dict(self):
        # Set up context for FX serialization based on the instrument
        instrument_id = self.instrument
        
        # Serialize FX with instrument context if there's a valid instrument reference
        if instrument_id != self.EMPTY_INSTRUMENT:
            from m8.core.enums import with_referenced_context
            with with_referenced_context(instrument_id):
                fx_list = self.fx.as_list()
        else:
            fx_list = self.fx.as_list()
        
        result = {
            "note": self.note,
            "velocity": self.velocity,
            "instrument": instrument_id,
            "fx": fx_list
        }
        return result

    @classmethod
    def from_dict(cls, data):
        instance = cls(
            note=data["note"],
            velocity=data["velocity"],
            instrument=data["instrument"]
        )
    
        # Deserialize FX using the FXTuples' from_list method, with instrument context
        if "fx" in data:
            instrument_id = data["instrument"]
            
            # Use instrument context if there's a valid instrument reference
            if instrument_id != cls.EMPTY_INSTRUMENT:
                from m8.core.enums import with_referenced_context
                with with_referenced_context(instrument_id):
                    instance.fx = M8FXTuples.from_list(data["fx"])
            else:
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

    def validate_references_instruments(self, instruments):
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

    def validate_references_instruments(self, instruments):
        for phrase_idx, phrase in enumerate(self):
            try:
                phrase.validate_references_instruments(instruments)
            except M8ValidationError as e:
                raise M8ValidationError(f"Phrase {phrase_idx}: {str(e)}") from e
    
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
