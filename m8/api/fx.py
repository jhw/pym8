from m8.api import M8ValidationError
from m8.api.utils.enums import EnumPropertyMixin, serialize_param_enum_value, deserialize_param_enum
from m8.api.utils.context import M8InstrumentContext
from m8.config import load_format_config

# Load configuration
config = load_format_config()["fx"]

# Module-level constants
BLOCK_SIZE = config["block_size"]
BLOCK_COUNT = config["block_count"]

class M8FXTuple(EnumPropertyMixin):
    """Key-value pair for M8 effects with key (effect type) and value (effect parameter)."""
    
    KEY_OFFSET = config["fields"]["key"]["offset"]
    VALUE_OFFSET = config["fields"]["value"]["offset"]
    EMPTY_KEY = config["constants"]["empty_key"]
    DEFAULT_VALUE = config["constants"]["default_value"]
    
    def __init__(self, key=EMPTY_KEY, value=DEFAULT_VALUE, instrument_type=None):
        # Get instrument context if not explicitly provided
        if instrument_type is None:
            context = M8InstrumentContext.get_instance()
            instrument_type_id = context.get_instrument_type_id()
            # Convert ID to string representation for external API
            if instrument_type_id is not None:
                from m8.config import get_instrument_types
                instrument_types = get_instrument_types()
                instrument_type = instrument_types.get(instrument_type_id)
            
        self._instrument_type = instrument_type
        self._data = bytearray([0, 0])  # Initialize with zeros
        
        # Set binary value directly or convert from string enum
        if isinstance(key, str) and key != self.EMPTY_KEY:
            if "enums" in config["fields"]["key"] and instrument_type is not None:
                numeric_key = deserialize_param_enum(
                    config["fields"]["key"]["enums"], 
                    key, 
                    "key", 
                    instrument_type
                )
                self._data[self.KEY_OFFSET] = numeric_key
            else:
                self._data[self.KEY_OFFSET] = int(key)  # Try direct conversion
        else:
            self._data[self.KEY_OFFSET] = key
            
        self._data[self.VALUE_OFFSET] = value
    
    @classmethod
    def read(cls, data, instrument_type=None):
        # Get instrument context if not explicitly provided
        if instrument_type is None:
            context = M8InstrumentContext.get_instance()
            instrument_type_id = context.get_instrument_type_id()
            # Convert ID to string representation for external API
            if instrument_type_id is not None:
                from m8.config import get_instrument_types
                instrument_types = get_instrument_types()
                instrument_type = instrument_types.get(instrument_type_id)
            
        instance = cls.__new__(cls)  # Create instance without calling __init__
        instance._data = bytearray(data[:BLOCK_SIZE])
        instance._instrument_type = instrument_type
        return instance
    
    def write(self):
        return bytes(self._data)
    
    def is_empty(self):
        """Check if this FX tuple is empty.
        
        Uses a lenient approach that only checks if the key equals the M8 empty key value (0xFF),
        rather than validating against instrument-specific FX enums. This approach is preferable because:
        1. It's simpler and more performant
        2. It doesn't require instrument context to be propagated everywhere
        3. It's more resilient to future changes in the M8 firmware
        4. It maintains separation between emptiness checks and validity checks
        """
        return self._data[self.KEY_OFFSET] == self.EMPTY_KEY
    
    @property
    def key(self):
        # Get the underlying byte value
        numeric_value = self._data[self.KEY_OFFSET]
        
        # If empty key, just return it as-is
        if numeric_value == self.EMPTY_KEY:
            return numeric_value
            
        # Get instrument type from instance or context
        instrument_type = self._instrument_type
        if instrument_type is None:
            context = M8InstrumentContext.get_instance()
            instrument_type_id = context.get_instrument_type_id()
            # Convert ID to string representation for external API
            if instrument_type_id is not None:
                from m8.config import get_instrument_types
                instrument_types = get_instrument_types()
                instrument_type = instrument_types.get(instrument_type_id)
            
        # If we have instrument type and there are enum mappings, convert to string
        if instrument_type is not None and "enums" in config["fields"]["key"]:
            string_value = serialize_param_enum_value(
                numeric_value, 
                config["fields"]["key"], 
                instrument_type, 
                "key"
            )
            return string_value
        
        return numeric_value
    
    @key.setter
    def key(self, value):
        # Get instrument type from instance or context
        instrument_type = self._instrument_type
        if instrument_type is None:
            context = M8InstrumentContext.get_instance()
            instrument_type_id = context.get_instrument_type_id()
            # Convert ID to string representation for external API
            if instrument_type_id is not None:
                from m8.config import get_instrument_types
                instrument_types = get_instrument_types()
                instrument_type = instrument_types.get(instrument_type_id)
            
        # Convert string enum to numeric value if needed
        if isinstance(value, str) and value != self.EMPTY_KEY and instrument_type is not None:
            if "enums" in config["fields"]["key"]:
                value = deserialize_param_enum(
                    config["fields"]["key"]["enums"], 
                    value, 
                    "key", 
                    instrument_type
                )
        
        self._data[self.KEY_OFFSET] = value
    
    @property
    def value(self):
        return self._data[self.VALUE_OFFSET]
    
    @value.setter
    def value(self, value):
        self._data[self.VALUE_OFFSET] = value
    
    def clone(self):
        """Create a copy of this FX tuple that preserves instrument_type."""
        return self.__class__(
            key=self.key,
            value=self.value,
            instrument_type=self._instrument_type
        )
    
    def as_dict(self):
        # The .key property getter already uses context if needed
        return {
            "key": self.key,
            "value": self.value
        }
    
    @classmethod
    def from_dict(cls, data, instrument_type=None):
        # The constructor will use context if instrument_type is None
        return cls(
            key=data["key"],
            value=data["value"],
            instrument_type=instrument_type
        )


class M8FXTuples(list):
    """Collection of effect settings that can be applied to phrases, instruments, and chains."""
    
    def __init__(self, instrument_type=None):
        super().__init__()
        
        # Get instrument context if not explicitly provided
        if instrument_type is None:
            context = M8InstrumentContext.get_instance()
            instrument_type_id = context.get_instrument_type_id()
            # Convert ID to string representation for external API
            if instrument_type_id is not None:
                from m8.config import get_instrument_types
                instrument_types = get_instrument_types()
                instrument_type = instrument_types.get(instrument_type_id)
            
        self._instrument_type = instrument_type
        
        # Initialize with empty FX tuples
        for _ in range(BLOCK_COUNT):
            self.append(M8FXTuple(instrument_type=instrument_type))
    
    @classmethod
    def read(cls, data, instrument_type=None):
        # Get instrument context if not explicitly provided
        if instrument_type is None:
            context = M8InstrumentContext.get_instance()
            instrument_type_id = context.get_instrument_type_id()
            # Convert ID to string representation for external API
            if instrument_type_id is not None:
                from m8.config import get_instrument_types
                instrument_types = get_instrument_types()
                instrument_type = instrument_types.get(instrument_type_id)
            
        instance = cls.__new__(cls)  # Create instance without calling __init__
        list.__init__(instance)  # Initialize the list properly
        instance._instrument_type = instrument_type
        
        for i in range(BLOCK_COUNT):
            start = i * BLOCK_SIZE
            tuple_data = data[start:start + BLOCK_SIZE]
            instance.append(M8FXTuple.read(tuple_data, instrument_type=instrument_type))
        
        return instance
    
    def clone(self):
        # Use existing instrument_type or get from context
        instrument_type = self._instrument_type
        if instrument_type is None:
            context = M8InstrumentContext.get_instance()
            instrument_type_id = context.get_instrument_type_id()
            # Convert ID to string representation for external API
            if instrument_type_id is not None:
                from m8.config import get_instrument_types
                instrument_types = get_instrument_types()
                instrument_type = instrument_types.get(instrument_type_id)
        
        instance = self.__class__(instrument_type=instrument_type)
        instance.clear()  # Remove default items
        
        for fx_tuple in self:
            if hasattr(fx_tuple, 'clone'):
                instance.append(fx_tuple.clone())
            else:
                # Pass instrument_type to read method
                cloned_tuple = M8FXTuple.read(fx_tuple.write(), instrument_type=instrument_type)
                instance.append(cloned_tuple)
        
        return instance
    
    def is_empty(self):
        return all(fx_tuple.is_empty() for fx_tuple in self)
    
    def write(self):
        result = bytearray()
        for fx_tuple in self:
            tuple_data = fx_tuple.write()
            result.extend(tuple_data)
        return bytes(result)
    
    def as_list(self):
        # Get instrument type from instance or context
        instrument_type = self._instrument_type
        if instrument_type is None:
            context = M8InstrumentContext.get_instance()
            instrument_type = context.get_instrument_type()
        
        # Only include non-empty tuples with their position index
        tuples = []
        for i, fx_tuple in enumerate(self):
            if not fx_tuple.is_empty():
                # Use the instrument context for serialization
                context = M8InstrumentContext.get_instance()
                # Get type ID
                if isinstance(instrument_type, int):
                    instrument_type_id = instrument_type
                elif hasattr(instrument_type, 'value'):
                    instrument_type_id = instrument_type.value
                else:
                    # For string types, lookup the ID
                    from m8.config import get_instrument_type_id
                    instrument_type_id = get_instrument_type_id(instrument_type)
                    
                with context.with_instrument(instrument_type_id=instrument_type_id):
                    tuple_dict = fx_tuple.as_dict()
                    # Add index to track position
                    tuple_dict["index"] = i
                    tuples.append(tuple_dict)
        
        return tuples
        
    @classmethod
    def from_list(cls, items, instrument_type=None):
        # Get instrument context if not explicitly provided
        if instrument_type is None:
            context = M8InstrumentContext.get_instance()
            instrument_type = context.get_instrument_type()
        
        instance = cls(instrument_type=instrument_type)
        instance.clear()  # Clear default tuples
        
        # Initialize with empty tuples
        for _ in range(BLOCK_COUNT):
            instance.append(M8FXTuple(instrument_type=instrument_type))
        
        # Set tuples at their original positions
        if items:
            # Use the instrument context for deserialization
            context = M8InstrumentContext.get_instance()
            # Get type ID
            if isinstance(instrument_type, int):
                instrument_type_id = instrument_type
            elif hasattr(instrument_type, 'value'):
                instrument_type_id = instrument_type.value
            else:
                # For string types, lookup the ID
                from m8.config import get_instrument_type_id
                instrument_type_id = get_instrument_type_id(instrument_type)
                
            with context.with_instrument(instrument_type_id=instrument_type_id):
                for tuple_data in items:
                    # Get index from data
                    index = tuple_data["index"]
                    if 0 <= index < BLOCK_COUNT:
                        # Remove index field before passing to from_dict
                        tuple_dict = {k: v for k, v in tuple_data.items() if k != "index"}
                        instance[index] = M8FXTuple.from_dict(tuple_dict, instrument_type=instrument_type)
        
        return instance