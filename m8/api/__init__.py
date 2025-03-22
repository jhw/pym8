import json

# exceptions
    
class M8ValidationError(Exception):
    """Exception for M8 data validation errors when parameters don't meet constraints."""
    pass

# default class

class M8Block:
    """Base class for M8 data blocks providing binary serialization functionality."""
    
    def __init__(self):
        self.data = bytearray()

    @classmethod
    def read(cls, data):
        instance = cls()
        instance.data = data
        return instance

    def is_empty(self):
        return all(b == 0x0 for b in self.data)
    
    def write(self):
        return self.data

    def as_dict(self):
        return {
            "data": list(self.data)
        }
    
    @classmethod
    def from_dict(cls, data):
        instance = cls()
        if "data" in data:
            instance.data = bytearray(data["data"])
        return instance

# dynamic classes

def load_class(class_path):
    """Dynamically load a class by its fully qualified path."""
    module_name, class_name = class_path.rsplit('.', 1)
    module = __import__(module_name, fromlist=[class_name])
    return getattr(module, class_name)

# bit twiddling

def split_byte(byte):
    """Split a byte into upper and lower nibbles (4-bit values)."""
    upper = (byte >> 4) & 0x0F
    lower = byte & 0x0F
    return upper, lower

def join_nibbles(upper, lower):
    """Join two 4-bit nibbles into a single byte."""
    return ((upper & 0x0F) << 4) | (lower & 0x0F)

def get_bits(value, start, length=1):
    """Extract specific bits from a value (0=least significant bit)."""
    mask = (1 << length) - 1
    return (value >> start) & mask

def set_bits(value, bits, start, length=1):
    """Set specific bits in a value (0=least significant bit)."""
    mask = ((1 << length) - 1) << start
    return (value & ~mask) | ((bits & ((1 << length) - 1)) << start)

# string handling

def read_fixed_string(data, offset, length):
    """Read fixed-length string from binary data, handling null bytes and 0xFF padding."""
    str_bytes = data[offset:offset + length]
    
    # Truncate at null byte if present
    null_idx = str_bytes.find(0)
    if null_idx != -1:
        str_bytes = str_bytes[:null_idx]
    
    # Filter out 0xFF bytes (common padding in M8 files)
    str_bytes = bytes([b for b in str_bytes if b != 0xFF])
    
    # Decode and strip
    return str_bytes.decode('utf-8', errors='replace').strip()

def write_fixed_string(string, length):
    """Encode string as fixed-length byte array with null byte padding."""
    encoded = string.encode('utf-8')
    
    # Truncate if too long
    if len(encoded) > length:
        encoded = encoded[:length]
    
    # Pad with null bytes if too short
    if len(encoded) < length:
        encoded = encoded + bytes([0] * (length - len(encoded)))
        
    return encoded

# serialisation

class M8JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that converts small integers (0-255) to hex strings."""
    
    def iterencode(self, obj, _one_shot=False):
        # Pre-process the object to convert all integers to hex strings
        obj = self._process_object(obj)
        return super().iterencode(obj, _one_shot)
    
    def _process_object(self, obj):
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
    """Convert hex strings back to integers in decoded JSON."""
    for key, value in obj.items():
        if isinstance(value, str) and value.startswith("0x"):
            try:
                # Convert hex strings back to integers
                obj[key] = int(value, 16)
            except ValueError:
                pass
    return obj

def json_dumps(obj, indent = 2):
    """Serialize an object to JSON using M8 encoding (integers as hex strings)."""
    return json.dumps(obj,
                      indent = indent,
                      cls = M8JSONEncoder)

def json_loads(json_str):
    """Deserialize a JSON string using M8 decoding (hex strings to integers)."""
    return json.loads(json_str,
                      object_hook = m8_json_decoder)
