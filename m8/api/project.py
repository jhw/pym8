from m8.api import M8Block, json_dumps, json_loads
from m8.api.chains import M8Chains
from m8.api.instruments import M8Instruments
from m8.api.metadata import M8Metadata
from m8.api.phrases import M8Phrases
from m8.api.song import M8SongMatrix
from m8.api.version import M8Version

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

class M8Project:

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
            raise IndexError("No empty instrument slots available in this project")
            
        self.instruments[slot] = instrument
        return slot
        
    def set_instrument(self, instrument, slot):
        if not (0 <= slot < len(self.instruments)):
            raise IndexError(f"Instrument slot index must be between 0 and {len(self.instruments)-1}")
            
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
            raise IndexError("No empty phrase slots available in this project")
            
        self.phrases[slot] = phrase
        return slot
        
    def set_phrase(self, phrase, slot):
        if not (0 <= slot < len(self.phrases)):
            raise IndexError(f"Phrase slot index must be between 0 and {len(self.phrases)-1}")
            
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
            raise IndexError("No empty chain slots available in this project")
            
        self.chains[slot] = chain
        return slot
        
    def set_chain(self, chain, slot):
        if not (0 <= slot < len(self.chains)):
            raise IndexError(f"Chain slot index must be between 0 and {len(self.chains)-1}")
            
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
                
                # Write the data to the output buffer
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
            "version": str(self.version),
            "metadata": self.metadata.as_dict(),
            "song": self.song.as_list(),
            "chains": self.chains.as_list(),
            "phrases": self.phrases.as_list(),
            "instruments": self.instruments.as_list()
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a project from a dictionary"""
        instance = cls()
        
        # Deserialize version
        if "version" in data:
            instance.version = M8Version.from_str(data["version"])
            
        # Deserialize metadata
        if "metadata" in data:
            instance.metadata = M8Metadata.from_dict(data["metadata"])
            
        # Deserialize song
        if "song" in data:
            instance.song = M8SongMatrix.from_list(data["song"])
            
        # Deserialize chains
        if "chains" in data:
            instance.chains = M8Chains.from_list(data["chains"])
            
        # Deserialize phrases
        if "phrases" in data:
            instance.phrases = M8Phrases.from_list(data["phrases"])
            
        # Deserialize instruments
        if "instruments" in data:
            instance.instruments = M8Instruments.from_list(data["instruments"])
        
        return instance
        
    def write_to_json_file(self, filename):
        """Write project to a JSON file"""
        with open(filename, "w") as f:
            f.write(json_dumps(self.as_dict()))
            
    @classmethod
    def read_from_json_file(cls, filename):
        """Read project from a JSON file"""
        with open(filename, "r") as f:
            json_str = f.read()
        return M8Project.from_dict(json_loads(json_str))

