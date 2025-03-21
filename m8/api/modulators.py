from m8.api import M8Block, load_class, split_byte, join_nibbles
from enum import Enum
from m8.config import load_format_config, get_modulator_types, get_modulator_type_id, get_modulator_data

# Load configuration
config = load_format_config()["modulators"]

# Module-level constants
BLOCK_SIZE = config["block_size"]
BLOCK_COUNT = config["count"]

# Type mapping from IDs to names - loaded from config
MODULATOR_TYPES = get_modulator_types()

# Default modulator configurations
DEFAULT_MODULATOR_CONFIGS = config["default_config"]  # 2 AHD envelopes, 2 LFOs

# Modulator type enum
class ModulatorType(Enum):
    AHD_ENVELOPE = "ahd_envelope"
    ADSR_ENVELOPE = "adsr_envelope"
    DRUM_ENVELOPE = "drum_envelope"
    LFO = "lfo"
    TRIGGER_ENVELOPE = "trigger_envelope"
    TRACKING_ENVELOPE = "tracking_envelope"
    
    @classmethod
    def get_type_id(cls, type_name):
        """Get the numeric type ID from the type name."""
        return get_modulator_type_id(type_name)
    
    @classmethod
    def from_id(cls, type_id):
        """Get the enum value from a numeric type ID."""
        for type_enum in cls:
            if get_modulator_type_id(type_enum.value) == type_id:
                return type_enum
        return None

class M8ModulatorParams:
    """Dynamic parameter container for modulator parameters."""
    
    def __init__(self, param_defs, **kwargs):
        """Initialize the parameter group with the given parameter definitions."""
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
    def from_config(cls, modulator_type, **kwargs):
        """Create parameters from modulator type config."""
        config = load_format_config()
        
        # Load parameter definitions from config
        param_defs = config["modulators"]["types"][modulator_type]["params"].copy()
        
        return cls(param_defs, **kwargs)
    
    def read(self, data):
        """Read parameters from binary data."""
        # Read values from their explicit offsets
        for param_name, param_def in self._param_defs.items():
            if 'nibble' in param_def:
                # This is a special case for destination which is stored in a nibble
                continue
                
            offset = param_def["offset"]
            if offset < len(data):
                value = data[offset]
                setattr(self, param_name, value)
    
    def write(self):
        """Convert parameters to binary data."""
        # Find the largest end offset to determine buffer size
        max_offset = 0
        for param_name, param_def in self._param_defs.items():
            if 'nibble' in param_def:
                # Skip nibble parameters as they're handled separately
                continue
                
            offset = param_def["offset"]
            if 'size' in param_def:
                end = offset + param_def["size"]
            else:
                end = offset + 1  # Default size is 1 byte
                
            max_offset = max(max_offset, end)
            
        buffer = bytearray([0] * max_offset)
        
        for param_name, param_def in self._param_defs.items():
            if 'nibble' in param_def:
                # Skip nibble parameters as they're handled separately
                continue
                
            offset = param_def["offset"]
            value = getattr(self, param_name)
            
            # All modulator parameters are UINT8
            buffer[offset] = value & 0xFF
        
        return bytes(buffer)
    
    def clone(self):
        """Create a deep copy of this parameter object."""
        instance = self.__class__(self._param_defs)
        for param_name in self._param_defs.keys():
            setattr(instance, param_name, getattr(self, param_name))
        return instance
    
    def as_dict(self):
        """Convert parameters to dictionary for serialization."""
        return {param_name: getattr(self, param_name) 
                for param_name in self._param_defs.keys()}
    
    @classmethod
    def from_dict(cls, modulator_type, data):
        """Create parameters from a dictionary."""
        params = cls.from_config(modulator_type)
        
        for param_name in params._param_defs.keys():
            if param_name in data:
                setattr(params, param_name, data[param_name])
            
        return params

class M8Modulator:
    """Unified modulator class for all M8 modulator types."""
    
    # Common parameter offsets for all modulator types
    TYPE_DEST_BYTE_OFFSET = 0  # Combined type and destination
    AMOUNT_OFFSET = 1         # Modulation amount
    
    # Common constants
    EMPTY_DESTINATION = config["constants"]["empty_destination"]
    DEFAULT_AMOUNT = config["constants"]["default_amount"]
    
    def __init__(self, modulator_type=None, **kwargs):
        """Initialize a new modulator with default parameters."""
        # Process modulator_type
        if modulator_type is None:
            # Default to AHD envelope if not specified
            modulator_type = ModulatorType.AHD_ENVELOPE.value
        elif isinstance(modulator_type, int):
            # Convert type ID to string name
            mod_type_enum = ModulatorType.from_id(modulator_type)
            if mod_type_enum:
                modulator_type = mod_type_enum.value
            else:
                raise ValueError(f"Unknown modulator type ID: {modulator_type}")
        elif isinstance(modulator_type, ModulatorType):
            # If it's already an enum, get its value
            modulator_type = modulator_type.value
        
        # Set the modulator type and ID
        self.modulator_type = modulator_type
        self.type = ModulatorType.get_type_id(modulator_type)
        
        # Common modulator parameters
        self.destination = self.EMPTY_DESTINATION
        self.amount = self.DEFAULT_AMOUNT
        
        # Create params object based on modulator type
        self.params = M8ModulatorParams.from_config(modulator_type)
        
        # Apply common parameters from kwargs
        for key, value in kwargs.items():
            if hasattr(self, key) and not key.startswith('_') and key not in ["type", "params"]:
                setattr(self, key, value)
                
        # Apply modulator-specific parameters from kwargs to params object
        for key, value in kwargs.items():
            if hasattr(self.params, key):
                setattr(self.params, key, value)
    
    def read(self, data):
        """Read all modulator parameters from binary data."""
        if len(data) < 2:
            return
            
        # Read the combined type/destination byte
        type_dest = data[self.TYPE_DEST_BYTE_OFFSET]
        self.type, self.destination = split_byte(type_dest)
        
        # Get the modulator type string from the type ID
        if self.type in MODULATOR_TYPES:
            self.modulator_type = MODULATOR_TYPES[self.type]
        else:
            # Default to ahd_envelope for unknown types
            self.modulator_type = "ahd_envelope"
        
        # Read amount
        self.amount = data[self.AMOUNT_OFFSET]
        
        # Create and read the appropriate params object based on modulator type
        self.params = M8ModulatorParams.from_config(self.modulator_type)
        self.params.read(data)
        
        return self
    
    @classmethod
    def read_from_data(cls, data):
        """Create a modulator from binary data."""
        if len(data) < 1:
            return M8Block()
            
        instance = cls()
        instance.read(data)
        return instance
    
    def write(self):
        """Convert the modulator to binary data."""
        # Create a buffer of the correct size
        buffer = bytearray([0] * BLOCK_SIZE)
        
        # Write combined type/destination
        buffer[self.TYPE_DEST_BYTE_OFFSET] = join_nibbles(self.type, self.destination)
        
        # Write amount
        buffer[self.AMOUNT_OFFSET] = self.amount
        
        # Write modulator-specific parameters
        params_data = self.params.write()
        
        # Copy non-amount parameter bytes to the buffer
        # Start at offset 2 for modulator-specific params (after type/dest and amount)
        for i in range(min(len(params_data), BLOCK_SIZE - 2)):
            buffer[i + 2] = params_data[i]
        
        # Return the finalized buffer
        return bytes(buffer)
    
    def is_empty(self):
        """Check if this modulator is empty."""
        return self.destination == self.EMPTY_DESTINATION
    
    def clone(self):
        """Create a deep copy of this modulator."""
        # Create a new instance of this class with the same modulator type
        instance = self.__class__(modulator_type=self.modulator_type)
        
        # Copy common attributes
        instance.type = self.type
        instance.destination = self.destination
        instance.amount = self.amount
        
        # Clone params
        instance.params = self.params.clone() if hasattr(self.params, 'clone') else self.params
                
        return instance
    
    def as_dict(self):
        """Convert modulator to dictionary for serialization."""
        # Start with the type and common parameters
        result = {
            "type": self.type,
            "destination": self.destination,
            "amount": self.amount
        }
        
        # Add modulator-specific parameters
        params_dict = self.params.as_dict()
        for key, value in params_dict.items():
            # Skip destination if already included in common params
            if key != "destination" and key != "amount":
                result[key] = value
            
        return result
    
    @classmethod
    def from_dict(cls, data):
        """Create a modulator from a dictionary."""
        # Get the modulator type
        mod_type = data["type"]
        
        # Create a new modulator with the appropriate type
        if mod_type in MODULATOR_TYPES:
            modulator_type = MODULATOR_TYPES[mod_type]
            modulator = cls(modulator_type=modulator_type)
            
            # Set common parameters
            for key in ["destination", "amount"]:
                if key in data:
                    setattr(modulator, key, data[key])
            
            # Set modulator-specific parameters
            for key, value in data.items():
                if key not in ["type", "destination", "amount"] and hasattr(modulator.params, key):
                    setattr(modulator.params, key, value)
            
            return modulator
        else:
            raise ValueError(f"Unknown modulator type: {mod_type}")

class M8Modulators(list):
    """Collection of M8 modulators."""
    
    def __init__(self, items=None):
        """Initialize a collection with optional modulators."""
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
            
            if len(block_data) < 1:
                instance.append(M8Block())
                continue
                
            first_byte = block_data[0]
            mod_type, dest = split_byte(first_byte)
            
            if mod_type in MODULATOR_TYPES:
                # For valid modulator types, create a modulator and read the data
                modulator = M8Modulator(modulator_type=mod_type)
                modulator.read(block_data)
                instance.append(modulator)
            else:
                # For unknown types, use M8Block
                instance.append(M8Block.read(block_data))
        
        return instance
    
    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        list.__init__(instance)
        
        for mod in self:
            if hasattr(mod, 'clone'):
                instance.append(mod.clone())
            else:
                instance.append(mod)
        
        return instance
    
    def write(self):
        result = bytearray()
        for mod in self:
            mod_data = mod.write() if hasattr(mod, 'write') else bytes([0] * BLOCK_SIZE)
            
            # Ensure each modulator occupies exactly BLOCK_SIZE bytes
            if len(mod_data) < BLOCK_SIZE:
                mod_data = mod_data + bytes([0x0] * (BLOCK_SIZE - len(mod_data)))
            elif len(mod_data) > BLOCK_SIZE:
                mod_data = mod_data[:BLOCK_SIZE]
            
            result.extend(mod_data)
        
        return bytes(result)
    
    def as_list(self):
        """Convert modulators to list for serialization."""
        # Only include non-empty modulators with their indexes
        items = []
        for i, mod in enumerate(self):
            if not (isinstance(mod, M8Block) or mod.is_empty()):
                # Make sure we're calling as_dict if it exists
                if hasattr(mod, 'as_dict') and callable(getattr(mod, 'as_dict')):
                    item_dict = mod.as_dict()
                else:
                    item_dict = {"__class__": "m8.M8Block"}
                
                # Add index field to track position
                item_dict["index"] = i
                items.append(item_dict)
        
        return items
    
    @classmethod
    def from_list(cls, items):
        """Create modulators from a list."""
        instance = cls.__new__(cls)
        list.__init__(instance)
        
        # Initialize with empty blocks
        for _ in range(BLOCK_COUNT):
            instance.append(M8Block())
        
        # Set modulators at their original positions
        if items:
            for mod_data in items:
                # Get index from data
                index = mod_data["index"]
                if 0 <= index < BLOCK_COUNT:
                    # Remove index field before passing to from_dict
                    mod_dict = {k: v for k, v in mod_data.items() if k != "index"}
                    
                    if "type" in mod_dict and mod_dict["type"] in MODULATOR_TYPES:
                        instance[index] = M8Modulator.from_dict(mod_dict)
                    elif "data" in mod_dict:
                        instance[index] = M8Block.from_dict(mod_dict)
        
        return instance

def create_default_modulators():
    """Create a list of default modulators (2 AHD envelopes and 2 LFOs)."""
    result = []
    
    for mod_type in DEFAULT_MODULATOR_CONFIGS:
        if mod_type in MODULATOR_TYPES:
            mod_type_name = MODULATOR_TYPES[mod_type]
            result.append(M8Modulator(modulator_type=mod_type_name))
        else:
            result.append(M8Block())
    return result