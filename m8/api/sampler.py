# m8/api/sampler.py
"""M8 Sampler instrument - the only instrument type supported."""

from m8.api import M8Block, _read_fixed_string, _write_fixed_string
from m8.api.version import M8Version

# Instruments configuration (from instruments.py to avoid circular import)
INSTRUMENTS_BLOCK_SIZE = 215
INSTRUMENTS_COUNT = 128

# Sampler configuration
SAMPLER_TYPE_ID = 2

# Common field offsets
TYPE_OFFSET = 0
NAME_OFFSET = 1
NAME_LENGTH = 12

# Sample path configuration
SAMPLE_PATH_OFFSET = 87
SAMPLE_PATH_SIZE = 128

# Block sizes and counts for samplers
BLOCK_SIZE = INSTRUMENTS_BLOCK_SIZE
BLOCK_COUNT = INSTRUMENTS_COUNT


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
