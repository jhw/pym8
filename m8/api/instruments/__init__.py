# m8/api/instruments/__init__.py
from m8.api import M8Block, load_class, join_nibbles, split_byte
from m8.api.instruments.params import M8FilterParams, M8AmpParams, M8MixerParams
from m8.api.modulators import M8Modulators, create_default_modulators

INSTRUMENT_TYPES = {
    0x01: "m8.api.instruments.macrosynth.M8MacroSynth"
}

BLOCK_SIZE = 215
BLOCK_COUNT = 128

class M8InstrumentBase:
    # Define offsets as class variables
    SYNTH_OFFSET = 18  # Shape starts at 18
    FILTER_OFFSET = 23  # Filter type starts at 23
    AMP_OFFSET = 26    # Amp level starts at 26
    MIXER_OFFSET = 28  # Mixer pan starts at 28
    MODULATORS_OFFSET = 63  # Keep this unchanged
    
    # Common parameter offsets
    TYPE_OFFSET = 0
    NAME_OFFSET = 1
    NAME_LENGTH = 12
    TRANSPOSE_EQ_OFFSET = 13
    TABLE_TICK_OFFSET = 14
    VOLUME_OFFSET = 15
    PITCH_OFFSET = 16
    FINE_TUNE_OFFSET = 17
    
    def __init__(self, **kwargs):
        # Common synthesizer parameters
        self.name = " "
        self.transpose = 0x4
        self.eq = 0x1
        self.table_tick = 0x01
        self.volume = 0x0
        self.pitch = 0x0
        self.fine_tune = 0x80
        
        # Initialize common parameter objects using class offsets
        self.filter = M8FilterParams(offset=self.FILTER_OFFSET)
        self.amp = M8AmpParams(offset=self.AMP_OFFSET)
        self.mixer = M8MixerParams(offset=self.MIXER_OFFSET)
        
        # Create modulators
        self.modulators = M8Modulators(items=create_default_modulators())
        
        # Extract prefixed parameters for each common group
        filter_kwargs = {k[7:]: v for k, v in kwargs.items() if k.startswith('filter_')}
        amp_kwargs = {k[4:]: v for k, v in kwargs.items() if k.startswith('amp_')}
        mixer_kwargs = {k[6:]: v for k, v in kwargs.items() if k.startswith('mixer_')}
        
        # Apply extracted parameters to common objects
        for key, value in filter_kwargs.items():
            if hasattr(self.filter, key):
                setattr(self.filter, key, value)
        
        for key, value in amp_kwargs.items():
            if hasattr(self.amp, key):
                setattr(self.amp, key, value)
                
        for key, value in mixer_kwargs.items():
            if hasattr(self.mixer, key):
                setattr(self.mixer, key, value)
        
        # Apply any remaining kwargs to base class attributes
        for key, value in kwargs.items():
            if hasattr(self, key) and not key.startswith('_') and key != "modulators" and key != "type":
                setattr(self, key, value)

    @classmethod
    def read(cls, data):
        # Get the instrument type and create the appropriate class
        instr_type = data[cls.TYPE_OFFSET]
        if instr_type not in INSTRUMENT_TYPES:
            raise ValueError(f"Unknown instrument type: {instr_type}")
            
        # Create the specific instrument class
        instr_class = load_class(INSTRUMENT_TYPES[instr_type])
        instance = instr_class.__new__(instr_class)
        
        # Initialize instrument specific parameters
        instance._read_parameters(data)
        
        # Read modulators
        instance.modulators = M8Modulators.read(data[cls.MODULATORS_OFFSET:], 
                                              instrument_type=instance.type)
        
        return instance

    def _read_common_parameters(self, data):
        """Read common parameters shared by all instrument types"""
        self.type = data[self.TYPE_OFFSET]
        self.name = data[self.NAME_OFFSET:self.NAME_OFFSET+self.NAME_LENGTH].decode('utf-8').rstrip('\0')
        
        # Split byte into transpose/eq
        transpose_eq = data[self.TRANSPOSE_EQ_OFFSET]
        self.transpose, self.eq = split_byte(transpose_eq)
        
        self.table_tick = data[self.TABLE_TICK_OFFSET]
        self.volume = data[self.VOLUME_OFFSET]
        self.pitch = data[self.PITCH_OFFSET]
        self.fine_tune = data[self.FINE_TUNE_OFFSET]
        
        # Return the synth offset for reading specific parameters
        return self.SYNTH_OFFSET

    def _read_parameters(self, data):
        """Read instrument parameters from binary data"""
        # Read common parameters first
        next_offset = self._read_common_parameters(data)
        
        # Read synth-specific parameters in subclass
        self._read_specific_parameters(data, next_offset)
        
        # Read common filter, amp, mixer parameters
        self.filter = M8FilterParams.read(data, offset=self.FILTER_OFFSET)
        self.amp = M8AmpParams.read(data, offset=self.AMP_OFFSET)
        self.mixer = M8MixerParams.read(data, offset=self.MIXER_OFFSET)
    
    def _read_specific_parameters(self, data, offset):
        """To be implemented by subclasses to read instrument-specific parameters"""
        pass

    def write(self):
        """
        Write instrument data to binary format with precise offset control.
        This method ensures all parameters are written at their exact offsets.
        """
        # Create a buffer of the correct size
        buffer = bytearray([0] * BLOCK_SIZE)
        
        # Write type
        buffer[self.TYPE_OFFSET] = self.type
        
        # Write name (padded to NAME_LENGTH bytes)
        name_bytes = self.name.encode('utf-8')
        name_bytes = name_bytes[:self.NAME_LENGTH]  # Truncate if too long
        name_padded = name_bytes + bytes([0] * (self.NAME_LENGTH - len(name_bytes)))  # Pad with nulls
        buffer[self.NAME_OFFSET:self.NAME_OFFSET+self.NAME_LENGTH] = name_padded
        
        # Write transpose/eq
        buffer[self.TRANSPOSE_EQ_OFFSET] = join_nibbles(self.transpose, self.eq)
        
        # Write remaining common parameters
        buffer[self.TABLE_TICK_OFFSET] = self.table_tick
        buffer[self.VOLUME_OFFSET] = self.volume
        buffer[self.PITCH_OFFSET] = self.pitch
        buffer[self.FINE_TUNE_OFFSET] = self.fine_tune
        
        # Write synth-specific parameters at SYNTH_OFFSET
        synth_params = self._write_specific_parameters()
        buffer[self.SYNTH_OFFSET:self.SYNTH_OFFSET + len(synth_params)] = synth_params
        
        # Write filter parameters at FILTER_OFFSET
        filter_params = self.filter.write()
        buffer[self.FILTER_OFFSET:self.FILTER_OFFSET + len(filter_params)] = filter_params
        
        # Write amp parameters at AMP_OFFSET
        amp_params = self.amp.write()
        buffer[self.AMP_OFFSET:self.AMP_OFFSET + len(amp_params)] = amp_params
        
        # Write mixer parameters at MIXER_OFFSET
        mixer_params = self.mixer.write()
        buffer[self.MIXER_OFFSET:self.MIXER_OFFSET + len(mixer_params)] = mixer_params
        
        # Write modulators at MODULATORS_OFFSET
        modulator_params = self.modulators.write()
        buffer[self.MODULATORS_OFFSET:self.MODULATORS_OFFSET + len(modulator_params)] = modulator_params
        
        return bytes(buffer)

    def _write_specific_parameters(self):
        """Write MacroSynth-specific parameters"""
        return self.synth.write()

    def is_empty(self):
        # This is a basic implementation that should be overridden by subclasses
        # with instrument-specific logic
        return self.name.strip() == ""

    def clone(self):
        # Create a new instance of the same class
        instance = self.__class__.__new__(self.__class__)
        
        # Copy all attributes
        for key, value in vars(self).items():
            if key == "modulators":
                # Clone modulators if they have a clone method
                instance.modulators = self.modulators.clone() if hasattr(self.modulators, 'clone') else self.modulators
            else:
                setattr(instance, key, value)
                
        return instance

    @property
    def available_modulator_slot(self):
        for slot_idx, mod in enumerate(self.modulators):
            if isinstance(mod, M8Block) or mod.destination == 0:
                return slot_idx
        return None

    def add_modulator(self, modulator):
        slot = self.available_modulator_slot
        if slot is None:
            raise IndexError("No empty modulator slots available in this instrument")
            
        self.modulators[slot] = modulator
        return slot
        
    def set_modulator(self, modulator, slot):
        if not (0 <= slot < len(self.modulators)):
            raise IndexError(f"Modulator slot index must be between 0 and {len(self.modulators)-1}")
            
        self.modulators[slot] = modulator

    def as_dict(self):
        """Convert instrument to dictionary for serialization"""
        # This is a base implementation that should be extended by subclasses
        result = {"type": self.type}
        
        # Add all instance variables except those starting with underscore
        for key, value in vars(self).items():
            if not key.startswith('_') and key != "modulators" and key != "type":
                if hasattr(value, 'as_dict') and callable(getattr(value, 'as_dict')):
                    # If the attribute has an as_dict method, use it
                    result[key] = value.as_dict()
                else:
                    result[key] = value
                
        # Add modulators separately
        result["modulators"] = self.modulators.as_list()
        
        return result

    @classmethod
    def from_dict(cls, data):
        """Create an instrument from a dictionary"""
        # Get the instrument type and create the appropriate class
        instr_type = data.get("type", 0x01)  # Default to MacroSynth if missing
        if instr_type not in INSTRUMENT_TYPES:
            raise ValueError(f"Unknown instrument type: {instr_type}")
        
        # Create the specific instrument class
        instr_class = load_class(INSTRUMENT_TYPES[instr_type])
        instance = instr_class.__new__(instr_class)
    
        # Set type explicitly before initialization
        instance.type = instr_type
    
        # Initialize with default values first
        instance.__init__()  # This will call the actual constructor with no args
    
        # Set all parameters from dict
        for key, value in data.items():
            if key != "modulators" and key != "__class__":
                # Check if this is a nested object with a from_dict method
                if hasattr(instance, key) and hasattr(getattr(instance, key), 'from_dict'):
                    # Replace the object with one created from this dict
                    obj = getattr(instance, key)
                    setattr(instance, key, obj.__class__.from_dict(value, obj.offset if hasattr(obj, 'offset') else None))
                elif hasattr(instance, key):
                    setattr(instance, key, value)
    
        # Set modulators - no longer passing instrument_type
        if "modulators" in data:
            instance.modulators = M8Modulators.from_list(data["modulators"])
    
        return instance

class M8Instruments(list):
    def __init__(self, items=None):
        super().__init__()
        items = items or []
        
        # Fill with provided items
        for item in items:
            self.append(item)
            
        # Fill remaining slots with M8Block instances
        while len(self) < BLOCK_COUNT:
            self.append(M8Block())
    
    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)
        list.__init__(instance)
        
        for i in range(BLOCK_COUNT):
            start = i * BLOCK_SIZE
            block_data = data[start:start + BLOCK_SIZE]
            
            # Check the instrument type byte
            instr_type = block_data[0]
            if instr_type in INSTRUMENT_TYPES:
                # Read using the base class read method which will dispatch to the right subclass
                instance.append(M8InstrumentBase.read(block_data))
            else:
                # Default to M8Block for unknown types or empty slots
                instance.append(M8Block.read(block_data))
        
        return instance
    
    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        list.__init__(instance)
        
        for instr in self:
            if hasattr(instr, 'clone'):
                instance.append(instr.clone())
            else:
                instance.append(instr)
        
        return instance
    
    def is_empty(self):
        return all(isinstance(instr, M8Block) or instr.is_empty() for instr in self)
    
    def write(self):
        result = bytearray()
        for instr in self:
            instr_data = instr.write() if hasattr(instr, 'write') else bytes([0] * BLOCK_SIZE)
            # Ensure each instrument occupies exactly BLOCK_SIZE bytes
            if len(instr_data) < BLOCK_SIZE:
                instr_data = instr_data + bytes([0x0] * (BLOCK_SIZE - len(instr_data)))
            elif len(instr_data) > BLOCK_SIZE:
                instr_data = instr_data[:BLOCK_SIZE]
            result.extend(instr_data)
        return bytes(result)
    
    def as_list(self):
        """Convert instruments to list for serialization"""
        # Only include non-empty instruments with their indexes
        items = []
        for i, instr in enumerate(self):
            if not (isinstance(instr, M8Block) or instr.is_empty()):
                # Make sure we're calling as_dict if it exists
                if hasattr(instr, 'as_dict') and callable(getattr(instr, 'as_dict')):
                    item_dict = instr.as_dict()
                else:
                    item_dict = {"__class__": "m8.M8Block"}
                
                # Add index field to track position
                item_dict["index"] = i
                items.append(item_dict)
        
        return items
    
    @classmethod
    def from_list(cls, items):
        """Create instruments from a list"""
        instance = cls.__new__(cls)
        list.__init__(instance)
        
        # Initialize with empty blocks
        for _ in range(BLOCK_COUNT):
            instance.append(M8Block())
        
        # Set instruments at their original positions
        if items:
            for instr_data in items:
                # Get index from data or default to 0
                index = instr_data.get("index", 0)
                if 0 <= index < BLOCK_COUNT:
                    # Remove index field before passing to from_dict
                    instr_dict = {k: v for k, v in instr_data.items() if k != "index"}
                    instance[index] = M8InstrumentBase.from_dict(instr_dict)
        
        return instance
