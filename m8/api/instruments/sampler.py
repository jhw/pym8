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

    def to_dict(self):
        """Export sampler parameters to a dictionary.

        Returns a dict with:
        - name: instrument name
        - sample_path: path to sample file
        - params: dict of sampler parameters using M8SamplerParam names as keys
        - modulators: list of modulator parameter dicts
        """
        result = {
            'name': self.name,
            'sample_path': self.sample_path,
            'params': {},
            'modulators': self.modulators.to_dict()
        }

        # Export all sampler parameters (excluding TYPE and NAME which are handled separately)
        for param in M8SamplerParam:
            if param != M8SamplerParam.TYPE and param != M8SamplerParam.NAME:
                result['params'][param.name] = self.get(param)

        return result

    @classmethod
    def from_dict(cls, params):
        """Create a sampler from a parameter dictionary.

        Args:
            params: Dict with keys: name, sample_path, params, modulators
                   - params is a dict with M8SamplerParam names as keys
                   - modulators is a list of modulator parameter dicts

        Returns:
            M8Sampler instance configured with given parameters
        """
        # Create instance with name and sample_path
        name = params.get('name', '')
        sample_path = params.get('sample_path', '')
        instance = cls(name=name, sample_path=sample_path)

        # Apply parameter overrides
        sampler_params = params.get('params', {})
        for param_name, value in sampler_params.items():
            try:
                param_offset = M8SamplerParam[param_name]
                instance.set(param_offset, value)
            except KeyError:
                # Skip unknown parameter names
                pass

        # Apply modulator configuration
        modulators_list = params.get('modulators')
        if modulators_list:
            from m8.api.modulator import M8Modulators
            instance.modulators = M8Modulators.from_dict(modulators_list)

        return instance

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
