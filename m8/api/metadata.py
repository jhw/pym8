import struct
from m8.config import load_format_config
from m8.api import read_fixed_string, write_fixed_string

# Load configuration
config = load_format_config()["metadata"]

class M8Metadata:
    """Stores M8 tracker metadata including song name, directory, tempo, key, transpose and quantize."""
    
    DIRECTORY_OFFSET = config["strings"]["directory"]["offset"]
    DIRECTORY_LENGTH = config["strings"]["directory"]["length"]
    TRANSPOSE_OFFSET = config["offsets"]["transpose"]
    TEMPO_OFFSET = config["offsets"]["tempo"]
    TEMPO_SIZE = config["offsets"]["tempo_size"]
    QUANTIZE_OFFSET = config["offsets"]["quantize"]
    NAME_OFFSET = config["strings"]["name"]["offset"]
    NAME_LENGTH = config["strings"]["name"]["length"]
    KEY_OFFSET = config["offsets"]["key"]
    BLOCK_SIZE = config["block_size"]

    def __init__(self, directory=config["default_values"]["directory"], 
                 transpose=config["default_values"]["transpose"], 
                 tempo=config["default_values"]["tempo"], 
                 quantize=config["default_values"]["quantize"], 
                 name=config["default_values"]["name"], 
                 key=config["default_values"]["key"]):
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
        instance.directory = read_fixed_string(data, cls.DIRECTORY_OFFSET, cls.DIRECTORY_LENGTH)
        
        # Transpose (1 byte)
        instance.transpose = data[cls.TRANSPOSE_OFFSET]
        
        # Tempo (4 bytes, float32)
        instance.tempo = struct.unpack('<f', data[cls.TEMPO_OFFSET:cls.TEMPO_OFFSET + cls.TEMPO_SIZE])[0]
        
        # Quantize (1 byte)
        instance.quantize = data[cls.QUANTIZE_OFFSET]
        
        # Name (null-terminated string)
        instance.name = read_fixed_string(data, cls.NAME_OFFSET, cls.NAME_LENGTH)
        
        # Key (1 byte)
        instance.key = data[cls.KEY_OFFSET]
        
        return instance
    
    def write(self):
        buffer = bytearray()
        
        # Directory (null-terminated) using utility function
        buffer.extend(write_fixed_string(self.directory, self.DIRECTORY_LENGTH))
        
        # Transpose (1 byte)
        buffer.append(self.transpose)
        
        # Tempo (4 bytes, float32)
        buffer.extend(struct.pack('<f', self.tempo))
        
        # Quantize (1 byte)
        buffer.append(self.quantize)
        
        # Name (null-terminated) using utility function
        buffer.extend(write_fixed_string(self.name, self.NAME_LENGTH))
        
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
        return cls(
            directory=data["directory"],
            transpose=data["transpose"],
            tempo=data["tempo"],
            quantize=data["quantize"],
            name=data["name"],
            key=data["key"]
        )
