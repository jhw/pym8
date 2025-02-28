from m8.api import M8Block, M8IndexError, load_class
from m8.api.modulators import M8Modulators, create_default_modulators

INSTRUMENT_TYPES = {
    0x01: "m8.api.instruments.macrosynth.M8MacroSynth"
}

BLOCK_SIZE = 215
BLOCK_COUNT = 128
MODULATORS_OFFSET = 63

class M8FilterParams:
    """Class to handle filter parameters shared by multiple instrument types."""
    
    def __init__(self, offset=24, **kwargs):
        # Default parameter values
        self.type = 0x0
        self.cutoff = 0xFF
        self.resonance = 0x0
        
        # Store the offset where these parameters start in the binary data
        self.offset = offset
        
        # Apply any kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def read(cls, data, offset=24):
        """Read filter parameters from binary data starting at a specific offset"""
        instance = cls(offset)
        
        # Read values from appropriate offsets
        instance.type = data[offset]
        instance.cutoff = data[offset + 1]
        instance.resonance = data[offset + 2]
        
        return instance
    
    def write(self):
        """Write filter parameters to binary data"""
        buffer = bytearray()
        buffer.append(self.type)
        buffer.append(self.cutoff)
        buffer.append(self.resonance)
        return bytes(buffer)
    
    def clone(self):
        """Create a copy of this filter parameters object"""
        instance = self.__class__(self.offset)
        instance.type = self.type
        instance.cutoff = self.cutoff
        instance.resonance = self.resonance
        return instance
    
    def as_dict(self):
        """Convert filter parameters to dictionary for serialization"""
        return {
            "type": self.type,
            "cutoff": self.cutoff,
            "resonance": self.resonance
        }
    
    @classmethod
    def from_dict(cls, data, offset=24):
        """Create filter parameters from a dictionary"""
        instance = cls(offset)
        
        if "type" in data:
            instance.type = data["type"]
        if "cutoff" in data:
            instance.cutoff = data["cutoff"]
        if "resonance" in data:
            instance.resonance = data["resonance"]
            
        return instance
        
    @classmethod
    def from_prefixed_dict(cls, data, prefix="filter_", offset=24):
        """Create filter parameters from a dict with prefixed keys (e.g., filter_type)"""
        # Extract parameters with the prefix
        params = {}
        for key, value in data.items():
            if key.startswith(prefix):
                # Remove the prefix
                clean_key = key[len(prefix):]
                params[clean_key] = value
                
        return cls(offset, **params)


class M8AmpParams:
    """Class to handle amp parameters shared by multiple instrument types."""
    
    def __init__(self, offset=27, **kwargs):
        # Default parameter values
        self.level = 0x0
        self.limit = 0x0
        
        # Store the offset where these parameters start in the binary data
        self.offset = offset
        
        # Apply any kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def read(cls, data, offset=27):
        """Read amp parameters from binary data starting at a specific offset"""
        instance = cls(offset)
        
        # Read values from appropriate offsets
        instance.level = data[offset]
        instance.limit = data[offset + 1]
        
        return instance
    
    def write(self):
        """Write amp parameters to binary data"""
        buffer = bytearray()
        buffer.append(self.level)
        buffer.append(self.limit)
        return bytes(buffer)
    
    def clone(self):
        """Create a copy of this amp parameters object"""
        instance = self.__class__(self.offset)
        instance.level = self.level
        instance.limit = self.limit
        return instance
    
    def as_dict(self):
        """Convert amp parameters to dictionary for serialization"""
        return {
            "level": self.level,
            "limit": self.limit
        }
    
    @classmethod
    def from_dict(cls, data, offset=27):
        """Create amp parameters from a dictionary"""
        instance = cls(offset)
        
        if "level" in data:
            instance.level = data["level"]
        if "limit" in data:
            instance.limit = data["limit"]
            
        return instance
        
    @classmethod
    def from_prefixed_dict(cls, data, prefix="amp_", offset=27):
        """Create amp parameters from a dict with prefixed keys (e.g., amp_level)"""
        # Extract parameters with the prefix
        params = {}
        for key, value in data.items():
            if key.startswith(prefix):
                # Remove the prefix
                clean_key = key[len(prefix):]
                params[clean_key] = value
                
        return cls(offset, **params)


class M8MixerParams:
    """Class to handle mixer parameters shared by multiple instrument types."""
    
    def __init__(self, offset=29, **kwargs):
        # Default parameter values
        self.pan = 0x80
        self.dry = 0xC0
        self.chorus = 0x0
        self.delay = 0x0
        self.reverb = 0x0
        
        # Store the offset where these parameters start in the binary data
        self.offset = offset
        
        # Apply any kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def read(cls, data, offset=29):
        """Read mixer parameters from binary data starting at a specific offset"""
        instance = cls(offset)
        
        # Read values from appropriate offsets
        instance.pan = data[offset]
        instance.dry = data[offset + 1]
        instance.chorus = data[offset + 2]
        instance.delay = data[offset + 3]
        instance.reverb = data[offset + 4]
        
        return instance
    
    def write(self):
        """Write mixer parameters to binary data"""
        buffer = bytearray()
        buffer.append(self.pan)
        buffer.append(self.dry)
        buffer.append(self.chorus)
        buffer.append(self.delay)
        buffer.append(self.reverb)
        return bytes(buffer)
    
    def clone(self):
        """Create a copy of this mixer parameters object"""
        instance = self.__class__(self.offset)
        instance.pan = self.pan
        instance.dry = self.dry
        instance.chorus = self.chorus
        instance.delay = self.delay
        instance.reverb = self.reverb
        return instance
    
    def as_dict(self):
        """Convert mixer parameters to dictionary for serialization"""
        return {
            "pan": self.pan,
            "dry": self.dry,
            "chorus": self.chorus,
            "delay": self.delay,
            "reverb": self.reverb
        }
    
    @classmethod
    def from_dict(cls, data, offset=29):
        """Create mixer parameters from a dictionary"""
        instance = cls(offset)
        
        if "pan" in data:
            instance.pan = data["pan"]
        if "dry" in data:
            instance.dry = data["dry"]
        if "chorus" in data:
            instance.chorus = data["chorus"]
        if "delay" in data:
            instance.delay = data["delay"]
        if "reverb" in data:
            instance.reverb = data["reverb"]
            
        return instance
        
    @classmethod
    def from_prefixed_dict(cls, data, prefix="mixer_", offset=29):
        """Create mixer parameters from a dict with prefixed keys (e.g., mixer_pan)"""
        # Extract parameters with the prefix
        params = {}
        for key, value in data.items():
            if key.startswith(prefix):
                # Remove the prefix
                clean_key = key[len(prefix):]
                params[clean_key] = value
                
        return cls(offset, **params)


class M8InstrumentBase:
    def __init__(self, **kwargs):
        # Create modulators using the instrument type
        default_modulators = create_default_modulators(self.type)
        self.modulators = M8Modulators(instrument_type=self.type, items=default_modulators)
        
        # Apply any kwargs - specific to each instrument subclass
        for key, value in kwargs.items():
            if hasattr(self, key):
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

    def _read_parameters(self, data):
        # This method should be implemented by subclasses
        raise NotImplementedError("Subclasses must implement _read_parameters")
    
    def _write_parameters(self):
        # This method should be implemented by subclasses
        raise NotImplementedError("Subclasses must implement _write_parameters")

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
        result["modulators"] = self.modulators.as_dict()
        
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
        
        # Set type explicitly 
        instance.type = instr_type
        
        # Initialize with default values specific to the instrument type
        instance._init_default_parameters()
        
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
        
        # Set modulators
        if "modulators" in data:
            instance.modulators = M8Modulators.from_dict(data["modulators"], 
                                                       instrument_type=instance.type)
        else:
            # Create default modulators
            default_modulators = create_default_modulators(instance.type)
            instance.modulators = M8Modulators(instrument_type=instance.type, items=default_modulators)
        
        return instance

    def _init_default_parameters(self):
        # This method should be implemented by subclasses to set default parameter values
        raise NotImplementedError("Subclasses must implement _init_default_parameters")


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
    
    def as_dict(self):
        """Convert instruments to dictionary for serialization"""
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
        
        return {
            "items": items
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create instruments from a dictionary"""
        instance = cls.__new__(cls)
        list.__init__(instance)
        
        # Initialize with empty blocks
        for _ in range(BLOCK_COUNT):
            instance.append(M8Block())
        
        # Set instruments at their original positions
        if "items" in data:
            for instr_data in data["items"]:
                # Get index from data or default to 0
                index = instr_data.get("index", 0)
                if 0 <= index < BLOCK_COUNT:
                    # Remove index field before passing to from_dict
                    instr_dict = {k: v for k, v in instr_data.items() if k != "index"}
                    instance[index] = M8InstrumentBase.from_dict(instr_dict)
        
        return instance
