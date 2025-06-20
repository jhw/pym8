from m8.api import (
    M8Block, load_class, split_byte, join_nibbles, serialize_enum, deserialize_enum, M8UnknownTypeError
)
from m8.enums import M8ModulatorType
from m8.config import (
    load_format_config, get_modulator_types, get_modulator_type_id, 
    get_modulator_data, get_modulator_common_offsets
)
import logging
import importlib

# Load configuration
config = load_format_config()["modulators"]

# Module-level constants
BLOCK_SIZE = config["block_size"]
BLOCK_COUNT = config["count"]

# Type mapping from IDs to names - loaded from config
MODULATOR_TYPES = get_modulator_types()

# Default modulator configurations
DEFAULT_MODULATOR_CONFIGS = config["default_config"]  # 2 AHD envelopes, 2 LFOs

class M8ModulatorParams:
    """Dynamic parameter container for modulator parameters."""
    
    def __init__(self, param_defs, **kwargs):
        """Initialize the parameter group with the given parameter definitions."""
        self._param_defs = param_defs
        
        # Initialize parameters with defaults
        for param_name, param_def in param_defs.items():
            default = param_def["default"]
            setattr(self, param_name, default)
        
        # Validate kwargs before applying them
        valid_params = set(self._param_defs.keys())
        for key in kwargs.keys():
            if key not in valid_params:
                raise ValueError(f"Unknown parameter '{key}' for modulator parameters")
        
        # Apply valid kwargs directly - clients should pass enum.value for enum parameters
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @classmethod
    def from_config(cls, modulator_type, **kwargs):
        """Create parameters from modulator type config."""
        config = load_format_config()
        
        # Use modulator_type as provided without case conversion
        lookup_type = modulator_type
        
        # Load parameter definitions from config
        param_defs = config["modulators"]["types"][lookup_type]["fields"].copy()
        
        return cls(param_defs, **kwargs)
    
    def read(self, data):
        """Read parameters from binary data."""
        # Read values directly from their explicit offsets in the binary data
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
            
            # All modulator parameters are UINT8 - clients pass enum.value directly
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
        result = {}
        
        for param_name, param_def in self._param_defs.items():
            value = getattr(self, param_name)
            result[param_name] = value
            
        return result
    
    @classmethod
    def from_dict(cls, modulator_type, data):
        """Create parameters from a dictionary."""
        params = cls.from_config(modulator_type)
        
        for param_name in params._param_defs.keys():
            if param_name in data:
                value = data[param_name]
                setattr(params, param_name, value)
            
        return params

class M8Modulator:
    """Unified modulator class for all M8 modulator types."""
    
    # Get common parameter offsets from config
    common_offsets = get_modulator_common_offsets()
    
    # Common parameter offsets for all modulator types
    TYPE_DEST_BYTE_OFFSET = common_offsets["type_dest_byte"]  # Combined type and destination
    AMOUNT_OFFSET = common_offsets["amount"]                  # Modulation amount
    
    # Common constants
    EMPTY_DESTINATION = config["constants"]["empty_destination"]
    DEFAULT_AMOUNT = config["constants"]["default_amount"]
    
    def __init__(self, modulator_type=None, **kwargs):
        """Initialize a new modulator with default parameters.
        
        Args:
            modulator_type: The type of modulator to create
            **kwargs: Additional parameters to set on the modulator
        """
        # Process modulator_type
        if modulator_type is None:
            # Default to AHD envelope if not specified
            self.type = M8ModulatorType.AHD_ENVELOPE
            modulator_type = "AHD_ENVELOPE"
        elif isinstance(modulator_type, int):
            # Convert type ID to enum
            try:
                self.type = M8ModulatorType(modulator_type)
                modulator_type = MODULATOR_TYPES[modulator_type]
            except (ValueError, KeyError):
                raise ValueError(f"Unknown modulator type ID: {modulator_type}")
        elif isinstance(modulator_type, M8ModulatorType):
            # If it's already an enum, use it directly
            self.type = modulator_type
            modulator_type = MODULATOR_TYPES[modulator_type.value]
        else:
            # Assume it's a string type name
            self.type = M8ModulatorType(get_modulator_type_id(modulator_type))
        
        # Set the modulator type name as provided
        self.modulator_type = modulator_type
        
        # Common modulator parameters - clients pass enum.value directly
        self.destination = self.EMPTY_DESTINATION
        self.amount = self.DEFAULT_AMOUNT
        
        # Create params object based on modulator type
        self.params = M8ModulatorParams.from_config(modulator_type)
        
        # Validate kwargs first
        valid_keys = set()
        # Add common modulator properties
        for key in dir(self):
            if not key.startswith('_') and key not in ["type", "params"]:
                valid_keys.add(key)
        
        # Add all parameter keys
        for key in dir(self.params):
            if not key.startswith('_') and not callable(getattr(self.params, key)):
                valid_keys.add(key)
        
        # Check for invalid keys
        for key in kwargs.keys():
            if key not in valid_keys:
                raise ValueError(f"Unknown parameter '{key}' for modulator type '{modulator_type}'")
        
        # Apply common parameters from kwargs - clients pass enum.value directly
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
        type_id, self.destination = split_byte(type_dest)
        
        # Get the modulator type string from the type ID
        if type_id in MODULATOR_TYPES:
            # Convert to enum for consistency
            self.type = M8ModulatorType(type_id)
            self.modulator_type = MODULATOR_TYPES[type_id]
        else:
            # Raise exception for unknown modulator types
            raise M8UnknownTypeError(f"Unknown modulator type ID: {type_id}")
        
        # Read amount
        self.amount = data[self.AMOUNT_OFFSET]
        
        # Create the parameters object based on modulator type
        self.params = M8ModulatorParams.from_config(self.modulator_type)
        
        # Read parameters directly from their positions in the binary data
        for param_name in dir(self.params):
            # Skip private attributes and methods
            if param_name.startswith('_') or callable(getattr(self.params, param_name)):
                continue
                
            # Get parameter definition to find its offset
            param_def = self.params._param_defs.get(param_name)
            if not param_def or 'nibble' in param_def:
                continue  # Skip parameters without definitions or nibble params
                
            # Get parameter offset
            offset = param_def.get("offset")
            
            # Read value directly from its position in the data
            if offset is not None and offset < len(data):
                setattr(self.params, param_name, data[offset])
        
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
        buffer = bytearray([0] * BLOCK_SIZE)
        
        # Get destination value - clients should pass enum.value directly
        dest_value = self.destination
        
        # Write common fields
        buffer[self.TYPE_DEST_BYTE_OFFSET] = join_nibbles(self.type, dest_value)
        buffer[self.AMOUNT_OFFSET] = self.amount
        
        # Write each parameter directly to its position in the buffer based on its offset
        # This ensures params are written to their correct positions directly
        for param_name in dir(self.params):
            # Skip private attributes and methods
            if param_name.startswith('_') or callable(getattr(self.params, param_name)):
                continue
                
            # Get parameter definition to find its offset
            param_def = self.params._param_defs.get(param_name)
            if not param_def or 'nibble' in param_def:
                continue  # Skip parameters without definitions or nibble params
                
            # Get parameter offset and value
            offset = param_def.get("offset")
            value = getattr(self.params, param_name)
            
            # Ensure the offset is within the buffer bounds
            if offset is not None and offset < BLOCK_SIZE:
                buffer[offset] = value & 0xFF
        
        return bytes(buffer)
    
    def is_empty(self):
        """Check if this modulator is empty."""
        # Check if type is valid
        type_value = getattr(self.type, 'value', self.type) if hasattr(self.type, 'value') else self.type
        if not isinstance(type_value, int) or type_value not in MODULATOR_TYPES:
            return True
            
        # Check if destination is OFF/0
        dest_value = self.destination
        if isinstance(dest_value, int) and dest_value == 0:
            return True
            
        return False
    
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
        type_value = serialize_enum(self.type, 'modulator')
        
        result = {
            "type": type_value,
            "destination": self.destination,
            "amount": self.amount
        }
        
        params_dict = self.params.as_dict()
        for key, value in params_dict.items():
            if key != "destination" and key != "amount":
                result[key] = value
            
        return result
    
    @classmethod
    def from_dict(cls, data):
        """Create a modulator from a dictionary."""
        mod_type = data["type"]
        
        try:
            modulator_type = deserialize_enum(M8ModulatorType, mod_type, 'modulator')
            modulator = cls(modulator_type=modulator_type)
            
            # Process destination value - clients should pass enum.value directly
            if "destination" in data:
                dest_value = data["destination"]
                modulator.destination = dest_value
            
            if "amount" in data:
                modulator.amount = data["amount"]
            
            # Set modulator-specific parameters
            for key, value in data.items():
                if key not in ["type", "destination", "amount"] and hasattr(modulator.params, key):
                    setattr(modulator.params, key, value)
            
            return modulator
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid modulator type: {mod_type}. Error: {str(e)}")

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
            
            try:
                if mod_type in MODULATOR_TYPES:
                    # For valid modulator types, create a modulator and read the data
                    modulator = M8Modulator(modulator_type=mod_type)
                    modulator.read(block_data)
                    instance.append(modulator)
                else:
                    # Default to M8Block for empty slots (all zeros)
                    if all(b == 0 for b in block_data[:3]):  # Check first few bytes
                        instance.append(M8Block.read(block_data))
                    else:
                        # Raise exception for unknown modulator types with data
                        raise M8UnknownTypeError(f"Unknown modulator type ID: {mod_type}")
            except M8UnknownTypeError as e:
                # Log error but treat as M8Block to be resilient in collection reading
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