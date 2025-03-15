from m8.api import M8Block, json_dumps, json_loads
from m8.api.chains import M8Chains
from m8.api.instruments import M8Instruments
from m8.api.metadata import M8Metadata
from m8.api.phrases import M8Phrases
from m8.api.song import M8SongMatrix
from m8.api.version import M8Version

# Reference: https://github.com/AlexCharlton/m8-files/blob/2e79f2592e3950c20081f93aaad135fb9f867f9f/src/songs.rs

# Offsets in the M8 project file for different data sections
OFFSETS = {
    "version": 0x0A,          # Version information
    "metadata": 0x0E,         # Song metadata (name, directory, etc.)
    "groove": 0xEE,           # Groove settings
    "song": 0x2EE,            # Song matrix
    "phrases": 0xAEE,         # Phrase data
    "chains": 0x9A5E,         # Chain data
    "table": 0xBA3E,          # Table data
    "instruments": 0x13A3E,   # Instrument data
    "effect_settings": 0x1A5C1, # Effect settings
    "midi_mapping": 0x1A5FE,  # MIDI mapping configuration
    "scale": 0x1AA7E,         # Scale settings
    "eq": 0x1AD5A + 4         # Equalizer settings
}

class M8Project:
    """Represents a complete M8 project/song file.
    
    The M8Project is the top-level container for all M8 data, including
    metadata, instruments, chains, phrases, and the song arrangement.
    It provides methods for loading, saving, validating, and modifying M8 projects.
    """
    
    def __init__(self):
        """Initialize an empty M8 project.
        
        Creates a new project with default/empty components. This constructor is typically
        not called directly; instead, use class methods like read(), read_from_file(),
        or initialise() to create projects from existing data or templates.
        
        Note: This initializes an incomplete project. For a fully functional project with
        proper default settings, use M8Project.initialise() instead.
        """
        self.data = bytearray()
        self.version = None
        self.metadata = None
        self.song = None
        self.chains = None
        self.phrases = None
        self.instruments = None

    @classmethod
    def read(cls, data):
        """Create a project from binary data.
        
        Args:
            data: Binary data containing an M8 project file
            
        Returns:
            M8Project: New instance with components initialized from the binary data
        """
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
        """Find the first available (empty) instrument slot.
        
        Returns:
            int: Index of the first empty slot, or None if all slots are used
        """
        for slot_idx, instrument in enumerate(self.instruments):
            if isinstance(instrument, M8Block):
                return slot_idx
        return None

    def add_instrument(self, instrument):
        """Add an instrument to the first available slot.
        
        Args:
            instrument: The instrument to add
            
        Returns:
            int: The index where the instrument was added
            
        Raises:
            IndexError: If no empty slots are available
        """
        slot = self.available_instrument_slot
        if slot is None:
            raise IndexError("No empty instrument slots available in this project")
            
        self.instruments[slot] = instrument
        return slot
        
    def set_instrument(self, instrument, slot):
        """Set an instrument at a specific slot.
        
        Args:
            instrument: The instrument to set
            slot: The slot index to set
            
        Raises:
            IndexError: If the slot index is out of range
        """
        if not (0 <= slot < len(self.instruments)):
            raise IndexError(f"Instrument slot index must be between 0 and {len(self.instruments)-1}")
            
        self.instruments[slot] = instrument

    # Phrase methods
    @property
    def available_phrase_slot(self):
        """Find the first available (empty) phrase slot.
        
        Returns:
            int: Index of the first empty slot, or None if all slots are used
        """
        for slot_idx, phrase in enumerate(self.phrases):
            if phrase.is_empty():
                return slot_idx
        return None

    def add_phrase(self, phrase):
        """Add a phrase to the first available slot.
        
        Args:
            phrase: The phrase to add
            
        Returns:
            int: The index where the phrase was added
            
        Raises:
            IndexError: If no empty slots are available
        """
        slot = self.available_phrase_slot
        if slot is None:
            raise IndexError("No empty phrase slots available in this project")
            
        self.phrases[slot] = phrase
        return slot
        
    def set_phrase(self, phrase, slot):
        """Set a phrase at a specific slot.
        
        Args:
            phrase: The phrase to set
            slot: The slot index to set
            
        Raises:
            IndexError: If the slot index is out of range
        """
        if not (0 <= slot < len(self.phrases)):
            raise IndexError(f"Phrase slot index must be between 0 and {len(self.phrases)-1}")
            
        self.phrases[slot] = phrase

    # Chain methods
    @property
    def available_chain_slot(self):
        """Find the first available (empty) chain slot.
        
        Returns:
            int: Index of the first empty slot, or None if all slots are used
        """
        for slot_idx, chain in enumerate(self.chains):
            if chain.is_empty():
                return slot_idx
        return None

    def add_chain(self, chain):
        """Add a chain to the first available slot.
        
        Args:
            chain: The chain to add
            
        Returns:
            int: The index where the chain was added
            
        Raises:
            IndexError: If no empty slots are available
        """
        slot = self.available_chain_slot
        if slot is None:
            raise IndexError("No empty chain slots available in this project")
            
        self.chains[slot] = chain
        return slot
        
    def set_chain(self, chain, slot):
        """Set a chain at a specific slot.
        
        Args:
            chain: The chain to set
            slot: The slot index to set
            
        Raises:
            IndexError: If the slot index is out of range
        """
        if not (0 <= slot < len(self.chains)):
            raise IndexError(f"Chain slot index must be between 0 and {len(self.chains)-1}")
            
        self.chains[slot] = chain

    def validate(self):
        """Validate the entire project for references consistency.
        
        Ensures that all references are valid across the project:
        - Song references valid chains
        - Chains reference valid phrases
        - Phrases reference valid instruments
        
        Raises:
            M8ValidationError: If any validation check fails
        """
        # Song -> Chains validation
        self.song.validate_chains(self.chains)
        
        # Chains -> Phrases validation
        self.chains.validate_phrases(self.phrases)
        
        # Phrases -> Instruments validation
        self.phrases.validate_instruments(self.instruments)
    
    def write(self) -> bytes:
        """Convert the project to binary data.
        
        Serializes the entire project to binary format that's compatible with the M8 tracker.
        This method writes all modified components back to their respective positions
        in the project data buffer, preserving the M8's binary file structure.
        
        The resulting binary data can be written directly to a .m8s file, which
        can be loaded in the M8 tracker. Note that this method only creates the binary
        representation; use write_to_file() to save it to disk.
        
        Returns:
            bytes: Binary representation of the entire project, ready for saving to an M8 file
        """
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
        """Read a project from a binary file.
        
        Args:
            filename: Path to the M8 project file (.m8s)
            
        Returns:
            M8Project: New instance loaded from the file
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            IOError: If the file can't be read
        """
        with open(filename, "rb") as f:
            return M8Project.read(f.read())

    @classmethod
    def initialise(cls, template_name: str = "DEFAULT401"):
        """Create a new M8Project from a template file.
        
        Loads a template song file to use as the starting point for a new project.
        Searches for the template in various locations including installed packages
        and local development paths.
        
        Args:
            template_name: Name of the template file without the .m8s extension (default: DEFAULT401)
            
        Returns:
            M8Project: New instance initialized from the template
            
        Raises:
            FileNotFoundError: If the template file cannot be found
        """
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
        """Write this project to a binary file.
        
        Args:
            filename: Path where the M8 project file (.m8s) will be written
            
        Raises:
            IOError: If the file can't be written
        """
        with open(filename, "wb") as f:
            f.write(self.write())

    def as_dict(self):
        """Convert project to dictionary for serialization.
        
        Creates a hierarchical dictionary representation of the entire project,
        suitable for JSON serialization or human-readable export. Uses the
        individual serialization methods of each component to build a complete
        representation of the project structure.
        
        This is useful for:
        - Storing projects in formats other than the binary M8 format
        - Creating human-readable project exports
        - Programmatically analyzing or modifying project structure
        
        Returns:
            dict: Dictionary representation of the project with all components,
                structured hierarchically with version, metadata, song, chains,
                phrases, and instruments
        """
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
        """Create a project from a dictionary.
        
        Deserializes a project from a dictionary representation, typically
        created by the as_dict() method or loaded from JSON. Reconstructs
        all project components from their serialized forms.
        
        This is the inverse operation of as_dict() and can be used to:
        - Load projects stored in JSON format
        - Create projects programmatically from structured data
        - Import projects from non-M8 formats that have been converted
          to the expected dictionary structure
        
        Args:
            data (dict): Dictionary containing serialized project components
                       with keys for "version", "metadata", "song", "chains",
                       "phrases", and "instruments"
            
        Returns:
            M8Project: New instance with all components reconstructed from
                     the dictionary representation
        """
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
        """Write project to a JSON file.
        
        Creates a human-readable JSON representation of the project and saves it to a file.
        This provides an alternative to the binary .m8s format, making project data
        accessible for inspection, manual editing, or integration with other tools.
        
        The JSON format preserves the full structure of the project but in a format that
        is easier to read, edit, and process with standard tools. Unlike the binary format,
        the JSON representation:
        - Is human-readable and editable in any text editor
        - Can be parsed by standard JSON libraries in any programming language
        - Provides a clear view of project structure and relationships
        - Is suitable for version control systems like Git
        
        Args:
            filename (str): Path where the JSON file will be written
            
        Raises:
            IOError: If the file can't be written due to permission issues,
                   path not existing, or other I/O errors
        """
        with open(filename, "w") as f:
            f.write(json_dumps(self.as_dict()))
            
    @classmethod
    def read_from_json_file(cls, filename):
        """Read project from a JSON file.
        
        Loads a project that was previously saved in JSON format using
        the write_to_json_file() method. This is the inverse operation
        and allows projects to be loaded from human-readable JSON files.
        
        This method is useful for:
        - Loading projects that were stored or exchanged in JSON format
        - Reading projects that were modified manually or by external tools
        - Migrating projects between M8 firmware versions (through manual edits)
        - Developing and testing projects in a more human-friendly format
        
        Args:
            filename (str): Path to the JSON file to read
            
        Returns:
            M8Project: New instance loaded from the JSON data
            
        Raises:
            FileNotFoundError: If the specified file doesn't exist
            IOError: If the file can't be read due to permission issues
            JSONDecodeError: If the file contains invalid JSON syntax
        """
        with open(filename, "r") as f:
            json_str = f.read()
        return M8Project.from_dict(json_loads(json_str))

