from m8.api import M8Block, M8IndexError, load_class
from m8.api.modulators import M8Modulators, create_default_modulators

INSTRUMENT_TYPES = {
    0x01: "m8.api.instruments.macrosynth.M8MacroSynth"
}

BLOCK_SIZE = 215
BLOCK_COUNT = 128
SYNTH_PARAMS_SIZE = 33
MODULATORS_OFFSET = 63

class M8InstrumentBase:
    def __init__(self, **kwargs):
        # Get params class path from instrument path
        params_path = f"{INSTRUMENT_TYPES[0x01]}Params"  # For now hardcoded to MacroSynth
        params_class = load_class(params_path)
        self.synth_params = params_class(**kwargs)
        
        # Create modulators using the type from synth params
        default_modulators = create_default_modulators(self.synth_params.type)
        self.modulators = M8Modulators(instrument_type=self.synth_params.type, items=default_modulators)

    @classmethod
    def read(cls, data):
        # Get the type from the first byte and validate
        instr_type = data[0]
        if instr_type not in INSTRUMENT_TYPES:
            raise ValueError(f"Unknown instrument type: {instr_type}")
            
        # Create instance and load its params
        instance = cls.__new__(cls)
        params_path = f"{INSTRUMENT_TYPES[instr_type]}Params"
        params_class = load_class(params_path)
        instance.synth_params = params_class.read(data[:SYNTH_PARAMS_SIZE])
        
        # Create modulators based on the loaded params
        instance.modulators = M8Modulators.read(data[MODULATORS_OFFSET:], 
                                               instrument_type=instance.synth_params.type)
        
        return instance

    def write(self):
        buffer = bytearray()
        buffer.extend(self.synth_params.write())
        buffer.extend(bytes([0] * (MODULATORS_OFFSET - SYNTH_PARAMS_SIZE)))
        buffer.extend(self.modulators.write())
        return bytes(buffer)

    def is_empty(self):
        # An instrument is considered empty if its synth params are empty
        return self.synth_params.is_empty() if hasattr(self.synth_params, 'is_empty') else False

    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        instance.synth_params = self.synth_params.clone() if hasattr(self.synth_params, 'clone') else self.synth_params
        instance.modulators = self.modulators.clone() if hasattr(self.modulators, 'clone') else self.modulators
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
        # Filter out empty modulators
        modulators_list = []
        for mod in self.modulators:
            # Include modulator if it has as_dict and is not empty
            if hasattr(mod, "as_dict") and not (hasattr(mod, "is_empty") and mod.is_empty()):
                modulators_list.append(mod.as_dict())
    
        return {
            "type": self.synth_params.type,
            "synth_params": self.synth_params.as_dict(),
            "modulators": modulators_list
        }
                    
    @classmethod
    def from_dict(cls, data):
        """Create an instrument from a dictionary"""
        instance = cls.__new__(cls)
        
        # Get synth params class
        if "type" in data and "synth_params" in data:
            instr_type = data["type"]
            if instr_type in INSTRUMENT_TYPES:
                params_path = f"{INSTRUMENT_TYPES[instr_type]}Params"
                params_class = load_class(params_path)
                instance.synth_params = params_class.from_dict(data["synth_params"])
        
        # Deserialize modulators
        if "modulators" in data:
            # Create appropriate modulators collection
            instance.modulators = M8Modulators(instrument_type=instance.synth_params.type)
            
            from m8.api.modulators import MODULATOR_TYPES
            
            for i, mod_data in enumerate(data["modulators"]):
                if mod_data is not None and i < len(instance.modulators):
                    # Determine modulator type
                    if "type" in mod_data and instance.synth_params.type in MODULATOR_TYPES:
                        mod_type = mod_data["type"]
                        if mod_type in MODULATOR_TYPES[instance.synth_params.type]:
                            ModClass = load_class(MODULATOR_TYPES[instance.synth_params.type][mod_type])
                            instance.modulators[i] = ModClass.from_dict(mod_data)
        
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
                # Create the specific instrument class
                InstrClass = load_class(INSTRUMENT_TYPES[instr_type])
                instance.append(InstrClass.read(block_data))
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
