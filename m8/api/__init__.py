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
    """Read fixed-length string from binary data.

    Matches m8-file-parser's Reader::read_string (reader.rs): truncate at
    the first 0x00 or 0xFF byte (whichever comes first), then back off
    byte-by-byte to the longest valid UTF-8 prefix. No whitespace stripping
    and no filtering of 0xFF bytes elsewhere in the field — either of those
    would silently change bytes that should round-trip untouched (e.g. a
    name with trailing spaces, or a sample path containing 0xFF past its
    terminator).
    """
    str_bytes = data[offset:offset + length]

    end = length
    for i, b in enumerate(str_bytes):
        if b == 0 or b == 0xFF:
            end = i
            break

    while end > 0:
        try:
            return bytes(str_bytes[:end]).decode('utf-8')
        except UnicodeDecodeError:
            end -= 1

    return ""

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
