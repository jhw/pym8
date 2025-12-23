from m8.api import M8Block
from m8.api.chain import M8Chains, CHAINS_OFFSET
from m8.api.instrument import M8Instruments, INSTRUMENTS_OFFSET
from m8.api.metadata import M8Metadata, METADATA_OFFSET
from m8.api.phrase import M8Phrases, PHRASES_OFFSET
from m8.api.song import M8SongMatrix, SONG_OFFSET
from m8.api.version import M8Version

# Reference: https://github.com/AlexCharlton/m8-files/blob/2e79f2592e3950c20081f93aaad135fb9f867f9f/src/songs.rs

# Project file offsets
VERSION_OFFSET = 10
GROOVE_OFFSET = 238
TABLE_OFFSET = 47678
EFFECT_SETTINGS_OFFSET = 107969
MIDI_MAPPING_OFFSET = 108030
SCALE_OFFSET = 109182
EQ_OFFSET = 109918

# Dictionary to cache offsets loaded from configuration
OFFSETS = {
    "version": VERSION_OFFSET,
    "metadata": METADATA_OFFSET,
    "groove": GROOVE_OFFSET,
    "song": SONG_OFFSET,
    "phrases": PHRASES_OFFSET,
    "chains": CHAINS_OFFSET,
    "table": TABLE_OFFSET,
    "instruments": INSTRUMENTS_OFFSET,
    "effect_settings": EFFECT_SETTINGS_OFFSET,
    "midi_mapping": MIDI_MAPPING_OFFSET,
    "scale": SCALE_OFFSET,
    "eq": EQ_OFFSET
}

class M8Project:
    """Top-level container for all M8 data, including metadata, instruments, chains, phrases, and song arrangement."""
    
    def __init__(self):
        self.data = bytearray()
        self.metadata = None
        self.song = None
        self.chains = None
        self.phrases = None
        self.instruments = None
        self.version = M8Version()

    @classmethod
    def read(cls, data):
        instance = cls()
        instance.data = bytearray(data)

        # Read version
        instance.version = M8Version.read(data[OFFSETS["version"]:])

        instance.metadata = M8Metadata.read(data[OFFSETS["metadata"]:])
        instance.song = M8SongMatrix.read(data[OFFSETS["song"]:])
        instance.chains = M8Chains.read(data[OFFSETS["chains"]:])
        instance.phrases = M8Phrases.read(data[OFFSETS["phrases"]:])
        instance.instruments = M8Instruments.read(data[OFFSETS["instruments"]:])

        # Context management was removed with enum system simplification

        return instance

    def clone(self):
        instance = self.__class__()
        
        # Clone all components
        instance.metadata = self.metadata.clone()
        instance.instruments = self.instruments.clone()
        instance.phrases = self.phrases.clone()
        instance.chains = self.chains.clone()
        instance.song = self.song.clone()
        
        # Copy version information if available
        if hasattr(self, '_version'):
            instance._version = self._version
            
        return instance
        
    def write(self) -> bytes:
        output = bytearray(self.data)
        
        # Write version data
        version_data = self.version.write()
        output[OFFSETS["version"]:OFFSETS["version"] + len(version_data)] = version_data
        
        for name, offset in OFFSETS.items():
            if hasattr(self, name) and name != "version":
                block = getattr(self, name)
                data = block.write()
                
                # Write the data to the output buffer
                output[offset:offset + len(data)] = data
        return bytes(output)

    @staticmethod
    def read_from_file(filename: str):
        with open(filename, "rb") as f:
            project = M8Project.read(f.read())
            
        # Context management was removed with enum system simplification
        
        return project

    @classmethod
    def initialise(cls, template_name: str = "TEMPLATE-6-2-1"):
        """Creates a new project from a template file."""
        import os
        import sys

        template_filename = template_name if template_name.endswith('.m8s') else f"{template_name}.m8s"

        # Strategy 1: Try importlib.resources (Python 3.7+, works with installed packages)
        try:
            import importlib.resources
            with importlib.resources.path('m8.templates', template_filename) as template_path:
                if os.path.exists(template_path):
                    return cls.read_from_file(str(template_path))
        except (ImportError, ModuleNotFoundError, FileNotFoundError, TypeError):
            pass

        # Strategy 2: Search sys.path for m8/templates
        for path in sys.path:
            potential_path = os.path.join(path, 'm8', 'templates', template_filename)
            if os.path.exists(potential_path):
                return cls.read_from_file(potential_path)

        # Strategy 3: Relative to this module (development/source installs)
        module_path = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(module_path, "..", "templates", template_filename)
        if os.path.exists(template_path):
            return cls.read_from_file(template_path)

        raise FileNotFoundError(f"Template '{template_filename}' not found. Check that it exists in the m8/templates directory.")

    def write_to_file(self, filename: str):
        import os

        # Create intermediate directories if they don't exist
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        with open(filename, "wb") as f:
            f.write(self.write())

