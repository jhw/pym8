# m8/api/sampler.py
"""M8 Sampler instrument - the only instrument type supported."""

from m8.api import M8Block, _read_fixed_string, _write_fixed_string
from m8.api.version import M8Version
from m8.api.modulator import M8Modulators

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

# Modulators offset (from v0.3.1 config)
MODULATORS_OFFSET = 63

# Default parameter values (offset, value) pairs for non-zero defaults
DEFAULT_PARAMETERS = [
    (17, 0x80),  # FINETUNE, default: 128
    (22, 0xFF),  # LENGTH, default: 255
    (25, 0xFF),  # CUTOFF, default: 255
    (29, 0x80),  # PAN, default: 128
    (30, 0xC0),  # DRY, default: 192
]

# Block sizes and counts for samplers
BLOCK_SIZE = INSTRUMENTS_BLOCK_SIZE
BLOCK_COUNT = INSTRUMENTS_COUNT


class M8Sampler:
    """M8 Sampler instrument - the only instrument type supported."""

    def __init__(self, name="", sample_path=""):
        """Initialize a sampler instrument with default parameters."""
        # Initialize buffer with zeros
        self._data = bytearray([0] * BLOCK_SIZE)

        # Set type
        self._data[TYPE_OFFSET] = SAMPLER_TYPE_ID

        # Set non-zero defaults
        for offset, value in DEFAULT_PARAMETERS:
            self._data[offset] = value

        # Version (set from project or file)
        self.version = M8Version()

        # Set name and sample path if provided
        if name:
            self.name = name
        if sample_path:
            self.sample_path = sample_path

        # Initialize modulators (4 modulators: 2 AHD, 2 LFO)
        self.modulators = M8Modulators()

    def get(self, offset):
        """Get parameter value at offset."""
        return self._data[offset]

    def set(self, offset, value):
        """Set parameter value at offset."""
        self._data[offset] = value & 0xFF

    @property
    def name(self):
        """Get instrument name."""
        return _read_fixed_string(self._data, NAME_OFFSET, NAME_LENGTH)

    @name.setter
    def name(self, value):
        """Set instrument name."""
        name_bytes = _write_fixed_string(value, NAME_LENGTH)
        self._data[NAME_OFFSET:NAME_OFFSET + NAME_LENGTH] = name_bytes

    @property
    def sample_path(self):
        """Get sample path."""
        return _read_fixed_string(self._data, SAMPLE_PATH_OFFSET, SAMPLE_PATH_SIZE)

    @sample_path.setter
    def sample_path(self, value):
        """Set sample path."""
        path_bytes = _write_fixed_string(value, SAMPLE_PATH_SIZE)
        self._data[SAMPLE_PATH_OFFSET:SAMPLE_PATH_OFFSET + SAMPLE_PATH_SIZE] = path_bytes

    def write(self):
        """Convert instrument to binary data."""
        buffer = bytearray(self._data)

        # Write modulators at offset 63
        modulator_data = self.modulators.write()
        buffer[MODULATORS_OFFSET:MODULATORS_OFFSET + len(modulator_data)] = modulator_data

        return bytes(buffer)

    def clone(self):
        """Create a copy of this instrument."""
        instance = M8Sampler.__new__(M8Sampler)
        instance._data = bytearray(self._data)
        instance.version = self.version
        instance.modulators = self.modulators.clone()
        return instance

    @classmethod
    def read(cls, data):
        """Read instrument from binary data."""
        instance = cls.__new__(cls)
        instance._data = bytearray(data[:BLOCK_SIZE])
        instance.version = M8Version()

        # Apply non-zero defaults for parameters that are zero
        for offset, default_value in DEFAULT_PARAMETERS:
            if instance._data[offset] == 0:
                instance._data[offset] = default_value

        # Read modulators from offset 63
        instance.modulators = M8Modulators.read(data[MODULATORS_OFFSET:])

        return instance
