import json
import logging

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

# enum helpers

def serialize_enum(enum_value, log_prefix=None):
    if hasattr(enum_value, 'name'):
        return enum_value.name
    
    logger = logging.getLogger(__name__)
    prefix = f"{log_prefix} " if log_prefix else ""
    logger.warning(f"Serializing non-enum {prefix}type: {enum_value}")
    return enum_value

def deserialize_enum(enum_class, value, log_prefix=None):
    from m8.enums import M8EnumError
    
    if isinstance(value, str):
        try:
            return enum_class[value].value
        except KeyError:
            error_msg = f"Invalid enum string value: '{value}' not found in {enum_class.__name__}"
            if log_prefix:
                error_msg = f"{log_prefix}: {error_msg}"
            raise M8EnumError(error_msg)
    else:
        try:
            enum_class(value)
        except ValueError:
            logger = logging.getLogger(__name__)
            prefix = f"{log_prefix} " if log_prefix else ""
            logger.warning(f"Deserializing unknown {prefix}type ID: {value}")
        
        return value

def get_enum_paths_for_instrument(enum_paths, instrument_type):
    if not isinstance(enum_paths, dict) or instrument_type is None:
        return enum_paths
        
    instrument_type_key = str(instrument_type)
    
    if instrument_type_key.isdigit():
        hex_key = f"0x{int(instrument_type_key):02x}"
        if hex_key in enum_paths:
            instrument_type_key = hex_key
    
    return enum_paths.get(instrument_type_key)

def load_enum_classes(enum_paths, log_context=None):
    import importlib
    logger = logging.getLogger(__name__)
    enum_classes = []
    
    if not enum_paths:
        return enum_classes
        
    # Make sure enum_paths is iterable
    if isinstance(enum_paths, str):
        enum_paths = [enum_paths]
        
    for enum_path in enum_paths:
        # Skip empty or invalid paths
        if not enum_path or not isinstance(enum_path, str):
            continue
            
        try:
            module_name, class_name = enum_path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            enum_class = getattr(module, class_name)
            enum_classes.append(enum_class)
        except (ImportError, AttributeError, ValueError) as e:
            context = f" for {log_context}" if log_context else ""
            logger.warning(f"Error importing enum {enum_path}{context}: {e}")
            
    return enum_classes

def serialize_param_enum_value(value, param_def, instrument_type=None, param_name=None):
    if "enums" not in param_def:
        return value
        
    enum_paths = get_enum_paths_for_instrument(param_def["enums"], instrument_type)
    if not enum_paths:
        return value
        
    enum_classes = load_enum_classes(enum_paths, param_name)
    if not enum_classes:
        return value
        
    if hasattr(value, 'name'):
        return value.name
        
    if isinstance(value, int):
        for enum_class in enum_classes:
            try:
                enum_value = enum_class(value)
                return enum_value.name
            except ValueError:
                continue
                
    return value

def deserialize_param_enum(enum_paths, value, param_name=None, instrument_type=None):
    from m8.enums import M8EnumError
    
    if not isinstance(value, str):
        return value
    
    enum_paths = get_enum_paths_for_instrument(enum_paths, instrument_type)
    if not enum_paths:
        logger = logging.getLogger(__name__)
        logger.warning(f"No enum defined for instrument type {instrument_type} parameter {param_name}")
        return value
    
    enum_classes = load_enum_classes(enum_paths, param_name)
    
    if enum_classes:
        for enum_class in enum_classes:
            try:
                return enum_class[value].value
            except KeyError:
                continue
    
    param_details = f" for parameter '{param_name}'" if param_name else ""
    error_msg = f"Invalid enum string value: '{value}' not found in any of the provided enum classes{param_details}"
    raise M8EnumError(error_msg)
    
def ensure_enum_int_value(value, enum_paths, instrument_type=None):
    if not isinstance(value, str):
        return value
    
    from m8.enums import M8EnumError
    
    enum_paths = get_enum_paths_for_instrument(enum_paths, instrument_type)
    if not enum_paths:
        logger = logging.getLogger(__name__)
        logger.warning(f"No enum defined for instrument type {instrument_type}")
        return value
    
    enum_classes = load_enum_classes(enum_paths)
    
    for enum_class in enum_classes:
        try:
            return enum_class[value].value
        except KeyError:
            continue
    
    error_msg = f"Invalid enum string value: '{value}' not found in any of the provided enum classes"
    raise M8EnumError(error_msg)
