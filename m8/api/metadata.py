import struct

class M8Metadata:
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
        
        # Directory (128 bytes, null-terminated string)
        dir_bytes = data[:128]
        null_term_idx = dir_bytes.find(0)
        if null_term_idx != -1:
            dir_bytes = dir_bytes[:null_term_idx]
        instance.directory = dir_bytes.decode('utf-8', errors='replace')
        
        # Transpose (1 byte)
        instance.transpose = data[128]
        
        # Tempo (4 bytes, float32)
        instance.tempo = struct.unpack('<f', data[129:133])[0]
        
        # Quantize (1 byte)
        instance.quantize = data[133]
        
        # Name (12 bytes, null-terminated string)
        name_bytes = data[134:146]
        null_term_idx = name_bytes.find(0)
        if null_term_idx != -1:
            name_bytes = name_bytes[:null_term_idx]
        instance.name = name_bytes.decode('utf-8', errors='replace')
        
        # Key (1 byte)
        instance.key = data[146]
        
        return instance
    
    def write(self):
        buffer = bytearray()
        
        # Directory (128 bytes, null-terminated)
        dir_bytes = self.directory.encode('utf-8')
        dir_bytes = dir_bytes[:127]  # Ensure it fits
        buffer.extend(dir_bytes)
        buffer.extend(bytes([0] * (128 - len(dir_bytes))))  # Pad with nulls
        
        # Transpose (1 byte)
        buffer.append(self.transpose)
        
        # Tempo (4 bytes, float32)
        buffer.extend(struct.pack('<f', self.tempo))
        
        # Quantize (1 byte)
        buffer.append(self.quantize)
        
        # Name (12 bytes, null-terminated)
        name_bytes = self.name.encode('utf-8')
        name_bytes = name_bytes[:11]  # Ensure it fits
        buffer.extend(name_bytes)
        buffer.extend(bytes([0] * (12 - len(name_bytes))))  # Pad with nulls
        
        # Key (1 byte)
        buffer.append(self.key)
        
        # The total size should be 147 bytes
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
    
