# Bit manipulation utilities

def split_byte(byte_value):
    """Split a byte into two nibbles (high 4 bits, low 4 bits)."""
    high_nibble = (byte_value >> 4) & 0x0F
    low_nibble = byte_value & 0x0F
    return high_nibble, low_nibble

def join_nibbles(high_nibble, low_nibble):
    """Join two nibbles into a single byte."""
    return ((high_nibble & 0x0F) << 4) | (low_nibble & 0x0F)

# String utilities for binary serialization

def _read_fixed_string(data, offset, length):
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

def _write_fixed_string(string, length):
    """Encode string as fixed-length byte array with null byte padding."""
    encoded = string.encode('utf-8')

    # Truncate if too long
    if len(encoded) > length:
        encoded = encoded[:length]

    # Pad with null bytes if too short
    if len(encoded) < length:
        encoded = encoded + bytes([0] * (length - len(encoded)))

    return encoded

# Default class

class M8Block:
    """Base class for M8 data blocks providing binary serialization functionality."""
    
    def __init__(self):
        self.data = bytearray()

    @classmethod
    def read(cls, data):
        instance = cls()
        instance.data = data
        return instance

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
