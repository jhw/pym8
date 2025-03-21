from m8.api import M8Block, json_dumps, json_loads
from m8.api.chains import M8Chains
from m8.api.instruments import M8Instruments
from m8.api.metadata import M8Metadata
from m8.api.phrases import M8Phrases
from m8.api.song import M8SongMatrix
from m8.api.version import M8Version
from m8.config import get_offset

# Reference: https://github.com/AlexCharlton/m8-files/blob/2e79f2592e3950c20081f93aaad135fb9f867f9f/src/songs.rs

# Dictionary to cache offsets loaded from configuration
OFFSETS = {
    "version": get_offset("version"),
    "metadata": get_offset("metadata"),
    "groove": get_offset("groove"),
    "song": get_offset("song"),
    "phrases": get_offset("phrases"),
    "chains": get_offset("chains"),
    "table": get_offset("table"),
    "instruments": get_offset("instruments"),
    "effect_settings": get_offset("effect_settings"),
    "midi_mapping": get_offset("midi_mapping"),
    "scale": get_offset("scale"),
    "eq": get_offset("eq")
}

class M8Project:
    """Top-level container for all M8 data, including metadata, instruments, chains, phrases, and song arrangement."""
    
    def __init__(self):
        self.data = bytearray()
        self.version = None
        self.metadata = None
        self.song = None
        self.chains = None
        self.phrases = None
        self.instruments = None

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
        """Validates references consistency between song, chains, phrases, and instruments."""
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

    @classmethod
    def initialise(cls, template_name: str = "DEFAULT401"):
        """Creates a new project from a template file, searching in multiple locations."""
        import os
        import sys
        
        # Try multiple approaches to find the template file
        
        # 1. Direct check for site-packages installation
        for path in sys.path:
            if 'site-packages' in path:
                potential_path = os.path.join(path, 'm8', 'templates', f"{template_name}.m8s")
                if os.path.exists(potential_path):
                    return cls.read_from_file(potential_path)
        
        # 2. Try pkg_resources as a fallback
        try:
            import pkg_resources
            try:
                template_path = pkg_resources.resource_filename('m8', f'templates/{template_name}.m8s')
                if os.path.exists(template_path):
                    return cls.read_from_file(template_path)
            except (ImportError, pkg_resources.DistributionNotFound, TypeError):
                # If pkg_resources.resource_filename fails, continue to next approach
                pass
        except ImportError:
            # pkg_resources not available
            pass
            
        # 3. Try relative path (for local development)
        module_path = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(module_path, "..", "templates", f"{template_name}.m8s")
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template '{template_name}' not found. Check that {template_name}.m8s exists in the m8/templates directory.")
            
        return cls.read_from_file(template_path)

    def write_to_file(self, filename: str):
        with open(filename, "wb") as f:
            f.write(self.write())

    def as_dict(self):
        """Converts project to a hierarchical dictionary for serialization."""
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
        """Creates a project from a dictionary representation."""
        instance = cls()
        
        # Deserialize each component
        if "version" in data:
            instance.version = M8Version.from_str(data["version"])
            
        if "metadata" in data:
            instance.metadata = M8Metadata.from_dict(data["metadata"])
            
        if "song" in data:
            instance.song = M8SongMatrix.from_list(data["song"])
            
        if "chains" in data:
            instance.chains = M8Chains.from_list(data["chains"])
            
        if "phrases" in data:
            instance.phrases = M8Phrases.from_list(data["phrases"])
            
        if "instruments" in data:
            instance.instruments = M8Instruments.from_list(data["instruments"])
        
        return instance
        
    def write_to_json_file(self, filename):
        """Writes project to a human-readable JSON file."""
        with open(filename, "w") as f:
            f.write(json_dumps(self.as_dict()))
            
    @classmethod
    def read_from_json_file(cls, filename):
        """Reads project from a JSON file previously created with write_to_json_file."""
        with open(filename, "r") as f:
            json_str = f.read()
        return M8Project.from_dict(json_loads(json_str))

