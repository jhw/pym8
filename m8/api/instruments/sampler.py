# m8/api/sampler.py
"""M8 Sampler instrument - the only instrument type supported."""

from enum import IntEnum
from m8.api import _read_fixed_string, _write_fixed_string
from m8.api.instrument import M8Instrument, BLOCK_SIZE, BLOCK_COUNT

# Sampler configuration
SAMPLER_TYPE_ID = 2


# Sampler Parameter Offsets
class M8SamplerParam(IntEnum):
    """Byte offsets for sampler instrument parameters."""
    # Common parameters
    TYPE = 0          # Instrument type (always 2 for sampler)
    NAME = 1          # Name starts at offset 1 (12 bytes)

    # Playback parameters
    TRANSPOSE = 13    # Pitch transpose
    TABLE_TICK = 14   # Table tick rate
    VOLUME = 15       # Master volume
    PITCH = 16        # Pitch offset
    FINE_TUNE = 17    # Fine pitch adjustment (0x80 = center)
    PLAY_MODE = 18    # Sample playback mode
    SLICE = 19        # Slice selection
    START = 20        # Sample start position
    LOOP_START = 21   # Loop start position
    LENGTH = 22       # Sample length (0xFF = full)
    DEGRADE = 23      # Bitcrusher amount

    # Filter parameters
    FILTER_TYPE = 24  # Filter type selection
    CUTOFF = 25       # Filter cutoff frequency (0xFF = open)
    RESONANCE = 26    # Filter resonance

    # Mixer parameters
    AMP = 27          # Amplifier level
    LIMIT = 28        # Limiter amount
    PAN = 29          # Stereo pan (0x80 = center)
    DRY = 30          # Dry/wet mix level
    CHORUS_SEND = 31  # Send to chorus effect
    DELAY_SEND = 32   # Send to delay effect
    REVERB_SEND = 33  # Send to reverb effect

    # Modulators start at offset 63


# Play Mode Values
class M8PlayMode(IntEnum):
    """Sample playback modes."""
    FWD = 0x00       # Forward
    REV = 0x01       # Reverse
    FWDLOOP = 0x02   # Forward loop
    REVLOOP = 0x03   # Reverse loop
    FWD_PP = 0x04    # Forward ping-pong
    REV_PP = 0x05    # Reverse ping-pong
    OSC = 0x06       # Oscillator
    OSC_REV = 0x07   # Oscillator reverse
    OSC_PP = 0x08    # Oscillator ping-pong

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

        # Apply sampler-specific defaults
        self._apply_defaults(DEFAULT_PARAMETERS)

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
