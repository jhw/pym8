from m8 import M8Block, NULL
from m8.api import M8IndexError
from m8.core.serialization import from_json, to_json
from m8.api.chains import M8Chains
from m8.api.instruments import M8Instruments
from m8.api.phrases import M8Phrases
from m8.api.song import M8SongMatrix
from m8.utils.bits import split_byte, join_nibbles

import json
import struct

# https://github.com/AlexCharlton/m8-files/blob/2e79f2592e3950c20081f93aaad135fb9f867f9f/src/songs.rs

OFFSETS = {
    "version": 0x0A,
    "metadata": 0x0E,
    "groove": 0xEE,
    "song": 0x2EE,
    "phrases": 0xAEE,
    "chains": 0x9A5E,
    "table": 0xBA3E,
    "instruments": 0x13A3E,
    "effect_settings": 0x1A5C1,
    "midi_mapping": 0x1A5FE,
    "scale": 0x1AA7E,
    "eq": 0x1AD5A + 4
}

class M8Version:
    def __init__(self, major=0, minor=0, patch=0):
        self.major = major
        self.minor = minor
        self.patch = patch
    
    @classmethod
    def read(cls, data):
        instance = cls()
        if len(data) >= 2:
            # First byte contains minor and patch
            minor_patch = data[0]
            instance.minor, instance.patch = split_byte(minor_patch)
            
            # Second byte contains major (in lower nibble)
            major_byte = data[1]
            _, instance.major = split_byte(major_byte)
        
        return instance
    
    def write(self):
        # Combine minor and patch into one byte
        minor_patch = join_nibbles(self.minor, self.patch)
        
        # Major goes in the lower nibble of the second byte
        major_byte = join_nibbles(0, self.major)  # Upper nibble is not used
        
        return bytes([minor_patch, major_byte])
    
    def is_empty(self):
        return self.major == 0 and self.minor == 0 and self.patch == 0
    
    def clone(self):
        return M8Version(self.major, self.minor, self.patch)
    
    def as_dict(self):
        """Convert version to dictionary for serialization"""
        return {
            "__class__": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create version from a dictionary"""
        return cls(
            major=data.get("major", 0),
            minor=data.get("minor", 0),
            patch=data.get("patch", 0)
        )
    
    def to_json(self, indent=None):
        """Convert version to JSON string"""
        return to_json(self, indent=indent)

    @classmethod
    def from_json(cls, json_str):
        """Create an instance from a JSON string"""
        return from_json(json_str, cls)


class M8Metadata:
    def __init__(self, directory="/Songs/woldo/", transpose=0, tempo=120.0, 
                 quantize=0, name="HELLO_MACRO", key=0):
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
            "__class__": f"{self.__class__.__module__}.{self.__class__.__name__}",
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
            directory=data.get("directory", "/Songs/woldo/"),
            transpose=data.get("transpose", 0),
            tempo=data.get("tempo", 120.0),
            quantize=data.get("quantize", 0),
            name=data.get("name", "HELLO_MACRO"),
            key=data.get("key", 0)
        )
    
    def to_json(self, indent=None):
        """Convert metadata to JSON string"""
        return to_json(self, indent=indent)

    @classmethod
    def from_json(cls, json_str):
        """Create an instance from a JSON string"""
        return from_json(json_str, cls)


class M8Project:
    def __init__(self):
        self.version = M8Version()
        self.metadata = M8Metadata()
        self.song = M8SongMatrix()
        self.chains = M8Chains()
        self.phrases = M8Phrases()
        self.instruments = M8Instruments()
        self.data = bytearray(sum(OFFSETS.values()))

    @classmethod
    def read(cls, data):
        instance = cls()
        instance.data = bytearray(data)

        instance.version = M8Version.read(data[OFFSETS["version"]:])
        instance.metadata = M8Metadata.read(data[OFFSETS["metadata"]:])
        instance.song = M8SongMatrix.read(data[OFFSETS["song"]:])
        instance.chains = M8Chains.read(data[OFFSETS["chains"]:])
        instance.phrases = M8Phrases.read(data[OFFSETS["phrases"]:])
        instance.instruments = M8Instruments.read(data[OFFSETS["instruments"]:])

        return instance

    # Instrument methods
    @property
    def available_instrument_slot(self):
        for slot_idx, instrument in enumerate(self.instruments):
            if isinstance(instrument, M8Block):
                return slot_idx
        return None

    def add_instrument(self, instrument):
        slot = self.available_instrument_slot
        if slot is None:
            raise M8IndexError("No empty instrument slots available in this project")
            
        self.instruments[slot] = instrument
        return slot
        
    def set_instrument(self, instrument, slot):
        if not (0 <= slot < len(self.instruments)):
            raise M8IndexError(f"Instrument slot index must be between 0 and {len(self.instruments)-1}")
            
        self.instruments[slot] = instrument

    # Phrase methods
    @property
    def available_phrase_slot(self):
        for slot_idx, phrase in enumerate(self.phrases):
            if phrase.is_empty():
                return slot_idx
        return None

    def add_phrase(self, phrase):
        slot = self.available_phrase_slot
        if slot is None:
            raise M8IndexError("No empty phrase slots available in this project")
            
        self.phrases[slot] = phrase
        return slot
        
    def set_phrase(self, phrase, slot):
        if not (0 <= slot < len(self.phrases)):
            raise M8IndexError(f"Phrase slot index must be between 0 and {len(self.phrases)-1}")
            
        self.phrases[slot] = phrase

    # Chain methods
    @property
    def available_chain_slot(self):
        for slot_idx, chain in enumerate(self.chains):
            if chain.is_empty():
                return slot_idx
        return None

    def add_chain(self, chain):
        slot = self.available_chain_slot
        if slot is None:
            raise M8IndexError("No empty chain slots available in this project")
            
        self.chains[slot] = chain
        return slot
        
    def set_chain(self, chain, slot):
        if not (0 <= slot < len(self.chains)):
            raise M8IndexError(f"Chain slot index must be between 0 and {len(self.chains)-1}")
            
        self.chains[slot] = chain

    def validate(self):
        # Song -> Chains validation
        self.song.validate_chains(self.chains)
        
        # Chains -> Phrases validation
        self.chains.validate_phrases(self.phrases)
        
        # Phrases -> Instruments validation
        self.phrases.validate_instruments(self.instruments)
    
    def write(self) -> bytes:
        output = bytearray(self.data)
        for name, offset in OFFSETS.items():
            if hasattr(self, name):
                block = getattr(self, name)
                data = block.write()
                output[offset:offset + len(data)] = data
        return bytes(output)

    @staticmethod
    def read_from_file(filename: str):
        with open(filename, "rb") as f:
            return M8Project.read(f.read())

    def write_to_file(self, filename: str):
        with open(filename, "wb") as f:
            f.write(self.write())

    def as_dict(self):
        """Convert project to dictionary for serialization"""
        return {
            "__class__": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "version": self.version.as_dict(),
            "metadata": self.metadata.as_dict(),
            "song": self.song.as_dict(),
            "chains": self.chains.as_dict(),
            "phrases": self.phrases.as_dict(),
            "instruments": self.instruments.as_dict()
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a project from a dictionary"""
        instance = cls()
        
        # Deserialize version
        if "version" in data:
            instance.version = M8Version.from_dict(data["version"])
            
        # Deserialize metadata
        if "metadata" in data:
            instance.metadata = M8Metadata.from_dict(data["metadata"])
            
        # Deserialize song
        if "song" in data:
            instance.song = M8SongMatrix.from_dict(data["song"])
            
        # Deserialize chains
        if "chains" in data:
            instance.chains = M8Chains.from_dict(data["chains"])
            
        # Deserialize phrases
        if "phrases" in data:
            instance.phrases = M8Phrases.from_dict(data["phrases"])
            
        # Deserialize instruments
        if "instruments" in data:
            instance.instruments = M8Instruments.from_dict(data["instruments"])
        
        return instance
        
    def write_to_json_file(self, filename):
        """Write project to a JSON file"""
        with open(filename, "w") as f:
            f.write(self.to_json(indent=2))
            
    @classmethod
    def read_from_json_file(cls, filename):
        """Read project from a JSON file"""
        with open(filename, "r") as f:
            json_str = f.read()
        return from_json(json_str, cls)

    def to_json(self, indent=2):
        """Convert project to JSON string"""
        return to_json(self, indent=indent)

    @classmethod
    def from_json(cls, json_str):
        """Create an instance from a JSON string"""
        return from_json(json_str, cls)
