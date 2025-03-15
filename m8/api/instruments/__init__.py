from m8.api import M8Block, load_class, join_nibbles, split_byte
from m8.api.modulators import M8Modulators, create_default_modulators
from enum import Enum, auto

import random

# Instrument type definitions (mapping of type ID to class path)
INSTRUMENT_TYPES = {
    0x00: "m8.api.instruments.wavsynth.M8WavSynth",    # WavSynth instrument
    0x01: "m8.api.instruments.macrosynth.M8MacroSynth", # MacroSynth instrument
    0x02: "m8.api.instruments.sampler.M8Sampler"       # Sampler instrument
}

# Global counter for auto-generating instrument names
_INSTRUMENT_COUNTER = 0

# Block sizes and counts for instruments
BLOCK_SIZE = 215    # Size of each instrument in bytes
BLOCK_COUNT = 128   # Maximum number of instruments

class M8ParamType(Enum):
    """Parameter data types for M8 instrument parameters.
    
    Defines the supported data types for instrument parameters and determines
    how they are serialized and deserialized.
    """
    UINT8 = auto()      # Standard 1-byte integer (0-255)
    STRING = auto()     # String type with variable length

class M8ParamsBase:
    """Base class for instrument parameter groups with support for different parameter types.
    
    This class provides common functionality for defining, reading, and writing
    instrument parameters with different data types and byte offsets.
    """
    
    @staticmethod
    def calculate_parameter_size(param_defs):
        """Calculate the total size in bytes of all parameters.
        
        Args:
            param_defs: List of parameter definition tuples
            
        Returns:
            int: Total size in bytes required for the parameters
        """
        total_size = 0
        for param_def in param_defs:
            start = param_def[3]
            end = param_def[4]
            total_size += (end - start)
        return total_size
    
    def __init__(self, param_defs, offset=None, **kwargs):
        """
        Initialize the parameter group.
        
        Args:
            param_defs: List of tuples defining the parameters with format:
                (name, default, M8ParamType.TYPE, start, end)
                where start and end are byte offsets relative to the instrument start
            offset: Optional legacy offset parameter, maintained for backward compatibility only
            **kwargs: Parameter values to set
        """
        # Store the offset (for backwards compatibility only)
        if offset is not None:
            self.offset = offset
        
        # Initialize parameters with defaults
        for param_def in param_defs:
            name, default = param_def[0], param_def[1]
            setattr(self, name, default)
        
        # Apply any kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def read(cls, data, offset=None):
        """Read parameters from binary data starting at a specific offset.
        
        Args:
            data: Binary data containing parameter values
            offset: Optional offset to apply to parameter positions
            
        Returns:
            M8ParamsBase: New instance with parameters read from the data
        """
        # Create an instance with default values
        instance = cls(offset=offset)
        
        # Read values from their explicit offsets
        for param_def in instance._param_defs:
            name, _, param_type, start, end = param_def
            param_size = end - start
            
            if param_type == M8ParamType.UINT8:
                # Read a single byte
                value = data[start]
            elif param_type == M8ParamType.STRING:
                # Read a string of specified length (determined by end - start)
                string_bytes = data[start:end]
                
                # Convert to string, stopping at null terminator if present
                null_pos = string_bytes.find(0)
                if null_pos != -1:
                    string_bytes = string_bytes[:null_pos]
                
                value = string_bytes.decode('utf-8', errors='replace')
            else:
                # Default to UINT8 for unknown types
                value = data[start]
                
            setattr(instance, name, value)
        
        return instance
    
    def write(self):
        """Convert parameters to binary data.
        
        Creates a buffer sized to fit all parameters and writes each parameter
        value to its specified position in the buffer.
        
        Returns:
            bytes: Binary representation of all parameters
        """
        # Find the largest end offset to determine buffer size
        max_end = max(param_def[4] for param_def in self._param_defs)
        buffer = bytearray([0] * max_end)
        
        for param_def in self._param_defs:
            name, _, param_type, start, end = param_def
            value = getattr(self, name)
            param_size = end - start
            
            if param_type == M8ParamType.UINT8:
                # Write a single byte
                buffer[start] = value & 0xFF
            elif param_type == M8ParamType.STRING:
                # Write a string of specified length (end - start)
                # Convert to bytes, pad with nulls
                if isinstance(value, str):
                    encoded = value.encode('utf-8')
                    # Truncate or pad to exactly the right size
                    if len(encoded) > param_size:
                        encoded = encoded[:param_size]
                    else:
                        encoded = encoded + bytes([0] * (param_size - len(encoded)))
                    
                    buffer[start:end] = encoded
                else:
                    # Handle non-string values by padding with nulls
                    buffer[start:end] = bytes([0] * param_size)
            else:
                # Default to UINT8 for unknown types
                buffer[start] = value & 0xFF
        
        return bytes(buffer[:max_end])
    
    def clone(self):
        """Create a deep copy of this parameter object.
        
        Returns:
            M8ParamsBase: New instance with the same parameter values
        """
        instance = self.__class__()
        for param_def in self._param_defs:
            name = param_def[0]
            setattr(instance, name, getattr(self, name))
        return instance
    
    def as_dict(self):
        """Convert parameters to dictionary for serialization.
        
        Returns:
            dict: Dictionary mapping parameter names to their values
        """
        return {param_def[0]: getattr(self, param_def[0]) for param_def in self._param_defs}
    
    @classmethod
    def from_dict(cls, data, offset=None):
        """Create parameters from a dictionary.
        
        Args:
            data: Dictionary containing parameter values
            offset: Optional offset to apply to parameter positions
            
        Returns:
            M8ParamsBase: New instance with parameters from the dictionary
        """
        instance = cls(offset=offset)
        
        for param_def in instance._param_defs:
            name = param_def[0]
            if name in data:
                setattr(instance, name, data[name])
            
        return instance

class M8InstrumentBase:
    """Base class for all M8 instruments.
    
    Provides common functionality for all instrument types including parameter 
    reading/writing, serialization, and modulators. Specific instrument types
    inherit from this class and add their own specialized parameters.
    """
    
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
        """Initialize a new instrument with default parameters.
        
        Generates an automatic name if one is not provided. Sets up common parameters
        and initializes modulators if supported by the instrument type.
        
        Args:
            **kwargs: Optional parameter values to override defaults
        """
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
        """Read common parameters shared by all instrument types.
        
        Extracts the basic parameters that all instrument types have in common
        from their standard positions in the binary data.
        
        Args:
            data: Binary data containing instrument parameters
            
        Returns:
            int: The offset where instrument-specific parameters begin
        """
        self.type = data[self.TYPE_OFFSET]
        
        # Read name as a string (null-terminated)
        name_bytes = data[self.NAME_OFFSET:self.NAME_OFFSET+self.NAME_LENGTH]
        null_term_idx = name_bytes.find(0)
        if null_term_idx != -1:
            name_bytes = name_bytes[:null_term_idx]
        self.name = name_bytes.decode('utf-8', errors='replace')
        
        # Split byte into transpose/eq
        transpose_eq = data[self.TRANSPOSE_EQ_OFFSET]
        self.transpose, self.eq = split_byte(transpose_eq)
        
        self.table_tick = data[self.TABLE_TICK_OFFSET]
        self.volume = data[self.VOLUME_OFFSET]
        self.pitch = data[self.PITCH_OFFSET]
        self.finetune = data[self.FINETUNE_OFFSET]  # renamed from fine_tune
        
        # Return a fixed synth offset for backward compatibility with subclasses
        # that may still use it during transition - in the future this can be removed
        return 18  # This was the original SYNTH_OFFSET value

    def _read_parameters(self, data):
        """Read all instrument parameters from binary data.
        
        First reads common parameters, then passes control to the instrument-specific
        parameter reader, and finally reads modulators if supported.
        
        Args:
            data: Binary data containing instrument parameters
        """
        # Read common parameters first
        next_offset = self._read_common_parameters(data)
        
        # Read synth-specific parameters in subclass (includes filter, amp, mixer params)
        self._read_specific_parameters(data, next_offset)
        
        # Read modulators if offset is defined
        # Modulators still need an offset as they're handled differently
        if hasattr(self, 'MODULATORS_OFFSET'):
            self.modulators = M8Modulators.read(data[self.MODULATORS_OFFSET:])

    def write(self):
        """Convert the instrument to binary data.
        
        Creates a properly sized buffer and writes all parameters at their exact
        offsets, handling both common parameters and instrument-specific parameters.
        
        Returns:
            bytes: Binary representation of the instrument
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
        buffer[self.FINETUNE_OFFSET] = self.finetune  # renamed from fine_tune
        
        # Write synth-specific parameters (includes filter, amp, mixer params)
        if hasattr(self, 'synth'):
            # The parameters have their positions defined correctly in the param_defs
            # but are compacted at position 0 in the synth_params buffer
            # We need to reapply them at their correct positions
            
            for param_def in self.synth._param_defs:
                name, _, param_type, start, end = param_def
                value = getattr(self.synth, name)
                
                if param_type == M8ParamType.UINT8:
                    # Write a single byte
                    buffer[start] = value & 0xFF
                elif param_type == M8ParamType.STRING:
                    # Write a string (with proper handling)
                    if isinstance(value, str):
                        encoded = value.encode('utf-8')
                        param_size = end - start
                        if len(encoded) > param_size:
                            encoded = encoded[:param_size]
                        else:
                            encoded = encoded + bytes([0] * (param_size - len(encoded)))
                        buffer[start:end] = encoded
                    else:
                        # Null padding
                        buffer[start:end] = bytes([0] * (end - start))
                else:
                    # Default to UINT8
                    buffer[start] = value & 0xFF
        
        # Write modulators
        # Modulators still need an offset as they're handled differently
        if hasattr(self, 'MODULATORS_OFFSET') and hasattr(self, 'modulators'):
            modulator_params = self.modulators.write()
            buffer[self.MODULATORS_OFFSET:self.MODULATORS_OFFSET + len(modulator_params)] = modulator_params
        
        # Return the finalized buffer
        
        return bytes(buffer)

    def _write_specific_parameters(self):
        """Write synth-specific parameters. To be implemented by subclasses.
        
        Returns:
            bytes: Binary representation of the instrument-specific parameters
        """
        return self.synth.write()

    def is_empty(self):
        """Check if this instrument is empty.
        
        This is a basic implementation that should be overridden by subclasses
        with instrument-specific logic.
        
        Returns:
            bool: True if the instrument is considered empty
        """
        return self.name.strip() == ""

    def clone(self):
        """Create a deep copy of this instrument.
        
        Creates a new instance and copies all attributes, handling special cases
        like modulators and synth parameters that need their own cloning methods.
        
        Returns:
            M8InstrumentBase: New instance with the same values
        """
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
        """Find the first available (empty) modulator slot.
        
        Returns:
            int: Index of the first empty slot, or None if all slots are used
        """
        for slot_idx, mod in enumerate(self.modulators):
            if isinstance(mod, M8Block) or mod.destination == 0:
                return slot_idx
        return None

    def add_modulator(self, modulator):
        """Add a modulator to the first available slot.
        
        Args:
            modulator: The modulator to add
            
        Returns:
            int: The index where the modulator was added
            
        Raises:
            IndexError: If no empty slots are available
        """
        slot = self.available_modulator_slot
        if slot is None:
            raise IndexError("No empty modulator slots available in this instrument")
            
        self.modulators[slot] = modulator
        return slot
        
    def set_modulator(self, modulator, slot):
        """Set a modulator at a specific slot.
        
        Args:
            modulator: The modulator to set
            slot: The slot index to set
            
        Raises:
            IndexError: If the slot index is out of range
        """
        if not (0 <= slot < len(self.modulators)):
            raise IndexError(f"Modulator slot index must be between 0 and {len(self.modulators)-1}")
            
        self.modulators[slot] = modulator

    def as_dict(self):
        """Convert instrument to dictionary for serialization.
        
        Creates a flat dictionary structure that includes instrument type,
        common parameters, synth-specific parameters, and modulators.
        
        Returns:
            dict: Dictionary representation of the instrument
        """
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
        """Create an instrument from a dictionary.
        
        Creates the appropriate instrument type based on the 'type' field
        and initializes it with values from the dictionary.
        
        Args:
            data: Dictionary containing instrument parameters
            
        Returns:
            M8InstrumentBase: New instance of the appropriate instrument type
            
        Raises:
            ValueError: If the instrument type is unknown
        """
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
        """Read an instrument from binary data.
        
        Creates the appropriate instrument type based on the type byte in the data
        and initializes it with values read from the binary data.
        
        Args:
            data: Binary data containing an instrument
            
        Returns:
            M8InstrumentBase: New instance of the appropriate instrument type,
                              or M8Block if the type is unknown or empty
        """
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
    """Collection of M8 instruments.
    
    Represents the set of instruments in an M8 project. Extends the built-in
    list type with M8-specific serialization and deserialization functionality.
    """
    
    def __init__(self, items=None):
        """Initialize a collection with optional instruments.
        
        Args:
            items: Optional list of instruments to initialize with
        """
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
