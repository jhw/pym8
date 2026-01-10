from enum import IntEnum
from m8.api import M8Block
from m8.api.fx import M8FXTuples, M8FXTuple

# Generate note enum dynamically using functional API
# M8 Note Range: C1 to G11 (where byte 0 = C1, and C4 = 0x24 = 36)
_NOTE_NAMES = ['C', 'CS', 'D', 'DS', 'E', 'F', 'FS', 'G', 'GS', 'A', 'AS', 'B']
_START_OCTAVE = 1  # Byte 0 = C1
_END_OCTAVE = 11   # Ends at G11

# Build dictionary of note names and values
_notes_dict = {}
_note_value = 0
for octave in range(_START_OCTAVE, _END_OCTAVE + 1):
    for note_name in _NOTE_NAMES:
        enum_name = f"{note_name}_{octave}"
        _notes_dict[enum_name] = _note_value
        _note_value += 1

        # Stop at G11
        if octave == _END_OCTAVE and note_name == 'G':
            break

# Create IntEnum from dictionary
M8Note = IntEnum('M8Note', _notes_dict)

# Phrases configuration
PHRASES_OFFSET = 2798
PHRASES_COUNT = 255
PHRASE_STEP_SIZE = 9
PHRASE_STEP_COUNT = 16
PHRASE_BLOCK_SIZE = PHRASE_STEP_COUNT * PHRASE_STEP_SIZE

# Field offsets within phrase step
NOTE_OFFSET = 0
VELOCITY_OFFSET = 1
INSTRUMENT_OFFSET = 2
FX_OFFSET = 3
FX_SIZE = 6

# Constants
BASE_DATA_SIZE = 3
EMPTY_NOTE = 255
EMPTY_VELOCITY = 255
EMPTY_INSTRUMENT = 255
OFF_NOTE = 0x80

# Module-level constants
FX_BLOCK_COUNT = 3  # Number of FX slots per step (from fx config)
STEP_BLOCK_SIZE = PHRASE_STEP_SIZE
STEP_COUNT = PHRASE_STEP_COUNT
PHRASE_COUNT = PHRASES_COUNT

class M8PhraseStep:
    """Step in an M8 phrase with note, velocity, instrument reference, and up to three effects."""

    def __init__(self, note=EMPTY_NOTE, velocity=EMPTY_VELOCITY, instrument=EMPTY_INSTRUMENT):
        # Clients should pass enum.value directly for note values
        self._data = bytearray([note, velocity, instrument])
        self.fx = M8FXTuples()

    @classmethod
    def read(cls, data):
        instance = cls()
        instance._data = bytearray(data[:BASE_DATA_SIZE])
        instance.fx = M8FXTuples.read(data[FX_OFFSET:])
        return instance

    def clone(self):
        instance = self.__class__()
        instance._data = bytearray(self._data)  # Clone base data
        instance.fx = self.fx.clone()  # Clone fx tuples
        return instance

    def write(self):
        buffer = bytearray(self._data)
        buffer.extend(self.fx.write())
        return bytes(buffer)

    @property
    def note(self):
        return self._data[NOTE_OFFSET]

    @note.setter
    def note(self, value):
        # Clients should pass enum.value directly for enum note values
        self._data[NOTE_OFFSET] = value

    @property
    def velocity(self):
        return self._data[VELOCITY_OFFSET]

    @velocity.setter
    def velocity(self, value):
        self._data[VELOCITY_OFFSET] = value

    @property
    def instrument(self):
        return self._data[INSTRUMENT_OFFSET]

    @instrument.setter
    def instrument(self, value):
        self._data[INSTRUMENT_OFFSET] = value

    def off(self):
        """Set this step to OFF note, clearing all other fields."""
        self._data[NOTE_OFFSET] = OFF_NOTE
        self._data[VELOCITY_OFFSET] = EMPTY_VELOCITY
        self._data[INSTRUMENT_OFFSET] = EMPTY_INSTRUMENT

        for i in range(len(self.fx)):
            self.fx[i] = M8FXTuple()

    def validate(self, step_index=None, phrase_index=None):
        """Validate the phrase step.

        Args:
            step_index: Optional step index for error messages
            phrase_index: Optional phrase index for error messages

        Raises:
            ValueError: If instrument reference is invalid
        """
        # Instrument must be 0-127 (valid) or 255 (empty)
        # Values 128-254 are invalid
        if self.instrument != EMPTY_INSTRUMENT and self.instrument > 127:
            ctx = ""
            if phrase_index is not None:
                ctx = f" phrase {phrase_index}"
            if step_index is not None:
                ctx += f" step {step_index}"
            raise ValueError(f"Invalid instrument reference {self.instrument}{ctx}: must be 0-127 or 255 (empty)")

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

    def validate(self, phrase_index=None):
        """Validate the phrase.

        Args:
            phrase_index: Optional phrase index for error messages

        Raises:
            ValueError: If phrase has incorrect number of steps
        """
        if len(self) != STEP_COUNT:
            ctx = f" (phrase {phrase_index})" if phrase_index is not None else ""
            raise ValueError(f"Phrase{ctx} has {len(self)} steps, expected {STEP_COUNT}")

        for i, step in enumerate(self):
            step.validate(step_index=i, phrase_index=phrase_index)

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

    def validate(self):
        """Validate the phrases collection.

        Raises:
            ValueError: If there are more phrases than allowed
        """
        if len(self) > PHRASE_COUNT:
            raise ValueError(f"Too many phrases: {len(self)}, maximum is {PHRASE_COUNT}")

        for i, phrase in enumerate(self):
            phrase.validate(phrase_index=i)