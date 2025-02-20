from m8 import NULL
from m8.core.object import m8_object_class
from m8.utils.bits import split_byte, join_nibbles

from m8.chains import M8Chains
from m8.instruments import M8Instruments
from m8.phrases import M8Phrases
from m8.song import M8SongMatrix

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

M8VersionBase = m8_object_class(
    field_map=[
        ("minor|patch", NULL, 0, 1, "UINT4_2"), 
        ("_|major", NULL, 1, 2, "UINT4_2")
    ]
)

class M8Version(M8VersionBase):

    def as_list(self):
        return [self.major, self.minor, self.patch]

M8Metadata = m8_object_class(
    field_map=[
        ("directory", "/Songs/woldo/", 0, 128, "STRING"),
        ("transpose", 0, 128, 129, "UINT8"),
        ("tempo", 120.0, 129, 133, "FLOAT32"),
        ("quantize", 0, 133, 134, "UINT8"),
        ("name", "HELLO_MACRO", 134, 146, "STRING"),
        ("key", 0, 146, 147, "UINT8")
    ]
)

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
