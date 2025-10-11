# m8/api/sampler.py
"""M8 Sampler instrument - the only instrument type supported."""

from m8.api import M8Block, read_fixed_string, write_fixed_string
from m8.api.version import M8Version
from m8.config import load_format_config, get_offset

# Load configuration
config = load_format_config()

# Block sizes and counts for samplers
BLOCK_SIZE = config["instruments"]["block_size"]
BLOCK_COUNT = config["instruments"]["count"]

# Sampler configuration
SAMPLER_CONFIG = config["instruments"]["types"]["SAMPLER"]
SAMPLER_TYPE_ID = SAMPLER_CONFIG["type_id"]

# Common parameter offsets from config
common_fields = config["instruments"]["common_fields"]

TYPE_OFFSET = common_fields["type"]["offset"]
NAME_OFFSET = common_fields["name"]["offset"]
NAME_LENGTH = common_fields["name"]["size"]
VOLUME_OFFSET = common_fields["volume"]["offset"]
PITCH_OFFSET = common_fields["pitch"]["offset"]
FINETUNE_OFFSET = common_fields["finetune"]["offset"]
TABLE_TICK_OFFSET = common_fields["table_tick"]["offset"]
TRANSPOSE_EQ_OFFSET = common_fields["transpose_eq"]["offset"]


class M8SamplerParams:
    """Sampler-specific parameters."""

    def __init__(self, play_mode=0, slice=0, sample_path=""):
        self.play_mode = play_mode
        self.slice = slice
        self.sample_path = sample_path

    def read(self, data):
        """Read parameters from binary data."""
        self.play_mode = data[SAMPLER_CONFIG["params"]["play_mode"]["offset"]]
        self.slice = data[SAMPLER_CONFIG["params"]["slice"]["offset"]]

        # Read sample_path
        sample_path_config = SAMPLER_CONFIG["sample_path"]
        offset = sample_path_config["offset"]
        size = sample_path_config["size"]
        self.sample_path = read_fixed_string(data, offset, size)

    def write(self):
        """Write parameters to binary data."""
        # Calculate buffer size needed
        sample_path_config = SAMPLER_CONFIG["sample_path"]
        max_offset = sample_path_config["offset"] + sample_path_config["size"]

        buffer = bytearray([0] * max_offset)

        buffer[SAMPLER_CONFIG["params"]["play_mode"]["offset"]] = self.play_mode & 0xFF
        buffer[SAMPLER_CONFIG["params"]["slice"]["offset"]] = self.slice & 0xFF

        # Write sample_path
        offset = sample_path_config["offset"]
        size = sample_path_config["size"]
        buffer[offset:offset + size] = write_fixed_string(self.sample_path, size)

        return bytes(buffer)

    def clone(self):
        """Create a copy of this params object."""
        return M8SamplerParams(
            play_mode=self.play_mode,
            slice=self.slice,
            sample_path=self.sample_path
        )

    def as_dict(self):
        """Convert to dictionary."""
        return {
            "play_mode": self.play_mode,
            "slice": self.slice,
            "sample_path": self.sample_path
        }

    @classmethod
    def from_dict(cls, data):
        """Create from dictionary."""
        return cls(
            play_mode=data.get("play_mode", 0),
            slice=data.get("slice", 0),
            sample_path=data.get("sample_path", "")
        )


class M8Sampler:
    """M8 Sampler instrument - the only instrument type supported."""

    def __init__(self, name="", sample_path="", play_mode=0, slice=0,
                 volume=255, pitch=64, transpose=4, eq=1, table_tick=1, finetune=128):
        """Initialize a sampler instrument with default parameters."""
        # Type is always SAMPLER
        self.type = SAMPLER_TYPE_ID

        # Version (set from project or file)
        self.version = M8Version()

        # Common parameters
        self.name = name
        self.volume = volume
        self.pitch = pitch
        self.transpose = transpose
        self.eq = eq
        self.table_tick = table_tick
        self.finetune = finetune

        # Sampler-specific parameters
        self.params = M8SamplerParams(play_mode, slice, sample_path)

    def _read_common_parameters(self, data):
        """Read common parameters from binary data."""
        self.type = data[TYPE_OFFSET]
        self.name = read_fixed_string(data, NAME_OFFSET, NAME_LENGTH)

        # Read transpose and eq from combined byte
        combined_byte = data[TRANSPOSE_EQ_OFFSET]
        self.transpose = combined_byte & 0x0F
        self.eq = (combined_byte >> 4) & 0x0F

        self.table_tick = data[TABLE_TICK_OFFSET]
        self.volume = data[VOLUME_OFFSET]
        self.pitch = data[PITCH_OFFSET]
        self.finetune = data[FINETUNE_OFFSET]

    def write(self):
        """Convert instrument to binary data."""
        buffer = bytearray([0] * BLOCK_SIZE)

        # Write type
        buffer[TYPE_OFFSET] = SAMPLER_TYPE_ID

        # Write name
        name_bytes = write_fixed_string(self.name, NAME_LENGTH)
        buffer[NAME_OFFSET:NAME_OFFSET + NAME_LENGTH] = name_bytes

        # Write transpose and eq combined
        buffer[TRANSPOSE_EQ_OFFSET] = (self.transpose & 0x0F) | ((self.eq & 0x0F) << 4)

        # Write other common parameters
        buffer[TABLE_TICK_OFFSET] = self.table_tick & 0xFF
        buffer[VOLUME_OFFSET] = self.volume & 0xFF
        buffer[PITCH_OFFSET] = self.pitch & 0xFF
        buffer[FINETUNE_OFFSET] = self.finetune & 0xFF

        # Write sampler-specific parameters
        buffer[SAMPLER_CONFIG["params"]["play_mode"]["offset"]] = self.params.play_mode & 0xFF
        buffer[SAMPLER_CONFIG["params"]["slice"]["offset"]] = self.params.slice & 0xFF

        # Write sample_path
        sample_path_config = SAMPLER_CONFIG["sample_path"]
        offset = sample_path_config["offset"]
        size = sample_path_config["size"]
        sample_path_bytes = write_fixed_string(self.params.sample_path, size)
        buffer[offset:offset + size] = sample_path_bytes

        return bytes(buffer)

    def is_empty(self):
        """Check if instrument is empty."""
        return self.type != SAMPLER_TYPE_ID

    def clone(self):
        """Create a copy of this instrument."""
        instance = M8Sampler(
            name=self.name,
            sample_path=self.params.sample_path,
            play_mode=self.params.play_mode,
            slice=self.params.slice,
            volume=self.volume,
            pitch=self.pitch,
            transpose=self.transpose,
            eq=self.eq,
            table_tick=self.table_tick,
            finetune=self.finetune
        )
        instance.version = self.version
        return instance

    def as_dict(self):
        """Convert to dictionary."""
        result = {
            "type": self.type,
            "name": self.name,
            "volume": self.volume,
            "pitch": self.pitch,
            "transpose": self.transpose,
            "eq": self.eq,
            "table_tick": self.table_tick,
            "finetune": self.finetune
        }

        # Add params
        params_dict = self.params.as_dict()
        result.update(params_dict)

        return result

    @classmethod
    def from_dict(cls, data):
        """Create instrument from dictionary."""
        return cls(
            name=data.get("name", ""),
            sample_path=data.get("sample_path", ""),
            play_mode=data.get("play_mode", 0),
            slice=data.get("slice", 0),
            volume=data.get("volume", 255),
            pitch=data.get("pitch", 64),
            transpose=data.get("transpose", 4),
            eq=data.get("eq", 1),
            table_tick=data.get("table_tick", 1),
            finetune=data.get("finetune", 128)
        )

    @classmethod
    def read(cls, data):
        """Read instrument from binary data."""
        instrument = cls()
        instrument._read_common_parameters(data)
        instrument.params.read(data)
        return instrument

    @classmethod
    def read_from_file(cls, file_path):
        """Read instrument from .m8i file."""
        with open(file_path, "rb") as f:
            data = f.read()

        # Read version
        version_offset = get_offset("version")
        version = M8Version.read(data[version_offset:])

        # Read instrument data
        metadata_offset = get_offset("metadata")
        instrument_data = data[metadata_offset:]

        instrument = cls.read(instrument_data)
        instrument.version = version

        return instrument

    def write_to_file(self, file_path):
        """Write instrument to .m8i file."""
        import os

        # Create directory if needed
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        instrument_data = self.write()

        # Get offsets
        version_offset = get_offset("version")
        metadata_offset = get_offset("metadata")

        # Create file buffer
        m8i_data = bytearray([0] * metadata_offset) + instrument_data

        # Write version
        version_data = self.version.write()
        m8i_data[version_offset:version_offset + len(version_data)] = version_data

        with open(file_path, "wb") as f:
            f.write(m8i_data)


# Legacy alias for backwards compatibility
M8Instrument = M8Sampler
