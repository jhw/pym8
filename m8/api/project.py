from m8.api import M8Block
from m8.api.chain import M8Chains, CHAINS_OFFSET
from m8.api.instrument import M8Instruments, INSTRUMENTS_OFFSET
from m8.api.metadata import M8Metadata, METADATA_OFFSET
from m8.api.phrase import M8Phrases, PHRASES_OFFSET
from m8.api.song import M8SongMatrix, SONG_OFFSET
from m8.api.version import M8Version

# Reference: https://github.com/Twinside/m8-file-parser/blob/master/src/songs.rs

VERSION_OFFSET = 10

# Offsets for sections pym8 actively parses. Sections present in the binary
# format but not parsed (groove, table, effect_settings, midi_mapping, scale,
# eq) are preserved verbatim through the raw `data` buffer.
OFFSETS = {
    "version": VERSION_OFFSET,
    "metadata": METADATA_OFFSET,
    "song": SONG_OFFSET,
    "phrases": PHRASES_OFFSET,
    "chains": CHAINS_OFFSET,
    "instruments": INSTRUMENTS_OFFSET,
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
        instance.version = M8Version.read(data[OFFSETS["version"]:])

        # Sections that don't yet have firmware-conditional logic — read
        # without threading version. Add the parameter on a per-section basis
        # when implementing settings/EQ/etc. (see docs/planning/roadmap.md).
        instance.metadata = M8Metadata.read(data[OFFSETS["metadata"]:])
        instance.song = M8SongMatrix.read(data[OFFSETS["song"]:])
        instance.chains = M8Chains.read(data[OFFSETS["chains"]:])
        instance.phrases = M8Phrases.read(data[OFFSETS["phrases"]:])

        # Instruments will be the first consumer (per-instrument associated_eq
        # in v6.0+, settings byte packing differences); thread version through.
        instance.instruments = M8Instruments.read(
            data[OFFSETS["instruments"]:], version=instance.version,
        )
        return instance

    def clone(self):
        instance = self.__class__()
        instance.data = bytearray(self.data)
        instance.version = M8Version(self.version.major, self.version.minor, self.version.patch)
        instance.metadata = self.metadata.clone() if self.metadata else None
        instance.instruments = self.instruments.clone() if self.instruments else None
        instance.phrases = self.phrases.clone() if self.phrases else None
        instance.chains = self.chains.clone() if self.chains else None
        instance.song = self.song.clone() if self.song else None
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

    def validate(self):
        """Validate all project components.

        Validates:
        - Chains collection (count and phrase references)
        - Phrases collection (count and instrument references)
        - Song matrix (chain references)
        - Instruments collection (count)

        Raises:
            ValueError: If any validation fails
        """
        if self.chains:
            self.chains.validate()
        if self.phrases:
            self.phrases.validate()
        if self.song:
            self.song.validate()
        if self.instruments:
            self.instruments.validate()

