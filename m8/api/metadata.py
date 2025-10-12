import struct
from m8.core.format import load_format_config

# Load configuration
config = load_format_config()["metadata"]

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

class M8Metadata:
    """Stores M8 tracker metadata including song name, directory, tempo, key, transpose and quantize."""
    
    DIRECTORY_OFFSET = config["fields"]["directory"]["offset"]
    DIRECTORY_LENGTH = config["fields"]["directory"]["size"]
    TRANSPOSE_OFFSET = config["fields"]["transpose"]["offset"]
    TEMPO_OFFSET = config["fields"]["tempo"]["offset"]
    TEMPO_SIZE = config["fields"]["tempo"]["size"]
    QUANTIZE_OFFSET = config["fields"]["quantize"]["offset"]
    NAME_OFFSET = config["fields"]["name"]["offset"]
    NAME_LENGTH = config["fields"]["name"]["size"]
    KEY_OFFSET = config["fields"]["key"]["offset"]
    BLOCK_SIZE = config["block_size"]

    def __init__(self, directory=config["fields"]["directory"]["default"], 
                 transpose=config["fields"]["transpose"]["default"], 
                 tempo=config["fields"]["tempo"]["default"], 
                 quantize=config["fields"]["quantize"]["default"], 
                 name=config["fields"]["name"]["default"], 
                 key=config["fields"]["key"]["default"]):
        self.directory = directory
        self.transpose = transpose
        self.tempo = tempo
        self.quantize = quantize
        self.name = name
        self.key = key
    
    @classmethod
    def read(cls, data):
        instance = cls()
        
        # Directory (null-terminated string)
        instance.directory = _read_fixed_string(data, cls.DIRECTORY_OFFSET, cls.DIRECTORY_LENGTH)
        
        # Transpose (1 byte)
        instance.transpose = data[cls.TRANSPOSE_OFFSET]
        
        # Tempo (4 bytes, float32)
        instance.tempo = struct.unpack('<f', data[cls.TEMPO_OFFSET:cls.TEMPO_OFFSET + cls.TEMPO_SIZE])[0]
        
        # Quantize (1 byte)
        instance.quantize = data[cls.QUANTIZE_OFFSET]
        
        # Name (null-terminated string)
        instance.name = _read_fixed_string(data, cls.NAME_OFFSET, cls.NAME_LENGTH)
        
        # Key (1 byte)
        instance.key = data[cls.KEY_OFFSET]
        
        return instance
    
    def write(self):
        buffer = bytearray()
        
        # Directory (null-terminated) using utility function
        buffer.extend(_write_fixed_string(self.directory, self.DIRECTORY_LENGTH))
        
        # Transpose (1 byte)
        buffer.append(self.transpose)
        
        # Tempo (4 bytes, float32)
        buffer.extend(struct.pack('<f', self.tempo))
        
        # Quantize (1 byte)
        buffer.append(self.quantize)
        
        # Name (null-terminated) using utility function
        buffer.extend(_write_fixed_string(self.name, self.NAME_LENGTH))
        
        # Key (1 byte)
        buffer.append(self.key)
        
        # The total size should be BLOCK_SIZE bytes
        assert len(buffer) == self.BLOCK_SIZE, f"Buffer size mismatch: {len(buffer)} != {self.BLOCK_SIZE}"
        return bytes(buffer)
    
    def is_empty(self):
        return (self.directory.strip('/') == "" and 
                self.name.strip() == "")
    
    def clone(self):
        return M8Metadata(
            directory=self.directory,
            transpose=self.transpose,
            tempo=self.tempo,
            quantize=self.quantize,
            name=self.name,
            key=self.key
        )
