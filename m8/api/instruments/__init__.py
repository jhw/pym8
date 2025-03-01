from m8.api import M8Block, M8IndexError, load_class, join_nibbles
from m8.api.modulators import M8Modulators, create_default_modulators

INSTRUMENT_TYPES = {
    0x01: "m8.api.instruments.macrosynth.M8MacroSynth"
}

BLOCK_SIZE = 215
BLOCK_COUNT = 128
MODULATORS_OFFSET = 63

class M8ParamsBase:
    """Base class for instrument parameter groups."""
    
    def __init__(self, param_defs, offset, **kwargs):
        """
        Initialize the parameter group.
        
        Args:
            param_defs: List of (name, default) tuples defining the parameters
            offset: Byte offset where these parameters start in binary data
            **kwargs: Parameter values to set
        """
        # Store the offset
        self.offset = offset
        
        # Initialize parameters with defaults
        for name, default in param_defs:
            setattr(self, name, default)
        
        # Apply any kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def read(cls, data, offset=None):
        """Read parameters from binary data starting at a specific offset"""
        # Create an instance with default values
        instance = cls(offset=offset)
        
        # Read values from appropriate offsets
        for i, (name, _) in enumerate(instance._param_defs):
            setattr(instance, name, data[offset + i])
        
        return instance
    
    def write(self):
        """Write parameters to binary data"""
        buffer = bytearray()
        for name, _ in self._param_defs:
            buffer.append(getattr(self, name))
        return bytes(buffer)
    
    def clone(self):
        """Create a copy of this parameter object"""
        instance = self.__class__(offset=self.offset)
        for name, _ in self._param_defs:
            setattr(instance, name, getattr(self, name))
        return instance
    
    def as_dict(self):
        """Convert parameters to dictionary for serialization"""
        return {name: getattr(self, name) for name, _ in self._param_defs}
    
    @classmethod
    def from_dict(cls, data, offset=None):
        """Create parameters from a dictionary"""
        instance = cls(offset=offset)
        
        for name, _ in instance._param_defs:
            if name in data:
                setattr(instance, name, data[name])
            
        return instance
        
class M8FilterParams(M8ParamsBase):
    """Class to handle filter parameters shared by multiple instrument types."""
    
    _param_defs = [
        ("type", 0x0),
        ("cutoff", 0xFF),
        ("resonance", 0x0)
    ]
    
    def __init__(self, offset=24, **kwargs):
        super().__init__(self._param_defs, offset, **kwargs)

class M8AmpParams(M8ParamsBase):
    """Class to handle amp parameters shared by multiple instrument types."""
    
    _param_defs = [
        ("level", 0x0),
        ("limit", 0x0)
    ]
    
    def __init__(self, offset=27, **kwargs):
        super().__init__(self._param_defs, offset, **kwargs)

class M8MixerParams(M8ParamsBase):
    """Class to handle mixer parameters shared by multiple instrument types."""
    
    _param_defs = [
        ("pan", 0x80),
        ("dry", 0xC0),
        ("chorus", 0x0),
        ("delay", 0x0),
        ("reverb", 0x0)
    ]
    
    def __init__(self, offset=29, **kwargs):
        super().__init__(self._param_defs, offset, **kwargs)

class M8InstrumentBase:
    def __init__(self, **kwargs):
        # Common synthesizer parameters
        self.name = " "
        self.transpose = 0x4
        self.eq = 0x1
        self.table_tick = 0x01
        self.volume = 0x0
        self.pitch = 0x0
        self.fine_tune = 0x80
        
        # Create modulators
        self.modulators = M8Modulators(items=create_default_modulators())
        
        # Apply any kwargs - specific to each instrument subclass
        for key, value in kwargs.items():
            if hasattr(self, key) and not key.startswith('_') and key != "modulators" and key != "type":
                setattr(self, key, value)

    @classmethod
    def read(cls, data):
        # Get the instrument type and create the appropriate class
        instr_type = data[0]
        if instr_type not in INSTRUMENT_TYPES:
            raise ValueError(f"Unknown instrument type: {instr_type}")
            
        # Create the specific instrument class
        instr_class = load_class(INSTRUMENT_TYPES[instr_type])
        instance = instr_class.__new__(instr_class)
        
        # Initialize instrument specific parameters
        instance._read_parameters(data)
        
        # Read modulators
        instance.modulators = M8Modulators.read(data[MODULATORS_OFFSET:], 
                                              instrument_type=instance.type)
        
        return instance

    def _read_common_parameters(self, data):
        """Read common parameters shared by all instrument types"""
        self.type = data[0]
        self.name = data[1:14].decode('utf-8').rstrip('\0')
        
        # Split byte into transpose/eq
        transpose_eq = data[14]
        self.transpose, self.eq = split_byte(transpose_eq)
        
        self.table_tick = data[15]
        self.volume = data[16]
        self.pitch = data[17]
        self.fine_tune = data[18]
        
        # Return the next offset for subclass-specific parameters
        return 19

    def _write_common_parameters(self):
        """Write common parameters shared by all instrument types"""
        buffer = bytearray()
        
        # Type
        buffer.append(self.type)
        
        # Name (padded to 13 bytes)
        name_bytes = self.name.encode('utf-8')
        name_bytes = name_bytes[:13]  # Truncate if too long
        name_bytes = name_bytes + bytes([0] * (13 - len(name_bytes)))  # Pad with nulls
        buffer.extend(name_bytes)
        
        # Transpose/EQ (combined into one byte)
        transpose_eq = join_nibbles(self.transpose, self.eq)
        buffer.append(transpose_eq)
        
        # Remaining fields
        buffer.append(self.table_tick)
        buffer.append(self.volume)
        buffer.append(self.pitch)
        buffer.append(self.fine_tune)
        
        return buffer

    def _read_parameters(self, data):
        # This method should be implemented by subclasses
        raise NotImplementedError("Subclasses must implement _read_parameters")

    def _write_parameters(self):
        """Write MacroSynth parameters to binary data"""
        # Write common parameters first
        buffer = bytearray(self._write_common_parameters())
        
        # Add synth, filter, amp, and mixer parameters
        buffer.extend(self.synth.write())
        buffer.extend(self.filter.write())
        buffer.extend(self.amp.write())
        buffer.extend(self.mixer.write())
        
        return bytes(buffer)

    def write(self):
        # Write parameters specific to this instrument type
        buffer = bytearray()
        buffer.extend(self._write_parameters())
        
        # Pad between parameters and modulators
        padding_size = MODULATORS_OFFSET - len(buffer)
        if padding_size > 0:
            buffer.extend(bytes([0] * padding_size))
            
        # Write modulators
        buffer.extend(self.modulators.write())
        
        # Ensure the buffer is the correct size
        if len(buffer) < BLOCK_SIZE:
            buffer.extend(bytes([0] * (BLOCK_SIZE - len(buffer))))
            
        return bytes(buffer)

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
            raise M8IndexError("No empty modulator slots available in this instrument")
            
        self.modulators[slot] = modulator
        return slot
        
    def set_modulator(self, modulator, slot):
        if not (0 <= slot < len(self.modulators)):
            raise M8IndexError(f"Modulator slot index must be between 0 and {len(self.modulators)-1}")
            
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
    
