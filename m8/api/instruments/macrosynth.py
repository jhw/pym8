# m8/api/instruments/macrosynth.py
"""M8 MacroSynth instrument - Mutable Instruments Braids-based synthesizer."""

from enum import IntEnum
from m8.api import _read_fixed_string, _write_fixed_string
from m8.api.instrument import M8Instrument, BLOCK_SIZE, BLOCK_COUNT

# MacroSynth configuration
MACROSYNTH_TYPE_ID = 1


# MacroSynth Parameter Offsets
class M8MacrosynthParam(IntEnum):
    """Byte offsets for macrosynth instrument parameters."""
    # Common parameters
    TYPE = 0          # Instrument type (always 1 for macrosynth)
    NAME = 1          # Name starts at offset 1 (12 bytes)

    # Common synth parameters
    TRANSPOSE = 13    # Pitch transpose
    TABLE_TICK = 14   # Table tick rate
    VOLUME = 15       # Master volume
    PITCH = 16        # Pitch offset
    FINE_TUNE = 17    # Fine pitch adjustment (0x80 = center)

    # MacroSynth-specific parameters (come BEFORE filter/mixer)
    SHAPE = 18        # Oscillator shape (see M8MacroShape enum)
    TIMBRE = 19       # Timbre control (synthesis parameter 1)
    COLOUR = 20       # Colour control (synthesis parameter 2)
    DEGRADE = 21      # Bitcrusher/degradation amount
    REDUX = 22        # Sample rate reduction amount

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
class M8MacrosynthModDest(IntEnum):
    """Macrosynth modulator destination parameters."""
    OFF = 0x00       # No modulation
    VOLUME = 0x01    # Volume modulation
    PITCH = 0x02     # Pitch modulation
    TIMBRE = 0x03    # Timbre (synthesis parameter 1)
    COLOUR = 0x04    # Colour (synthesis parameter 2)
    DEGRADE = 0x05   # Bitcrusher amount
    REDUX = 0x06     # Sample rate reduction
    CUTOFF = 0x07    # Filter cutoff
    RES = 0x08       # Filter resonance
    AMP = 0x09       # Amplifier level
    PAN = 0x0A       # Stereo pan


# MacroSynth Oscillator Shapes (based on Mutable Instruments Braids)
class M8MacroShape(IntEnum):
    """MacroSynth oscillator shapes - 45 synthesis algorithms from Braids."""
    CSAW = 0          # CS80-like sawtooth with 'notch'
    MORPH = 1         # /\/|-_-_ - Variable wave morphing
    SAW_SQUARE = 2    # /|/|-_-_ - Sawtooth/square morphing
    FOLD = 3          # FOLD - Waveform folding
    SQUARE = 4        # _|_|_|_| - Dual square
    SYN_SAW = 5       # SYN-_-_ - Synced sawtooth
    SYN_SQUARE = 6    # SYN/| - Synced square
    SAW_SWARM = 7     # /|/|x3 - Triple saw
    SQUARE_SWARM = 8  # -_-_x3 - Triple square
    TRI_SWARM = 9     # /\x3 - Triple triangle
    SIN_SWARM = 10    # SIx3 - Triple sine
    RING = 11         # RING - Ring modulation
    SAW_STACK = 12    # /|/|/|/| - Supersaw
    SAW_WAVE = 13     # /|/|_|_|_ - Saw wave variation
    TOY = 14          # TOY* - Toy-like synthesis
    ZLPF = 15         # ZLPF - Zero-delay low-pass filtered noise
    ZPKF = 16         # ZPKF - Zero-delay peak filtered noise
    ZBPF = 17         # ZBPF - Zero-delay band-pass filtered noise
    ZHPF = 18         # ZHPF - Zero-delay high-pass filtered noise
    VOSM = 19         # VOSM - Vowel/speech synthesis (low-fi)
    VOWL = 20         # VOWL - Vowel synthesis
    VFOF = 21         # VFOF - Formant synthesis (FOF-like)
    HARM = 22         # HARM - Harmonic oscillator
    FM = 23           # FM - FM synthesis
    FBFM = 24         # FBFM - Feedback FM
    WTFM = 25         # WTFM - Wavetable FM
    PLUK = 26         # PLUK - Plucked string (Karplus-Strong)
    BOWD = 27         # BOWD - Bowed string
    BLOW = 28         # BLOW - Blown reed
    FLUT = 29         # FLUT - Flute
    BELL = 30         # BELL - Bell
    DRUM = 31         # DRUM - Metallic drum
    KICK = 32         # KICK - Kick drum
    CYMB = 33         # CYMB - Cymbal
    SNAR = 34         # SNAR - Snare drum
    WTBL = 35         # WTBL - Wavetable
    WMAP = 36         # WMAP - Wavetable map
    WLIN = 37         # WLIN - Linear wavetable interpolation
    WTX4 = 38         # WTX4 - Wavetable 4X
    NOIS = 39         # NOIS - Filtered noise
    TWNQ = 40         # TWNQ - Twin peaks filtered noise
    CLKN = 41         # CLKN - Clocked noise
    CLOU = 42         # CLOU - Granular cloud
    PRTC = 43         # PRTC - Particle noise
    QPSK = 44         # QPSK - Digital modulation


# Default parameter values (offset, value) pairs for non-zero defaults
DEFAULT_PARAMETERS = [
    (17, 0x80),  # FINE_TUNE, default: 128 (center)
    (19, 0x80),  # TIMBRE, default: 128 (center)
    (20, 0x80),  # COLOUR, default: 128 (center)
    (24, 0xFF),  # CUTOFF, default: 255 (fully open)
    (28, 0x80),  # PAN, default: 128 (center)
    (29, 0xC0),  # DRY, default: 192
]


class M8Macrosynth(M8Instrument):
    """M8 MacroSynth instrument - Mutable Instruments Braids-based synthesizer."""

    # Configuration for base class dict serialization
    PARAM_ENUM_CLASS = M8MacrosynthParam
    MOD_DEST_ENUM_CLASS = M8MacrosynthModDest
    PARAM_ENUM_TYPES = {
        'SHAPE': M8MacroShape,
        'FILTER_TYPE': None,  # Will be set below to avoid circular import
        'LIMIT': None,        # Will be set below to avoid circular import
    }

    def __init__(self, name=""):
        """Initialize a macrosynth instrument with default parameters."""
        super().__init__(MACROSYNTH_TYPE_ID)

        # Apply macrosynth-specific defaults
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
        """Export macrosynth parameters to a dictionary.

        Args:
            enum_mode: How to serialize enum values:
                      'value' (default) - use integer values
                      'name' - use enum names as strings (human-readable)

        Returns a dict with:
        - name: instrument name
        - params: dict of macrosynth parameters using M8MacrosynthParam names as keys
        - modulators: list of modulator parameter dicts
        """
        self._setup_enum_types()
        return super().to_dict(enum_mode=enum_mode)

    @classmethod
    def from_dict(cls, params):
        """Create a macrosynth from a parameter dictionary.

        Args:
            params: Dict with keys: name, params, modulators
                   - params is a dict with M8MacrosynthParam names as keys
                   - param values can be integers or enum names (strings)
                   - modulators is a list of modulator parameter dicts

        Returns:
            M8Macrosynth instance configured with given parameters
        """
        cls._setup_enum_types()
        return super(M8Macrosynth, cls).from_dict(params)

    @classmethod
    def read(cls, data):
        """Read instrument from binary data."""
        # Use base class read for common functionality
        instance = super(M8Macrosynth, cls).read(data)

        # Apply non-zero defaults for parameters that are zero
        for offset, default_value in DEFAULT_PARAMETERS:
            if instance._data[offset] == 0:
                instance._data[offset] = default_value

        return instance
