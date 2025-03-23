# m8/api/instruments.py
from m8.api import M8Block, load_class, join_nibbles, split_byte, read_fixed_string, write_fixed_string, serialize_enum, deserialize_enum
from m8.api.modulators import M8Modulators, create_default_modulators, M8Modulator
from m8.api.version import M8Version
from enum import Enum, auto
from m8.enums import M8InstrumentType
import importlib
import logging
from m8.config import (
    load_format_config, get_offset, get_instrument_type_id,
    get_instrument_modulators_offset, get_instrument_types,
    get_instrument_common_offsets, get_instrument_common_defaults
)

import random
import logging

# Load configuration
config = load_format_config()

# Instrument type mapping
INSTRUMENT_TYPES = get_instrument_types()

# Global counter for auto-generating instrument names
_INSTRUMENT_COUNTER = 0

# Block sizes and counts for instruments - from config
BLOCK_SIZE = config["instruments"]["block_size"]    # Size of each instrument in bytes
BLOCK_COUNT = config["instruments"]["count"]        # Maximum number of instruments

class M8ParamType(Enum):
    """Parameter data types for M8 instrument parameters."""
    UINT8 = auto()      # Standard 1-byte integer (0-255)
    STRING = auto()     # String type with variable length

class M8Params:
    """Dynamic parameter container for instrument parameters with support for different parameter types."""
    
    @staticmethod
    def calculate_parameter_size(param_defs):
        """Calculate the total size in bytes of all parameters."""
        total_size = 0
        for param_name, param_def in param_defs.items():
            start = param_def["offset"]
            size = param_def["size"]
            end = start + size
            total_size = max(total_size, end)
        return total_size
    
    def __init__(self, param_defs, **kwargs):
        """
        Initialize the parameter group with the given parameter definitions.
        """
        self._param_defs = param_defs
        
        # Initialize parameters with defaults
        for param_name, param_def in param_defs.items():
            default = param_def["default"]
            setattr(self, param_name, default)
        
        # Apply any kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def from_config(cls, instrument_type, **kwargs):
        """Create parameters from instrument type config."""
        config = load_format_config()
        
        # Load parameter definitions from config
        param_defs = config["instruments"][instrument_type]["params"].copy()
        
        # Special case for sampler: add sample_path from top level
        if instrument_type == "sampler" and "sample_path" in config["instruments"][instrument_type]:
            param_defs["sample_path"] = config["instruments"][instrument_type]["sample_path"]
            
        return cls(param_defs, **kwargs)
    
    def read(self, data):
        """Read parameters from binary data."""
        # Read values from their explicit offsets
        for param_name, param_def in self._param_defs.items():
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
                
            setattr(self, param_name, value)
    
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
        instance = self.__class__(self._param_defs)
        for param_name in self._param_defs.keys():
            setattr(instance, param_name, getattr(self, param_name))
        return instance
    
    def as_dict(self):
        """Convert parameters to dictionary for serialization."""
        result = {}
        
        for param_name, param_def in self._param_defs.items():
            value = getattr(self, param_name)
            
            # Handle enum parameters
            if "enums" in param_def:
                enum_classes = []
                
                # Import the enum classes dynamically
                for enum_path in param_def["enums"]:
                    try:
                        module_name, class_name = enum_path.rsplit('.', 1)
                        module = importlib.import_module(module_name)
                        enum_class = getattr(module, class_name)
                        enum_classes.append(enum_class)
                    except (ImportError, AttributeError) as e:
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Error importing enum {enum_path}: {e}")
                
                # If we have valid enum classes, try to convert and serialize
                if enum_classes:
                    # Try to convert to an enum instance if it's not already one
                    if not hasattr(value, 'name'):
                        for enum_class in enum_classes:
                            try:
                                if isinstance(value, int):
                                    value = enum_class(value)
                                    break  # Successfully converted to enum
                            except ValueError:
                                continue
                    
                    # Serialize the enum value or raw value
                    value = serialize_enum(value, param_name)
            
            result[param_name] = value
            
        return result
    
    @classmethod
    def from_dict(cls, instrument_type, data):
        """Create parameters from a dictionary."""
        params = cls.from_config(instrument_type)
        
        for param_name in params._param_defs.keys():
            if param_name in data:
                value = data[param_name]
                
                # Handle enum parameters
                param_def = params._param_defs[param_name]
                if "enums" in param_def:
                    enum_classes = []
                    
                    # Import the enum classes dynamically
                    for enum_path in param_def["enums"]:
                        try:
                            module_name, class_name = enum_path.rsplit('.', 1)
                            module = importlib.import_module(module_name)
                            enum_class = getattr(module, class_name)
                            enum_classes.append(enum_class)
                        except (ImportError, AttributeError) as e:
                            logger = logging.getLogger(__name__)
                            logger.warning(f"Error importing enum {enum_path}: {e}")
                    
                    # If we have valid enum classes, try to convert the value
                    if enum_classes:
                        # If it's a string, try to convert to enum value
                        if isinstance(value, str):
                            for enum_class in enum_classes:
                                try:
                                    value = enum_class[value].value
                                    break  # Found a matching enum
                                except KeyError:
                                    continue
                                    
                            # If we couldn't convert, log it
                            if isinstance(value, str):
                                logger = logging.getLogger(__name__)
                                logger.warning(f"Deserializing non-enum {param_name} string: {value}")
                
                setattr(params, param_name, value)
            
        return params

class M8Instrument:
    """Unified instrument class for all M8 instrument types."""
    
    # Get common parameter offsets from config
    common_offsets = get_instrument_common_offsets()
    
    # Common parameter offsets for all instrument types
    TYPE_OFFSET = common_offsets["type"]
    NAME_OFFSET = common_offsets["name"]
    NAME_LENGTH = common_offsets["name_length"]
    TRANSPOSE_EQ_OFFSET = common_offsets["transpose_eq"]
    TABLE_TICK_OFFSET = common_offsets["table_tick"]
    VOLUME_OFFSET = common_offsets["volume"]
    PITCH_OFFSET = common_offsets["pitch"]
    FINETUNE_OFFSET = common_offsets["finetune"]
    
    def __init__(self, instrument_type=None, **kwargs):
        """Initialize a new instrument with default parameters."""
        global _INSTRUMENT_COUNTER
        
        # Process instrument_type
        if instrument_type is None:
            # Default to wavsynth if not specified
            self.type = M8InstrumentType.WAVSYNTH
            instrument_type = "wavsynth"
        elif isinstance(instrument_type, int):
            # Convert type ID to enum
            try:
                self.type = M8InstrumentType(instrument_type)
                instrument_type = INSTRUMENT_TYPES[instrument_type]
            except (ValueError, KeyError):
                raise ValueError(f"Unknown instrument type ID: {instrument_type}")
        elif isinstance(instrument_type, M8InstrumentType):
            # If it's already an enum, use it directly
            self.type = instrument_type
            instrument_type = INSTRUMENT_TYPES[instrument_type.value]
        else:
            # Assume it's a string type name
            self.type = M8InstrumentType(get_instrument_type_id(instrument_type))
        
        # Set the instrument type name
        self.instrument_type = instrument_type
        
        # Initialize version (will be set from project or read from file)
        self.version = M8Version()
        
        # Generate sequential name if not provided
        if 'name' not in kwargs:
            # Use instrument type for name base
            base_name = instrument_type.upper()
            # Truncate or pad to 8 characters
            name_base = (base_name[:8] if len(base_name) > 8 else base_name.ljust(8))
            # Use global counter for 4-digit hex code
            counter_hex = f"{_INSTRUMENT_COUNTER & 0xFFFF:04X}"
            # Combine name components
            kwargs['name'] = f"{name_base}{counter_hex}"
            # Increment counter for next instrument
            _INSTRUMENT_COUNTER += 1
        
        # Get common default parameters from config
        common_defaults = get_instrument_common_defaults()
        
        # Common synthesizer parameters
        self.name = common_defaults["name"]
        self.transpose = common_defaults["transpose"]
        self.eq = common_defaults["eq"]
        self.table_tick = common_defaults["table_tick"]
        self.volume = common_defaults["volume"]
        self.pitch = common_defaults["pitch"]
        self.finetune = common_defaults["finetune"]  # Center value for fine tuning
        
        # Create params object based on instrument type
        self.params = M8Params.from_config(instrument_type)
        
        # Set up modulators
        self.modulators_offset = get_instrument_modulators_offset(instrument_type)
        self.modulators = M8Modulators(items=create_default_modulators())
        
        # Apply common parameters from kwargs
        for key, value in kwargs.items():
            if hasattr(self, key) and not key.startswith('_') and key not in ["modulators", "type", "params"]:
                setattr(self, key, value)
                
        # Apply instrument-specific parameters from kwargs to params object
        for key, value in kwargs.items():
            if hasattr(self.params, key):
                setattr(self.params, key, value)
    
    def _read_common_parameters(self, data):
        """Read common parameters shared by all instrument types."""
        self.type = data[self.TYPE_OFFSET]
        
        # Get the instrument type string from the type ID
        if self.type in INSTRUMENT_TYPES:
            self.instrument_type = INSTRUMENT_TYPES[self.type]
        else:
            # Default to wavsynth for unknown types
            self.instrument_type = "wavsynth"
        
        # Read name as a string (null-terminated) using utility function
        self.name = read_fixed_string(data, self.NAME_OFFSET, self.NAME_LENGTH)
        
        # Split byte into transpose/eq
        transpose_eq = data[self.TRANSPOSE_EQ_OFFSET]
        self.transpose, self.eq = split_byte(transpose_eq)
        
        self.table_tick = data[self.TABLE_TICK_OFFSET]
        self.volume = data[self.VOLUME_OFFSET]
        self.pitch = data[self.PITCH_OFFSET]
        self.finetune = data[self.FINETUNE_OFFSET]
        
        # Return the standard offset where instrument-specific params begin
        return 18

    def _read_parameters(self, data):
        """Read all instrument parameters from binary data."""
        # Read common parameters first
        next_offset = self._read_common_parameters(data)
        
        # Create and read the appropriate params object based on instrument type
        self.params = M8Params.from_config(self.instrument_type)
        self.params.read(data)
        
        # Set the modulators offset based on instrument type
        self.modulators_offset = get_instrument_modulators_offset(self.instrument_type)
        
        # Read modulators
        self.modulators = M8Modulators.read(data[self.modulators_offset:])

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
        buffer[self.FINETUNE_OFFSET] = self.finetune
        
        # Write instrument-specific parameters
        params_data = self.params.write()
        for param_name, param_def in self.params._param_defs.items():
            offset = param_def["offset"]
            size = param_def["size"]
            end = offset + size
            
            # Get the parameter value
            value = getattr(self.params, param_name)
            
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
        modulator_params = self.modulators.write()
        buffer[self.modulators_offset:self.modulators_offset + len(modulator_params)] = modulator_params
        
        # Return the finalized buffer
        return bytes(buffer)

    def is_empty(self):
        """Check if this instrument is empty."""
        # First check if the name is non-empty
        if self.name.strip() != "":
            return False
            
        # If name is empty, do additional checks based on instrument type
        if self.instrument_type == "wavsynth" or self.instrument_type == "macrosynth":
            # Check if shape or volume is non-zero, which would make it non-empty
            return self.volume == 0x0 and self.params.shape == 0x0
        elif self.instrument_type == "sampler":
            # Check if volume or sample_path is non-empty, which would make it non-empty
            return self.volume == 0x0 and getattr(self.params, "sample_path", "") == ""
        else:
            # Default to just checking name
            return True

    def clone(self):
        """Create a deep copy of this instrument."""
        # Create a new instance of this class with the same instrument type
        instance = self.__class__(instrument_type=self.instrument_type)
        
        # Copy all attributes
        for key, value in vars(self).items():
            if key == "modulators":
                # Clone modulators if they have a clone method
                instance.modulators = self.modulators.clone() if hasattr(self.modulators, 'clone') else self.modulators
            elif key == "params":
                # Clone params
                instance.params = self.params.clone() if hasattr(self.params, 'clone') else self.params
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
        # Start with the type and common parameters
        type_value = serialize_enum(self.type, 'instrument')
            
        result = {
            "type": type_value,
            "name": self.name,
            "transpose": self.transpose,
            "eq": self.eq,
            "table_tick": self.table_tick,
            "volume": self.volume,
            "pitch": self.pitch,
            "finetune": self.finetune
            # Version is deliberately excluded from serialization
        }
        
        # Add instrument-specific parameters
        params_dict = self.params.as_dict()
        for key, value in params_dict.items():
            result[key] = value
            
        # Add modulators
        result["modulators"] = self.modulators.as_list()
        
        return result

    @classmethod
    def from_dict(cls, data):
        """Create an instrument from a dictionary."""
        # Get the instrument type
        instr_type = data["type"]
        
        # Create a new instrument with the appropriate type
        # Handle both enum name strings and integer type IDs
        try:
            logger = logging.getLogger(__name__)
            
            instrument_type = deserialize_enum(M8InstrumentType, instr_type, 'instrument')
            instrument = cls(instrument_type=instrument_type)
            
            # Set common parameters
            for key in ["name", "transpose", "eq", "table_tick", "volume", "pitch", "finetune"]:
                if key in data:
                    setattr(instrument, key, data[key])
            
            # Create params object and set parameters
            instrument.params = M8Params.from_config(instrument.instrument_type)
            for key, value in data.items():
                if key not in ["name", "transpose", "eq", "table_tick", "volume", "pitch", "finetune", "type", "modulators"] and hasattr(instrument.params, key):
                    setattr(instrument.params, key, value)
            
            # Set modulators
            if "modulators" in data:
                instrument.modulators = M8Modulators.from_list(data["modulators"])
            
            return instrument
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid instrument type: {instr_type}. Error: {str(e)}")

    @classmethod
    def read(cls, data):
        """Read an instrument from binary data."""
        # Get the instrument type from the data
        instr_type = data[cls.TYPE_OFFSET]
        
        if instr_type in INSTRUMENT_TYPES:
            # Create a new instrument with the type from the data
            instrument = cls(instrument_type=instr_type)
            
            # Read all parameters
            instrument._read_parameters(data)
            
            return instrument
        else:
            # Return an M8Block for unknown types
            return M8Block.read(data)
            
    @classmethod
    def read_from_file(cls, file_path, expected_version=None):
        with open(file_path, "rb") as f:
            data = f.read()
        
        # Set up logging
        logger = logging.getLogger(__name__)
        
        # Read version from file
        version_offset = get_offset("version")
        version = M8Version.read(data[version_offset:])
        logger.info(f"M8 instrument file {file_path} has version {version}")
        
        # Check if version matches expected version if provided
        if expected_version is not None and str(version) != str(expected_version):
            raise ValueError(f"Version mismatch: instrument has version {version}, expected {expected_version}")
        
        # Read instrument data
        metadata_offset = get_offset("metadata")
        instrument_data = data[metadata_offset:]
        
        # Create instrument and store version
        instrument = cls.read(instrument_data)
        instrument.version = version
        
        return instrument
        
    def write_to_file(self, file_path):
        instrument_data = self.write()
        
        # Get offsets
        version_offset = get_offset("version")
        metadata_offset = get_offset("metadata")
            
        # Create data buffer with zeros for header and instrument data
        m8i_data = bytearray([0] * metadata_offset) + instrument_data
        
        # Write version
        version_data = self.version.write()
        m8i_data[version_offset:version_offset + len(version_data)] = version_data
        
        # Write file
        with open(file_path, "wb") as f:
            f.write(m8i_data)

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
                # Read using the base class read method
                instance.append(M8Instrument.read(block_data))
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
                    instance[index] = M8Instrument.from_dict(instr_dict)
        
        return instance

# No backward compatibility needed per project preferences