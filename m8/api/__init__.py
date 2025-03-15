import json

# exceptions
    
class M8ValidationError(Exception):
    """Exception raised for M8 data validation errors.
    
    Used when validating M8 parameters, settings, or values that don't meet
    expected constraints.
    """
    pass

class IndexError(IndexError):
    """Exception raised for M8-specific index errors.
    
    Used when accessing elements with out-of-range indices in M8 data structures.
    """
    pass

# default class

class M8Block:
    """Base class for M8 data blocks.
    
    Provides fundamental functionality for reading, writing, and serializing
    binary data blocks used in M8 file formats.
    """
    
    def __init__(self):
        """Initialize an empty M8Block instance."""
        self.data = bytearray()

    @classmethod
    def read(cls, data):
        """Create a new instance from binary data.
        
        Args:
            data: Binary data to initialize the block with
            
        Returns:
            A new instance of the class
        """
        instance = cls()
        instance.data = data
        return instance

    def is_empty(self):
        """Check if the data block is empty (contains only zeros).
        
        Returns:
            bool: True if all bytes are zero, False otherwise
        """
        return all(b == 0x0 for b in self.data)
    
    def write(self):
        """Get the binary representation of this block.
        
        Returns:
            bytearray: The binary data
        """
        return self.data

    def as_dict(self):
        """Convert block to dictionary for serialization.
        
        Returns:
            dict: Dictionary representation with the binary data as a list
        """
        return {
            "data": list(self.data)
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create an instance from a dictionary.
        
        Args:
            data: Dictionary containing serialized data
            
        Returns:
            A new instance of the class initialized with the dictionary data
        """
        instance = cls()
        if "data" in data:
            instance.data = bytearray(data["data"])
        return instance

# dynamic classes

def load_class(class_path):
    """Dynamically load a class by its fully qualified path.
    
    Args:
        class_path: String with module path and class name (e.g. 'module.submodule.ClassName')
        
    Returns:
        The class object
        
    Raises:
        AttributeError: If the class doesn't exist in the specified module
        ImportError: If the module cannot be imported
    """
    module_name, class_name = class_path.rsplit('.', 1)
    module = __import__(module_name, fromlist=[class_name])
    return getattr(module, class_name)

# bit twiddling

def split_byte(byte):
    """Split a byte into upper and lower nibbles (4-bit values).
    
    Args:
        byte: The byte value to split (0-255)
        
    Returns:
        tuple: (upper_nibble, lower_nibble) - Two 4-bit values
    """
    upper = (byte >> 4) & 0x0F
    lower = byte & 0x0F
    return upper, lower

def join_nibbles(upper, lower):
    """Join two 4-bit nibbles into a single byte.
    
    Args:
        upper: The upper nibble (0-15)
        lower: The lower nibble (0-15)
        
    Returns:
        int: A byte value (0-255)
    """
    return ((upper & 0x0F) << 4) | (lower & 0x0F)

def get_bits(value, start, length=1):
    """Extract specific bits from a value.
    
    Args:
        value: The integer value to extract bits from
        start: Starting bit position (0 = least significant bit)
        length: Number of bits to extract
        
    Returns:
        int: The extracted bits as an integer value
    """
    mask = (1 << length) - 1
    return (value >> start) & mask

def set_bits(value, bits, start, length=1):
    """Set specific bits in a value.
    
    Args:
        value: The original integer value
        bits: The bits to set
        start: Starting bit position (0 = least significant bit)
        length: Number of bits to set
        
    Returns:
        int: The value with specified bits set
    """
    mask = ((1 << length) - 1) << start
    return (value & ~mask) | ((bits & ((1 << length) - 1)) << start)

# serialisation

class M8JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for M8 data.
    
    Converts small integers (0-255) to hex strings for more readable JSON output
    and easier debugging of binary data.
    """
    
    def iterencode(self, obj, _one_shot=False):
        """Override iterencode to process all integer values.
        
        Args:
            obj: The object to encode
            _one_shot: Internal parameter used by JSONEncoder
            
        Returns:
            Generator yielding strings of JSON data
        """
        # Pre-process the object to convert all integers to hex strings
        obj = self._process_object(obj)
        return super().iterencode(obj, _one_shot)
    
    def _process_object(self, obj):
        """Recursively process objects to convert integers to hex strings.
        
        Args:
            obj: The object to process
            
        Returns:
            The processed object with integers converted to hex strings
        """
        if isinstance(obj, int) and obj < 256:
            # Convert integers to hex strings with '0x' prefix
            return f"0x{obj:02x}"
        elif isinstance(obj, dict):
            # Process dictionaries recursively
            return {k: self._process_object(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            # Process lists recursively
            return [self._process_object(item) for item in obj]
        else:
            # Return other types unchanged
            return obj

def m8_json_decoder(obj):
    """Custom object hook function for decoding hex strings back to integers.
    
    Args:
        obj: Dictionary object from JSON parsing
        
    Returns:
        Dictionary with hex strings converted to integers
    """
    for key, value in obj.items():
        if isinstance(value, str) and value.startswith("0x"):
            try:
                # Convert hex strings back to integers
                obj[key] = int(value, 16)
            except ValueError:
                pass
    return obj

def json_dumps(obj, indent = 2):
    """Serialize an object to JSON string using M8 encoding conventions.
    
    Args:
        obj: The object to serialize
        indent: Number of spaces for indentation
        
    Returns:
        str: JSON string representation
    """
    return json.dumps(obj,
                      indent = indent,
                      cls = M8JSONEncoder)

def json_loads(json_str):
    """Deserialize a JSON string using M8 decoding conventions.
    
    Args:
        json_str: JSON string to parse
        
    Returns:
        Parsed object with hex strings converted to integers
    """
    return json.loads(json_str,
                      object_hook = m8_json_decoder)
