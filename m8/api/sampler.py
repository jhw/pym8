# m8/api/sampler.py
"""M8 Sampler instrument - the only instrument type supported."""

from m8.api import M8Block, _read_fixed_string, _write_fixed_string
from m8.api.version import M8Version
from m8.core.format import load_format_config, get_offset

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

# Sample path configuration
SAMPLE_PATH_OFFSET = SAMPLER_CONFIG["sample_path"]["offset"]
SAMPLE_PATH_SIZE = SAMPLER_CONFIG["sample_path"]["size"]


class M8Sampler:
    """M8 Sampler instrument - the only instrument type supported."""

    def __init__(self, name="", sample_path=""):
        """Initialize a sampler instrument with default parameters."""
        # Type is always SAMPLER
        self.type = SAMPLER_TYPE_ID

        # Version (set from project or file)
        self.version = M8Version()

        # Common parameters (only name is supported)
        self.name = name

        # Sampler-specific parameter
        self.sample_path = sample_path

    def write(self):
        """Convert instrument to binary data."""
        buffer = bytearray([0] * BLOCK_SIZE)

        # Write type
        buffer[TYPE_OFFSET] = SAMPLER_TYPE_ID

        # Write name
        name_bytes = _write_fixed_string(self.name, NAME_LENGTH)
        buffer[NAME_OFFSET:NAME_OFFSET + NAME_LENGTH] = name_bytes

        # Write common parameters with config defaults
        buffer[common_fields["table_tick"]["offset"]] = common_fields["table_tick"]["default"] & 0xFF
        buffer[common_fields["finetune"]["offset"]] = common_fields["finetune"]["default"] & 0xFF

        # Write sample_path
        sample_path_bytes = _write_fixed_string(self.sample_path, SAMPLE_PATH_SIZE)
        buffer[SAMPLE_PATH_OFFSET:SAMPLE_PATH_OFFSET + SAMPLE_PATH_SIZE] = sample_path_bytes

        return bytes(buffer)

    def clone(self):
        """Create a copy of this instrument."""
        instance = M8Sampler(
            name=self.name,
            sample_path=self.sample_path
        )
        instance.version = self.version
        return instance

    @classmethod
    def read(cls, data):
        """Read instrument from binary data."""
        instrument = cls()
        instrument.type = data[TYPE_OFFSET]
        instrument.name = _read_fixed_string(data, NAME_OFFSET, NAME_LENGTH)
        instrument.sample_path = _read_fixed_string(data, SAMPLE_PATH_OFFSET, SAMPLE_PATH_SIZE)
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
