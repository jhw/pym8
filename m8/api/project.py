from m8.api import M8Block
from m8.api.chain import M8Chains, CHAINS_OFFSET
from m8.api.eq import M8Eqs
from m8.api.instrument import M8Instruments, INSTRUMENTS_OFFSET
from m8.api.metadata import M8Metadata, METADATA_OFFSET
from m8.api.midi_settings import M8MidiSettings
from m8.api.phrase import M8Phrases, PHRASES_OFFSET
from m8.api.settings import M8EffectsSettings, M8MixerSettings
from m8.api.song import M8SongMatrix, SONG_OFFSET
from m8.api.version import M8Version

# Reference: https://github.com/Twinside/m8-file-parser/blob/master/src/songs.rs

VERSION_OFFSET = 10

# MidiSettings starts immediately after metadata (file 14-159; contiguous
# metadata block is 146 bytes ending at the project name).
MIDI_SETTINGS_OFFSET = 160       # 27 bytes
KEY_OFFSET = 187                 # 1 byte (project musical key)
# bytes 188-205 reserved        # preserved as raw data

MIXER_SETTINGS_OFFSET = 206

# Effects/MIDI-mapping/scale/EQ offsets (v4.1+ — both V4_0 and V4_1 in
# m8-file-parser use these same offsets; only inner counts differ, and
# pym8 targets v6.0+).
EFFECTS_SETTINGS_OFFSET = 107969  # 0x1A5C1
EQ_OFFSET = 109918                # 0x1AD5A + 4

# Offsets for sections pym8 parses today. Sections present in the binary
# format but not yet parsed (groove, table, midi_mapping, scale) are
# preserved verbatim through the raw `data` buffer. The musical-key byte
# at offset 187 isn't a section per se — M8Project handles it specially
# (see read/write below).
OFFSETS = {
    "version": VERSION_OFFSET,
    "metadata": METADATA_OFFSET,
    "midi": MIDI_SETTINGS_OFFSET,
    "mixer": MIXER_SETTINGS_OFFSET,
    "song": SONG_OFFSET,
    "phrases": PHRASES_OFFSET,
    "chains": CHAINS_OFFSET,
    "instruments": INSTRUMENTS_OFFSET,
    "effects": EFFECTS_SETTINGS_OFFSET,
    "eq": EQ_OFFSET,
}

class M8Project:
    """Top-level container for all M8 data, including metadata, instruments, chains, phrases, and song arrangement."""
    
    def __init__(self):
        self.data = bytearray()
        self.metadata = None
        self.midi = None
        self.song = None
        self.chains = None
        self.phrases = None
        self.instruments = None
        self.mixer = None
        self.effects = None
        self.eq = None
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
        instance.midi = M8MidiSettings.read(
            data[OFFSETS["midi"]:OFFSETS["midi"] + M8MidiSettings.BYTES],
            version=instance.version,
        )
        # The musical key byte sits between MidiSettings and the 18 reserved
        # bytes that precede MixerSettings. Exposed on metadata for ergonomics
        # even though the byte itself isn't in the contiguous metadata block.
        instance.metadata.key = data[KEY_OFFSET]

        instance.song = M8SongMatrix.read(data[OFFSETS["song"]:])
        instance.chains = M8Chains.read(data[OFFSETS["chains"]:])
        instance.phrases = M8Phrases.read(data[OFFSETS["phrases"]:])

        # Sections that consume firmware version (per-instrument
        # associated_eq byte, mixer limiter v6.0+ / OTT v6.2+, EQ count).
        instance.mixer = M8MixerSettings.read(
            data[OFFSETS["mixer"]:OFFSETS["mixer"] + M8MixerSettings.BYTES],
            version=instance.version,
        )
        instance.instruments = M8Instruments.read(
            data[OFFSETS["instruments"]:], version=instance.version,
        )
        instance.effects = M8EffectsSettings.read(
            data[OFFSETS["effects"]:OFFSETS["effects"] + M8EffectsSettings.BYTES],
            version=instance.version,
        )
        instance.eq = M8Eqs.read(
            data[OFFSETS["eq"]:OFFSETS["eq"] + M8Eqs.TOTAL_BYTES],
            version=instance.version,
        )
        return instance

    def clone(self):
        instance = self.__class__()
        instance.data = bytearray(self.data)
        instance.version = M8Version(self.version.major, self.version.minor, self.version.patch)
        instance.metadata = self.metadata.clone() if self.metadata else None
        instance.midi = self.midi.clone() if self.midi else None
        instance.instruments = self.instruments.clone() if self.instruments else None
        instance.phrases = self.phrases.clone() if self.phrases else None
        instance.chains = self.chains.clone() if self.chains else None
        instance.song = self.song.clone() if self.song else None
        instance.mixer = self.mixer.clone() if self.mixer else None
        instance.effects = self.effects.clone() if self.effects else None
        instance.eq = self.eq.clone() if self.eq else None
        return instance
        
    def write(self) -> bytes:
        output = bytearray(self.data)

        # Version is a 4-byte header at offset 10 — handled specially
        # because it's a value, not a section block.
        version_data = self.version.write()
        output[OFFSETS["version"]:OFFSETS["version"] + len(version_data)] = version_data

        for name, offset in OFFSETS.items():
            if hasattr(self, name) and name != "version":
                block = getattr(self, name)
                if block is None:
                    continue
                data = block.write()
                output[offset:offset + len(data)] = data

        # Musical key byte at file offset 187 — exposed via
        # metadata.key but not part of any contiguous block, so written
        # explicitly here.
        if self.metadata is not None:
            output[KEY_OFFSET] = self.metadata.key & 0xFF

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

