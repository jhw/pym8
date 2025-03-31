from m8.api import M8Block, json_dumps, json_loads
from m8.api.chains import M8Chains
from m8.api.instruments import M8Instruments
from m8.api.metadata import M8Metadata
from m8.api.phrases import M8Phrases
from m8.api.song import M8SongMatrix
from m8.api.version import M8Version
from m8.config import get_offset
from m8.core.validation import M8ValidationResult
import logging

# Set up logging
logger = logging.getLogger(__name__)

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

        # Read version, store it, and log it
        instance.version = M8Version.read(data[OFFSETS["version"]:])
        logger.info(f"M8 file version: {instance.version}")

        instance.metadata = M8Metadata.read(data[OFFSETS["metadata"]:])
        instance.song = M8SongMatrix.read(data[OFFSETS["song"]:])
        instance.chains = M8Chains.read(data[OFFSETS["chains"]:])
        instance.phrases = M8Phrases.read(data[OFFSETS["phrases"]:])
        instance.instruments = M8Instruments.read(data[OFFSETS["instruments"]:])

        # This handles the case when read() is called directly without read_from_file()
        from m8.core.enums import M8InstrumentContext
        context = M8InstrumentContext.get_instance()
        context.set_project(instance)

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
            
        # Set the instrument's version to match project version
        if hasattr(instrument, 'version'):
            instrument.version = self.version
            
        self.instruments[slot] = instrument
        return slot
        
    def set_instrument(self, instrument, slot):
        if not (0 <= slot < len(self.instruments)):
            raise IndexError(f"Instrument slot index must be between 0 and {len(self.instruments)-1}")
            
        # Set the instrument's version to match project version
        if hasattr(instrument, 'version'):
            instrument.version = self.version
            
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
        
    def validate_references(self, result=None):
        """Validate all references between components."""
        if result is None:
            result = M8ValidationResult(context="project.references")
            
        try:
            # Song -> Chains validation
            self.song.validate_references_chains(self.chains)
        except ValueError as e:
            result.add_error(str(e), "song")
            
        try:
            # Chains -> Phrases validation
            self.chains.validate_references_phrases(self.phrases)
        except ValueError as e:
            result.add_error(str(e), "chains")
            
        try:
            # Phrases -> Instruments validation
            self.phrases.validate_references_instruments(self.instruments)
        except ValueError as e:
            result.add_error(str(e), "phrases")
            
        return result
        
    def validate_one_to_one_chains(self, result=None):
        """Validates chains have one phrase matching their own ID."""
        if result is None:
            result = M8ValidationResult(context="project.one_to_one")
            
        for chain_idx, chain in enumerate(self.chains):
            if not chain.is_empty():
                chain_result = chain.validate_one_to_one_pattern(chain_idx)
                if not chain_result.valid:
                    result.merge(chain_result, f"chain[{chain_idx}]")
                    
        return result
        
    def validate_versions(self, result=None):
        """Validates that all instruments have the same version as the project."""
        if result is None:
            result = M8ValidationResult(context="project.versions")
            
        if not hasattr(self, 'instruments') or self.instruments is None:
            return result
            
        for instr_idx, instrument in enumerate(self.instruments):
            if hasattr(instrument, 'version') and not isinstance(instrument, M8Block):
                if str(instrument.version) != str(self.version):
                    result.add_error(
                        f"Instrument has version {instrument.version} but project has version {self.version}",
                        f"instrument[{instr_idx}]"
                    )
                    
        return result
        
    def validate(self, check_one_to_one=False, raise_on_error=True, log_errors=False):
        """Validate the entire project.
        
        Args:
            check_one_to_one: Whether to check for one-to-one chain patterns
            raise_on_error: Whether to raise an exception if validation fails
            log_errors: Whether to log validation errors via the logger
            
        Returns:
            M8ValidationResult: Result object containing validation status and errors
            
        Raises:
            ValueError: If validation fails and raise_on_error is True
        """
        # Create master validation result
        result = M8ValidationResult(context="project")
        
        # Run all validations and collect results
        result.merge(self.validate_references(), "references")
        
        if check_one_to_one:
            result.merge(self.validate_one_to_one_chains(), "one_to_one")
        
        result.merge(self.validate_versions(), "versions")
        result.merge(self.validate_completeness(), "completeness")
        
        # Handle logging if requested
        if log_errors:
            result.log_errors(logger)
            
        # Optionally raise exception
        if raise_on_error:
            result.raise_if_invalid()
            
        return result
        
    def validate_completeness(self, result=None):
        """Validate that all required components are complete."""
        if result is None:
            result = M8ValidationResult(context="project.completeness")
            
        # Check phrases completeness
        if self.phrases is not None and not self.phrases.is_complete():
            result.add_error("Phrases are incomplete", "phrases")
            
        # Additional chain and instrument validation can be added here
        
        return result
    
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
            
        # Set the project on the context manager for proper enum resolution
        from m8.core.enums import M8InstrumentContext
        context = M8InstrumentContext.get_instance()
        context.set_project(project)
        
        return project

    @classmethod
    def initialise(cls, template_name: str = "TEMPLATE-5-0-1-4-0-33"):
        """Creates a new project from a template file."""
        import os
        import sys
        
        template_filename = template_name if template_name.endswith('.m8s') else f"{template_name}.m8s"
        
        try:
            import importlib.resources
            try:
                with importlib.resources.path('m8.templates', template_filename) as template_path:
                    if os.path.exists(template_path):
                        # Will automatically set the project on the context manager
                        return cls.read_from_file(str(template_path))
            except (ImportError, ModuleNotFoundError, FileNotFoundError):
                pass
        except ImportError:
            pass
            
        for path in sys.path:
            potential_path = os.path.join(path, 'm8', 'templates', template_filename)
            if os.path.exists(potential_path):
                return cls.read_from_file(potential_path)
            
        module_path = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(module_path, "..", "templates", template_filename)
        
        if os.path.exists(template_path):
            return cls.read_from_file(template_path)
            
        raise FileNotFoundError(f"Template '{template_filename}' not found. Check that it exists in the m8/templates directory.")

    def write_to_file(self, filename: str):
        with open(filename, "wb") as f:
            f.write(self.write())

    def as_dict(self):
        """Converts project to a hierarchical dictionary for serialization."""
        return {
            "metadata": self.metadata.as_dict(),
            "song": self.song.as_list(),
            "chains": self.chains.as_list(),
            "phrases": self.phrases.as_list(),
            "instruments": self.instruments.as_list()
            # Version is deliberately excluded from serialization
        }
    
    @classmethod
    def from_dict(cls, data):
        """Creates a project from a dictionary representation."""
        instance = cls()
        
        # Deserialize each component
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

