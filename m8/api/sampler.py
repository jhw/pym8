# m8/api/sampler.py
"""M8 Sampler instrument - the only instrument type supported."""

from m8.api import _read_fixed_string, _write_fixed_string
from m8.api.instrument import M8Instrument, BLOCK_SIZE, BLOCK_COUNT

# Sampler configuration
SAMPLER_TYPE_ID = 2

# Sample path configuration
SAMPLE_PATH_OFFSET = 87
SAMPLE_PATH_SIZE = 128

# Default parameter values (offset, value) pairs for non-zero defaults
DEFAULT_PARAMETERS = [
    (17, 0x80),  # FINETUNE, default: 128
    (22, 0xFF),  # LENGTH, default: 255
    (25, 0xFF),  # CUTOFF, default: 255
    (29, 0x80),  # PAN, default: 128
    (30, 0xC0),  # DRY, default: 192
]


class M8Sampler(M8Instrument):
    """M8 Sampler instrument - the only instrument type supported."""

    def __init__(self, name="", sample_path=""):
        """Initialize a sampler instrument with default parameters."""
        # Initialize base instrument
        super().__init__(SAMPLER_TYPE_ID)

        # Set non-zero defaults
        for offset, value in DEFAULT_PARAMETERS:
            self._data[offset] = value

        # Set name and sample path if provided
        if name:
            self.name = name
        if sample_path:
            self.sample_path = sample_path

    @property
    def sample_path(self):
        """Get sample path."""
        return _read_fixed_string(self._data, SAMPLE_PATH_OFFSET, SAMPLE_PATH_SIZE)

    @sample_path.setter
    def sample_path(self, value):
        """Set sample path."""
        path_bytes = _write_fixed_string(value, SAMPLE_PATH_SIZE)
        self._data[SAMPLE_PATH_OFFSET:SAMPLE_PATH_OFFSET + SAMPLE_PATH_SIZE] = path_bytes

    @classmethod
    def read(cls, data):
        """Read instrument from binary data."""
        # Use base class read for common functionality
        instance = super(M8Sampler, cls).read(data)

        # Apply non-zero defaults for parameters that are zero
        for offset, default_value in DEFAULT_PARAMETERS:
            if instance._data[offset] == 0:
                instance._data[offset] = default_value

        return instance
