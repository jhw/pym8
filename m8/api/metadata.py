import struct

class M8Metadata:
    # Define offsets and lengths as class variables
    DIRECTORY_OFFSET = 0
    DIRECTORY_LENGTH = 128
    TRANSPOSE_OFFSET = 128
    TEMPO_OFFSET = 129
    TEMPO_SIZE = 4
    QUANTIZE_OFFSET = 133
    NAME_OFFSET = 134
    NAME_LENGTH = 12
    KEY_OFFSET = 146
    
    # Total size of metadata block
    BLOCK_SIZE = 147

    def __init__(self, directory="/Songs/", transpose=0, tempo=120.0, 
                 quantize=0, name="HELLO", key=0):
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
        dir_bytes = data[cls.DIRECTORY_OFFSET:cls.DIRECTORY_OFFSET + cls.DIRECTORY_LENGTH]
        null_term_idx = dir_bytes.find(0)
        if null_term_idx != -1:
            dir_bytes = dir_bytes[:null_term_idx]
        instance.directory = dir_bytes.decode('utf-8', errors='replace')
        
        # Transpose (1 byte)
        instance.transpose = data[cls.TRANSPOSE_OFFSET]
        
        # Tempo (4 bytes, float32)
        instance.tempo = struct.unpack('<f', data[cls.TEMPO_OFFSET:cls.TEMPO_OFFSET + cls.TEMPO_SIZE])[0]
        
        # Quantize (1 byte)
        instance.quantize = data[cls.QUANTIZE_OFFSET]
        
        # Name (null-terminated string)
        name_bytes = data[cls.NAME_OFFSET:cls.NAME_OFFSET + cls.NAME_LENGTH]
        null_term_idx = name_bytes.find(0)
        if null_term_idx != -1:
            name_bytes = name_bytes[:null_term_idx]
        instance.name = name_bytes.decode('utf-8', errors='replace')
        
        # Key (1 byte)
        instance.key = data[cls.KEY_OFFSET]
        
        return instance
    
    def write(self):
        buffer = bytearray()
        
        # Directory (null-terminated)
        dir_bytes = self.directory.encode('utf-8')
        dir_bytes = dir_bytes[:self.DIRECTORY_LENGTH - 1]  # Ensure it fits with null terminator
        buffer.extend(dir_bytes)
        buffer.extend(bytes([0] * (self.DIRECTORY_LENGTH - len(dir_bytes))))  # Pad with nulls
        
        # Transpose (1 byte)
        buffer.append(self.transpose)
        
        # Tempo (4 bytes, float32)
        buffer.extend(struct.pack('<f', self.tempo))
        
        # Quantize (1 byte)
        buffer.append(self.quantize)
        
        # Name (null-terminated)
        name_bytes = self.name.encode('utf-8')
        name_bytes = name_bytes[:self.NAME_LENGTH - 1]  # Ensure it fits with null terminator
        buffer.extend(name_bytes)
        buffer.extend(bytes([0] * (self.NAME_LENGTH - len(name_bytes))))  # Pad with nulls
        
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
    
    def as_dict(self):
        """Convert metadata to dictionary for serialization"""
        return {
            "directory": self.directory,
            "transpose": self.transpose,
            "tempo": self.tempo,
            "quantize": self.quantize,
            "name": self.name,
            "key": self.key
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create metadata from a dictionary"""
        return cls(
            directory=data.get("directory", "/Songs/"),
            transpose=data.get("transpose", 0),
            tempo=data.get("tempo", 120.0),
            quantize=data.get("quantize", 0),
            name=data.get("name", "HELLO"),
            key=data.get("key", 0)
        )
