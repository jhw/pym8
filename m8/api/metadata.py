import struct
from m8.api import _read_fixed_string, _write_fixed_string

# Metadata offsets and sizes
METADATA_OFFSET = 14
METADATA_BLOCK_SIZE = 147

# Field offsets within metadata block
DIRECTORY_OFFSET = 0
DIRECTORY_LENGTH = 128
TRANSPOSE_OFFSET = 128
TEMPO_OFFSET = 129
TEMPO_SIZE = 4
QUANTIZE_OFFSET = 133
NAME_OFFSET = 134
NAME_LENGTH = 12
KEY_OFFSET = 146

# Default values
DEFAULT_DIRECTORY = '/Songs/'
DEFAULT_TRANSPOSE = 0
DEFAULT_TEMPO = 120.0
DEFAULT_QUANTIZE = 0
DEFAULT_NAME = 'HELLO'
DEFAULT_KEY = 0

class M8Metadata:
    """Stores M8 tracker metadata including song name, directory, tempo, key, transpose and quantize."""

    DIRECTORY_OFFSET = DIRECTORY_OFFSET
    DIRECTORY_LENGTH = DIRECTORY_LENGTH
    TRANSPOSE_OFFSET = TRANSPOSE_OFFSET
    TEMPO_OFFSET = TEMPO_OFFSET
    TEMPO_SIZE = TEMPO_SIZE
    QUANTIZE_OFFSET = QUANTIZE_OFFSET
    NAME_OFFSET = NAME_OFFSET
    NAME_LENGTH = NAME_LENGTH
    KEY_OFFSET = KEY_OFFSET
    BLOCK_SIZE = METADATA_BLOCK_SIZE

    def __init__(self, directory=DEFAULT_DIRECTORY,
                 transpose=DEFAULT_TRANSPOSE,
                 tempo=DEFAULT_TEMPO,
                 quantize=DEFAULT_QUANTIZE,
                 name=DEFAULT_NAME,
                 key=DEFAULT_KEY):
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
    
    def clone(self):
        return M8Metadata(
            directory=self.directory,
            transpose=self.transpose,
            tempo=self.tempo,
            quantize=self.quantize,
            name=self.name,
            key=self.key
        )
