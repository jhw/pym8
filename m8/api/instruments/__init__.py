from m8.api import M8Block, M8IndexError, load_class
from m8.api.modulators import M8Modulators, create_default_modulators

INSTRUMENT_TYPES = {
    0x01: "m8.api.instruments.macrosynth.M8MacroSynth"
}

BLOCK_SIZE = 215
BLOCK_COUNT = 128
MODULATORS_OFFSET = 63

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
            if key != "modulators" and key != "__class__" and hasattr(instance, key):
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
                item_dict = instr.as_dict() if hasattr(instr, 'as_dict') else {"__class__": "m8.M8Block"}
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
