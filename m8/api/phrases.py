from m8.api import M8Block
from m8.api.fx import M8FXTuples, M8FXTuple
from m8.core.format import load_format_config

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

    def off(self):
        self._data[self.NOTE_OFFSET] = self.OFF_NOTE
        self._data[self.VELOCITY_OFFSET] = self.EMPTY_VELOCITY
        self._data[self.INSTRUMENT_OFFSET] = self.EMPTY_INSTRUMENT

        for i in range(len(self.fx)):
            self.fx[i] = M8FXTuple(key=M8FXTuple.EMPTY_KEY, value=M8FXTuple.DEFAULT_VALUE)

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