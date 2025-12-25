# m8/api/instruments/wavsynth.py
"""M8 WavSynth instrument - wavetable synthesizer."""

from enum import IntEnum
from m8.api import _read_fixed_string, _write_fixed_string
from m8.api.instrument import M8Instrument, BLOCK_SIZE, BLOCK_COUNT

# WavSynth configuration
WAVSYNTH_TYPE_ID = 0


# WavSynth Parameter Offsets
class M8WavsynthParam(IntEnum):
    """Byte offsets for wavsynth instrument parameters."""
    # Common parameters
    TYPE = 0          # Instrument type (always 0 for wavsynth)
    NAME = 1          # Name starts at offset 1 (12 bytes)

    # Common synth parameters
    TRANSPOSE = 13    # Pitch transpose
    TABLE_TICK = 14   # Table tick rate
    VOLUME = 15       # Master volume
    PITCH = 16        # Pitch offset
    FINE_TUNE = 17    # Fine pitch adjustment (0x80 = center)

    # WavSynth-specific parameters (come BEFORE filter/mixer)
    SHAPE = 18        # Waveform shape (see M8WavShape enum)
    SIZE = 19         # Wavetable size
    MULT = 20         # Frequency multiplier
    WARP = 21         # Waveform warp amount
    MIRROR = 22       # Waveform mirror amount (scan in M8 UI)

    # Filter parameters
    FILTER_TYPE = 23  # Filter type selection
    CUTOFF = 24       # Filter cutoff frequency (0xFF = open)
    RESONANCE = 25    # Filter resonance

    # Mixer parameters
    AMP = 26          # Amplifier level
    LIMIT = 27        # Limiter amount
    PAN = 28          # Stereo pan (0x80 = center)
    DRY = 29          # Dry/wet mix level
    CHORUS_SEND = 30  # Send to chorus effect (mixer_mfx in M8)
    DELAY_SEND = 31   # Send to delay effect
    REVERB_SEND = 32  # Send to reverb effect

    # Modulators start at offset 63


# Modulator Destination Values
class M8WavsynthModDest(IntEnum):
    """Wavsynth modulator destination parameters."""
    OFF = 0x00       # No modulation
    VOLUME = 0x01    # Volume modulation
    PITCH = 0x02     # Pitch modulation
    SIZE = 0x03      # Wavetable size
    MULT = 0x04      # Frequency multiplier
    WARP = 0x05      # Waveform warp
    MIRROR = 0x06    # Waveform mirror (scan)
    CUTOFF = 0x07    # Filter cutoff
    RES = 0x08       # Filter resonance
    AMP = 0x09       # Amplifier level
    PAN = 0x0A       # Stereo pan


# WavSynth Wave Shapes
class M8WavShape(IntEnum):
    """WavSynth waveform shapes."""
    # Basic waveforms
    PULSE12 = 0
    PULSE25 = 1
    PULSE50 = 2
    PULSE75 = 3
    SAW = 4
    TRIANGLE = 5
    SINE = 6
    NOISE_PITCHED = 7
    NOISE = 8

    # Wavetable variants
    WT_CRUSH = 9
    WT_FOLDING = 10
    WT_FREQ = 11
    WT_FUZZY = 12
    WT_GHOST = 13
    WT_GRAPHIC = 14
    WT_LFOPLAY = 15
    WT_LIQUID = 16
    WT_MORPHING = 17
    WT_MYSTIC = 18
    WT_STICKY = 19
    WT_TIDAL = 20
    WT_TIDY = 21
    WT_TUBE = 22
    WT_UMBRELLA = 23
    WT_UNWIND = 24
    WT_VIRAL = 25
    WT_WAVES = 26
    WT_DRIP = 27
    WT_FROGGY = 28
    WT_INSONIC = 29
    WT_RADIUS = 30
    WT_SCRATCH = 31
    WT_SMOOTH = 32
    WT_WOBBLE = 33
    WT_ASIMMTRY = 34
    WT_BLEEN = 35
    WT_FRACTAL = 36
    WT_GENTLE = 37
    WT_HARMONIC = 38
    WT_HYPNOTIC = 39
    WT_ITERATIV = 40
    WT_MICROWAV = 41
    WT_PLAITS01 = 42
    WT_PLAITS02 = 43
    WT_RISEFALL = 44
    WT_TONAL = 45
    WT_TWINE = 46
    WT_ALIEN = 47
    WT_CYBERNET = 48
    WT_DISORDR = 49
    WT_FORMANT = 50
    WT_HYPER = 51
    WT_JAGGED = 52
    WT_MIXED = 53
    WT_MULTIPLY = 54
    WT_NOWHERE = 55
    WT_PINBALL = 56
    WT_RINGS = 57
    WT_SHIMMER = 58
    WT_SPECTRAL = 59
    WT_SPOOKY = 60
    WT_TRANSFRM = 61
    WT_TWISTED = 62
    WT_VOCAL = 63
    WT_WASHED = 64
    WT_WONDER = 65
    WT_WOWEE = 66
    WT_ZAP = 67
    WT_BRAIDS = 68
    WT_VOXSYNTH = 69


# Default parameter values (offset, value) pairs for non-zero defaults
DEFAULT_PARAMETERS = [
    (17, 0x80),  # FINE_TUNE, default: 128 (center)
    (19, 0x20),  # SIZE, default: 32
    (24, 0xFF),  # CUTOFF, default: 255 (fully open)
    (28, 0x80),  # PAN, default: 128 (center)
    (29, 0xC0),  # DRY, default: 192
]


class M8Wavsynth(M8Instrument):
    """M8 WavSynth instrument - wavetable synthesizer."""

    # Configuration for base class dict serialization
    PARAM_ENUM_CLASS = M8WavsynthParam
    PARAM_ENUM_TYPES = {
        'SHAPE': M8WavShape,
        'FILTER_TYPE': None,  # Will be set below to avoid circular import
        'LIMIT': None,        # Will be set below to avoid circular import
    }

    def __init__(self, name=""):
        """Initialize a wavsynth instrument with default parameters."""
        super().__init__(WAVSYNTH_TYPE_ID)

        # Apply wavsynth-specific defaults
        self._apply_defaults(DEFAULT_PARAMETERS)

        # Set name if provided
        if name:
            self.name = name

    @classmethod
    def _setup_enum_types(cls):
        """Setup enum types (called lazily to avoid circular imports)."""
        if cls.PARAM_ENUM_TYPES['FILTER_TYPE'] is None:
            from m8.api.instrument import M8FilterType, M8LimiterType
            cls.PARAM_ENUM_TYPES['FILTER_TYPE'] = M8FilterType
            cls.PARAM_ENUM_TYPES['LIMIT'] = M8LimiterType

    def to_dict(self, enum_mode='value'):
        """Export wavsynth parameters to a dictionary.

        Args:
            enum_mode: How to serialize enum values:
                      'value' (default) - use integer values
                      'name' - use enum names as strings (human-readable)

        Returns a dict with:
        - name: instrument name
        - params: dict of wavsynth parameters using M8WavsynthParam names as keys
        - modulators: list of modulator parameter dicts
        """
        self._setup_enum_types()
        return super().to_dict(enum_mode=enum_mode)

    @classmethod
    def from_dict(cls, params):
        """Create a wavsynth from a parameter dictionary.

        Args:
            params: Dict with keys: name, params, modulators
                   - params is a dict with M8WavsynthParam names as keys
                   - param values can be integers or enum names (strings)
                   - modulators is a list of modulator parameter dicts

        Returns:
            M8Wavsynth instance configured with given parameters
        """
        cls._setup_enum_types()
        return super(M8Wavsynth, cls).from_dict(params)

    @classmethod
    def read(cls, data):
        """Read instrument from binary data."""
        # Use base class read for common functionality
        instance = super(M8Wavsynth, cls).read(data)

        # Apply non-zero defaults for parameters that are zero
        for offset, default_value in DEFAULT_PARAMETERS:
            if instance._data[offset] == 0:
                instance._data[offset] = default_value

        return instance
