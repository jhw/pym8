# m8/api/sampler.py
"""M8 Sampler instrument - the only instrument type supported."""

from enum import IntEnum
from m8.api import _read_fixed_string, _write_fixed_string
from m8.api.instrument import M8Instrument, M8InstrumentType, BLOCK_SIZE, BLOCK_COUNT


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
    REPITCH = 0x09   # Repitch
    REP_REV = 0x0A   # Repitch reverse
    REP_PP = 0x0B    # Repitch ping-pong
    REP_BPM = 0x0C   # Repitch BPM sync
    BPM_REV = 0x0D   # BPM sync reverse
    BPM_PP = 0x0E    # BPM sync ping-pong


# Modulator Destination Values
class M8SamplerModDest(IntEnum):
    """Sampler modulator destination parameters."""
    OFF = 0x00       # No modulation
    VOLUME = 0x01    # Volume modulation
    PITCH = 0x02     # Pitch modulation
    LOOP_ST = 0x03   # Loop start position
    LENGTH = 0x04    # Sample length
    DEGRADE = 0x05   # Bitcrusher amount
    CUTOFF = 0x06    # Filter cutoff
    RES = 0x07       # Filter resonance
    AMP = 0x08       # Amplifier level
    PAN = 0x09       # Stereo pan

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

    # Configuration for base class dict serialization
    PARAM_ENUM_CLASS = M8SamplerParam
    MOD_DEST_ENUM_CLASS = M8SamplerModDest
    PARAM_ENUM_TYPES = {
        'PLAY_MODE': M8PlayMode,
        'FILTER_TYPE': None,  # Will be set below to avoid circular import
        'LIMIT': None,        # Will be set below to avoid circular import
    }

    def __init__(self, name="", sample_path=""):
        """Initialize a sampler instrument with default parameters."""
        # Initialize base instrument
        super().__init__(M8InstrumentType.SAMPLER)

        # Apply sampler-specific defaults
        self._apply_defaults(DEFAULT_PARAMETERS)

        # Set name and sample path if provided
        if name:
            self.name = name
        if sample_path:
            self.sample_path = sample_path

    @classmethod
    def _setup_enum_types(cls):
        """Setup enum types (called lazily to avoid circular imports)."""
        if cls.PARAM_ENUM_TYPES['FILTER_TYPE'] is None:
            from m8.api.instrument import M8FilterType, M8LimiterType
            cls.PARAM_ENUM_TYPES['FILTER_TYPE'] = M8FilterType
            cls.PARAM_ENUM_TYPES['LIMIT'] = M8LimiterType

    @property
    def sample_path(self):
        """Get sample path."""
        return _read_fixed_string(self._data, SAMPLE_PATH_OFFSET, SAMPLE_PATH_SIZE)

    @sample_path.setter
    def sample_path(self, value):
        """Set sample path."""
        path_bytes = _write_fixed_string(value, SAMPLE_PATH_SIZE)
        self._data[SAMPLE_PATH_OFFSET:SAMPLE_PATH_OFFSET + SAMPLE_PATH_SIZE] = path_bytes

    def _get_extra_dict_fields(self):
        """Get extra fields for dict export (sample_path)."""
        return {'sample_path': self.sample_path}

    def _set_extra_dict_fields(self, fields):
        """Set extra fields from dict import (sample_path)."""
        if 'sample_path' in fields:
            self.sample_path = fields['sample_path']

    @classmethod
    def _create_from_dict(cls, params):
        """Create instance for from_dict with sample_path."""
        return cls(
            name=params.get('name', ''),
            sample_path=params.get('sample_path', '')
        )

    def to_dict(self, enum_mode='value'):
        """Export sampler parameters to a dictionary.

        Args:
            enum_mode: How to serialize enum values:
                      'value' (default) - use integer values
                      'name' - use enum names as strings (human-readable)

        Returns a dict with:
        - name: instrument name
        - sample_path: path to sample file
        - params: dict of sampler parameters using M8SamplerParam names as keys
        - modulators: list of modulator parameter dicts
        """
        self._setup_enum_types()
        return super().to_dict(enum_mode=enum_mode)

    @classmethod
    def from_dict(cls, params):
        """Create a sampler from a parameter dictionary.

        Args:
            params: Dict with keys: name, sample_path, params, modulators
                   - params is a dict with M8SamplerParam names as keys
                   - param values can be integers or enum names (strings)
                   - modulators is a list of modulator parameter dicts

        Returns:
            M8Sampler instance configured with given parameters
        """
        cls._setup_enum_types()
        return super(M8Sampler, cls).from_dict(params)

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
