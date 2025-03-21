# m8/api/instruments/__init__.py
from m8.api import M8Block, load_class, join_nibbles, split_byte, read_fixed_string, write_fixed_string
from m8.api.modulators import M8Modulators, create_default_modulators
from enum import Enum, auto
from m8.config import load_format_config, get_instrument_type_id

import random

# Load configuration
config = load_format_config()

# Instrument type definitions (mapping of type ID to class path)
INSTRUMENT_TYPES = {
    0x00: "m8.api.instruments.wavsynth.M8WavSynth",    # WavSynth instrument
    0x01: "m8.api.instruments.macrosynth.M8MacroSynth", # MacroSynth instrument
    0x02: "m8.api.instruments.sampler.M8Sampler"       # Sampler instrument
}

# Global counter for auto-generating instrument names
_INSTRUMENT_COUNTER = 0

# Block sizes and counts for instruments - from config
BLOCK_SIZE = config["instruments"]["block_size"]    # Size of each instrument in bytes
BLOCK_COUNT = config["instruments"]["count"]        # Maximum number of instruments

class M8ParamType(Enum):
    """Parameter data types for M8 instrument parameters."""
    UINT8 = auto()      # Standard 1-byte integer (0-255)
    STRING = auto()     # String type with variable length

class M8ParamsBase:
    """Base class for instrument parameter groups with support for different parameter types."""
    
    @staticmethod
    def calculate_parameter_size(param_defs):
        """Calculate the total size in bytes of all parameters."""
        total_size = 0
        for param_name, param_def in param_defs.items():
            start = param_def["offset"]
            size = param_def["size"]
            total_size += size
        return total_size
    
    def __init__(self, param_defs, **kwargs):
        """
        Initialize the parameter group.
        """
        # Initialize parameters with defaults
        for param_name, param_def in param_defs.items():
            default = param_def["default"]
            setattr(self, param_name, default)
        
        # Apply any kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def read(cls, data):
        """Read parameters from binary data."""
        # Create an instance with default values
        instance = cls()
        
        # Read values from their explicit offsets
        for param_name, param_def in instance._param_defs.items():
            offset = param_def["offset"]
            size = param_def["size"]
            end = offset + size
            
            # Get parameter type (enum value or use UINT8 as default)
            param_type = M8ParamType.UINT8
            if "type" in param_def:
                type_name = param_def["type"]
                if type_name == "STRING":
                    param_type = M8ParamType.STRING
            
            if param_type == M8ParamType.UINT8:
                # Read a single byte
                value = data[offset]
            elif param_type == M8ParamType.STRING:
                # Read a string of specified length using utility function
                value = read_fixed_string(data, offset, size)
            else:
                # Default to UINT8 for unknown types
                value = data[offset]
                
            setattr(instance, param_name, value)
        
        return instance
    
    def write(self):
        """Convert parameters to binary data."""
        # Find the largest end offset to determine buffer size
        max_end = 0
        for param_name, param_def in self._param_defs.items():
            offset = param_def["offset"]
            size = param_def["size"]
            end = offset + size
            max_end = max(max_end, end)
            
        buffer = bytearray([0] * max_end)
        
        for param_name, param_def in self._param_defs.items():
            offset = param_def["offset"]
            size = param_def["size"]
            end = offset + size
            value = getattr(self, param_name)
            
            # Get parameter type (enum value or use UINT8 as default)
            param_type = M8ParamType.UINT8
            if "type" in param_def:
                type_name = param_def["type"]
                if type_name == "STRING":
                    param_type = M8ParamType.STRING
            
            if param_type == M8ParamType.UINT8:
                # Write a single byte
                buffer[offset] = value & 0xFF
            elif param_type == M8ParamType.STRING:
                # Write a string of specified length using utility function
                if isinstance(value, str):
                    buffer[offset:end] = write_fixed_string(value, size)
                else:
                    # Handle non-string values by padding with nulls
                    buffer[offset:end] = bytes([0] * size)
            else:
                # Default to UINT8 for unknown types
                buffer[offset] = value & 0xFF
        
        return bytes(buffer[:max_end])
    
    def clone(self):
        """Create a deep copy of this parameter object."""
        instance = self.__class__()
        for param_name in self._param_defs.keys():
            setattr(instance, param_name, getattr(self, param_name))
        return instance
    
    def as_dict(self):
        """Convert parameters to dictionary for serialization."""
        return {param_name: getattr(self, param_name) for param_name in self._param_defs.keys()}
    
    @classmethod
    def from_dict(cls, data):
        """Create parameters from a dictionary."""
        instance = cls()
        
        for param_name in instance._param_defs.keys():
            if param_name in data:
                setattr(instance, param_name, data[param_name])
            
        return instance

class M8InstrumentBase:
    """Base class for all M8 instruments."""
    
    # Common parameter offsets for all instrument types
    TYPE_OFFSET = 0        # Instrument type ID
    NAME_OFFSET = 1        # Start of instrument name
    NAME_LENGTH = 12       # Maximum name length
    TRANSPOSE_EQ_OFFSET = 13  # Combined transpose and EQ settings
    TABLE_TICK_OFFSET = 14    # Table tick rate
    VOLUME_OFFSET = 15        # Instrument volume
    PITCH_OFFSET = 16         # Pitch offset
    FINETUNE_OFFSET = 17      # Fine pitch tuning
    
    def __init__(self, **kwargs):
        """Initialize a new instrument with default parameters."""
        global _INSTRUMENT_COUNTER
        
        # Generate sequential name if not provided
        if 'name' not in kwargs:
            # Get class name without the M8 prefix
            base_name = self.__class__.__name__[2:].upper()
            # Truncate or pad to 8 characters
            name_base = (base_name[:8] if len(base_name) > 8 else base_name.ljust(8))
            # Use global counter for 4-digit hex code
            counter_hex = f"{_INSTRUMENT_COUNTER & 0xFFFF:04X}"
            # Combine name components
            kwargs['name'] = f"{name_base}{counter_hex}"
            # Increment counter for next instrument
            _INSTRUMENT_COUNTER += 1
        
        # Common synthesizer parameters
        self.name = " "
        self.transpose = 0x4
        self.eq = 0x1
        self.table_tick = 0x01
        self.volume = 0x0
        self.pitch = 0x0
        self.finetune = 0x80  # Center value for fine tuning
        
        # Create modulators if MODULATORS_OFFSET is defined by the subclass
        # Modulators offset is still needed as it's handled differently
        if hasattr(self, 'MODULATORS_OFFSET'):
            self.modulators = M8Modulators(items=create_default_modulators())
        
        # Apply any remaining kwargs to base class attributes
        for key, value in kwargs.items():
            if hasattr(self, key) and not key.startswith('_') and key not in ["modulators", "type", "synth"]:
                setattr(self, key, value)
    
    def _read_common_parameters(self, data):
        """Read common parameters shared by all instrument types."""
        self.type = data[self.TYPE_OFFSET]
        
        # Read name as a string (null-terminated) using utility function
        self.name = read_fixed_string(data, self.NAME_OFFSET, self.NAME_LENGTH)
        
        # Split byte into transpose/eq
        transpose_eq = data[self.TRANSPOSE_EQ_OFFSET]
        self.transpose, self.eq = split_byte(transpose_eq)
        
        self.table_tick = data[self.TABLE_TICK_OFFSET]
        self.volume = data[self.VOLUME_OFFSET]
        self.pitch = data[self.PITCH_OFFSET]
        self.finetune = data[self.FINETUNE_OFFSET]
        
        # Standardized position where instrument-specific params begin
        return 18

    def _read_parameters(self, data):
        """Read all instrument parameters from binary data."""
        # Read common parameters first
        next_offset = self._read_common_parameters(data)
        
        # Read synth-specific parameters in subclass (includes filter, amp, mixer params)
        self._read_specific_parameters(data, next_offset)
        
        # Read modulators if offset is defined
        # Modulators still need an offset as they're handled differently
        if hasattr(self, 'MODULATORS_OFFSET'):
            self.modulators = M8Modulators.read(data[self.MODULATORS_OFFSET:])

    def write(self):
        """Convert the instrument to binary data."""
        # Create a buffer of the correct size
        buffer = bytearray([0] * BLOCK_SIZE)
        
        # Write type
        buffer[self.TYPE_OFFSET] = self.type
        
        # Write name (padded to NAME_LENGTH bytes) using utility function
        name_bytes = write_fixed_string(self.name, self.NAME_LENGTH)
        buffer[self.NAME_OFFSET:self.NAME_OFFSET+self.NAME_LENGTH] = name_bytes
        
        # Write transpose/eq
        buffer[self.TRANSPOSE_EQ_OFFSET] = join_nibbles(self.transpose, self.eq)
        
        # Write remaining common parameters
        buffer[self.TABLE_TICK_OFFSET] = self.table_tick
        buffer[self.VOLUME_OFFSET] = self.volume
        buffer[self.PITCH_OFFSET] = self.pitch
        buffer[self.FINETUNE_OFFSET] = self.finetune  # renamed from fine_tune
        
        # Write synth-specific parameters (includes filter, amp, mixer params)
        if hasattr(self, 'synth'):
            # The parameters have their positions defined correctly in the param_defs
            # but are compacted at position 0 in the synth_params buffer
            # We need to reapply them at their correct positions
            
            for param_name, param_def in self.synth._param_defs.items():
                offset = param_def["offset"]
                size = param_def["size"]
                end = offset + size
                value = getattr(self.synth, param_name)
                
                # Get parameter type (enum value or use UINT8 as default)
                param_type = M8ParamType.UINT8
                if "type" in param_def:
                    type_name = param_def["type"]
                    if type_name == "STRING":
                        param_type = M8ParamType.STRING
                
                if param_type == M8ParamType.UINT8:
                    # Write a single byte
                    buffer[offset] = value & 0xFF
                elif param_type == M8ParamType.STRING:
                    # Write a string using utility function
                    if isinstance(value, str):
                        buffer[offset:end] = write_fixed_string(value, size)
                    else:
                        # Null padding
                        buffer[offset:end] = bytes([0] * size)
                else:
                    # Default to UINT8
                    buffer[offset] = value & 0xFF
        
        # Write modulators
        # Modulators still need an offset as they're handled differently
        if hasattr(self, 'MODULATORS_OFFSET') and hasattr(self, 'modulators'):
            modulator_params = self.modulators.write()
            buffer[self.MODULATORS_OFFSET:self.MODULATORS_OFFSET + len(modulator_params)] = modulator_params
        
        # Return the finalized buffer
        
        return bytes(buffer)

    def _write_specific_parameters(self):
        """Write synth-specific parameters. To be implemented by subclasses."""
        return self.synth.write()

    def is_empty(self):
        """Check if this instrument is empty."""
        return self.name.strip() == ""

    def clone(self):
        """Create a deep copy of this instrument."""
        # Create a new instance of the same class
        instance = self.__class__.__new__(self.__class__)
        
        # Copy all attributes
        for key, value in vars(self).items():
            if key == "modulators":
                # Clone modulators if they have a clone method
                instance.modulators = self.modulators.clone() if hasattr(self.modulators, 'clone') else self.modulators
            elif hasattr(value, 'clone') and callable(getattr(value, 'clone')):
                # Clone other objects with clone method (like filter, amp, mixer, synth)
                setattr(instance, key, value.clone())
            else:
                setattr(instance, key, value)
                
        return instance

    @property
    def available_modulator_slot(self):
        """Find the first available (empty) modulator slot."""
        for slot_idx, mod in enumerate(self.modulators):
            if isinstance(mod, M8Block) or mod.destination == 0:
                return slot_idx
        return None

    def add_modulator(self, modulator):
        """Add a modulator to the first available slot."""
        slot = self.available_modulator_slot
        if slot is None:
            raise IndexError("No empty modulator slots available in this instrument")
            
        self.modulators[slot] = modulator
        return slot
        
    def set_modulator(self, modulator, slot):
        """Set a modulator at a specific slot."""
        if not (0 <= slot < len(self.modulators)):
            raise IndexError(f"Modulator slot index must be between 0 and {len(self.modulators)-1}")
            
        self.modulators[slot] = modulator

    def as_dict(self):
        """Convert instrument to dictionary for serialization."""
        # This is a base implementation that should be extended by subclasses
        result = {"type": self.type}
        
        # Add all base instance variables except those starting with underscore
        for key, value in vars(self).items():
            if not key.startswith('_') and key != "modulators" and key != "type" and key != "synth":
                result[key] = value
        
        # Add synth parameters with flattened structure
        if hasattr(self, 'synth'):
            synth_dict = self.synth.as_dict()
            for key, value in synth_dict.items():
                result[key] = value
                
        # Add modulators separately
        if hasattr(self, 'modulators'):
            result["modulators"] = self.modulators.as_list()
        
        return result

    @classmethod
    def from_dict(cls, data):
        """Create an instrument from a dictionary."""
        # Get the instrument type and create the appropriate class
        instr_type = data["type"]
        if instr_type not in INSTRUMENT_TYPES:
            raise ValueError(f"Unknown instrument type: {instr_type}")
        
        # Create the specific instrument class
        instr_class = load_class(INSTRUMENT_TYPES[instr_type])
        instance = instr_class.__new__(instr_class)
    
        # Set type explicitly before initialization
        instance.type = instr_type
    
        # Initialize with default values first
        instance.__init__()  # This will call the actual constructor with no args
    
        # Set all base parameters from dict
        synth_params = {}
        base_params = {}
        
        for key, value in data.items():
            if key != "modulators" and key != "__class__":
                # Check if this is a synth parameter
                if hasattr(instance.synth, key):
                    synth_params[key] = value
                # Otherwise it's a base parameter
                elif hasattr(instance, key):
                    base_params[key] = value
        
        # Apply base parameters
        for key, value in base_params.items():
            setattr(instance, key, value)
            
        # Apply synth parameters
        for key, value in synth_params.items():
            setattr(instance.synth, key, value)
    
        # Set modulators
        if "modulators" in data:
            instance.modulators = M8Modulators.from_list(data["modulators"])
    
        return instance

    @classmethod
    def read(cls, data):
        """Read an instrument from binary data."""
        # Get the instrument type from the data
        instr_type = data[cls.TYPE_OFFSET]
        
        if instr_type in INSTRUMENT_TYPES:
            # Create the specific instrument class
            class_name = INSTRUMENT_TYPES[instr_type]
            instr_class = load_class(class_name)
            instance = instr_class.__new__(instr_class)
            
            # Initialize the instance with default values
            instance.__init__()
            
            # Read parameters
            instance._read_parameters(data)
            
            return instance
        else:
            # Return an M8Block for unknown types
            return M8Block.read(data)

class M8Instruments(list):
    """Collection of M8 instruments."""
    
    def __init__(self, items=None):
        """Initialize a collection with optional instruments."""
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
        for i, instr in enumerate(self):
            instr_data = instr.write() if hasattr(instr, 'write') else bytes([0] * BLOCK_SIZE)
            
            # Ensure each instrument occupies exactly BLOCK_SIZE bytes
            if len(instr_data) < BLOCK_SIZE:
                instr_data = instr_data + bytes([0x0] * (BLOCK_SIZE - len(instr_data)))
            elif len(instr_data) > BLOCK_SIZE:
                instr_data = instr_data[:BLOCK_SIZE]
            
            result.extend(instr_data)
            
        # Return the complete instrument data
            
        return bytes(result)
    
    def as_list(self):
        """Convert instruments to list for serialization."""
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
        """Create instruments from a list."""
        instance = cls.__new__(cls)
        list.__init__(instance)
        
        # Initialize with empty blocks
        for _ in range(BLOCK_COUNT):
            instance.append(M8Block())
        
        # Set instruments at their original positions
        if items:
            for instr_data in items:
                # Get index from data
                index = instr_data["index"]
                if 0 <= index < BLOCK_COUNT:
                    # Remove index field before passing to from_dict
                    instr_dict = {k: v for k, v in instr_data.items() if k != "index"}
                    instance[index] = M8InstrumentBase.from_dict(instr_dict)
        
        return instance