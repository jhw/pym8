# m8/api/instruments/fmsynth.py
"""M8 FM Synth instrument - 4-operator frequency modulation synthesizer."""

from enum import IntEnum
from m8.api import _read_fixed_string, _write_fixed_string
from m8.api.instrument import M8Instrument, BLOCK_SIZE, BLOCK_COUNT

# FM Synth configuration
FMSYNTH_TYPE_ID = 4


# FM Synth Parameter Offsets
class M8FMSynthParam(IntEnum):
    """Byte offsets for FM synth instrument parameters."""
    # Common parameters
    TYPE = 0          # Instrument type (always 4 for FM synth)
    NAME = 1          # Name starts at offset 1 (12 bytes)

    # Common synth parameters
    TRANSPOSE = 13    # Pitch transpose
    TABLE_TICK = 14   # Table tick rate
    VOLUME = 15       # Master volume
    PITCH = 16        # Pitch offset
    FINE_TUNE = 17    # Fine pitch adjustment (0x80 = center)

    # FM algorithm
    ALGO = 18         # FM algorithm (see M8FMAlgo enum)

    # Operator parameters (grouped by type, not by operator)
    # 4 operators: A, B, C, D
    OP_A_SHAPE = 19   # Operator A waveform shape (M8FMWave)
    OP_B_SHAPE = 20   # Operator B waveform shape
    OP_C_SHAPE = 21   # Operator C waveform shape
    OP_D_SHAPE = 22   # Operator D waveform shape

    # Interleaved operator data (need more reverse engineering)
    # Ratios appear at even offsets: 0x18, 0x1A, 0x1C, 0x1E
    OP_A_RATIO = 24   # Operator A frequency ratio (0-255 = 0.00-25.5x)
    OP_B_RATIO = 26   # Operator B frequency ratio
    OP_C_RATIO = 28   # Operator C frequency ratio
    OP_D_RATIO = 30   # Operator D frequency ratio

    # Level and feedback (interleaved)
    OP_A_LEVEL = 31   # Operator A output level
    OP_A_FEEDBACK = 32  # Operator A feedback amount
    OP_B_LEVEL = 33   # Operator B output level
    OP_B_FEEDBACK = 34  # Operator B feedback amount
    OP_C_LEVEL = 35   # Operator C output level
    OP_C_FEEDBACK = 36  # Operator C feedback amount
    OP_D_LEVEL = 37   # Operator D output level
    OP_D_FEEDBACK = 38  # Operator D feedback amount

    # Modulator values (0x2F-0x32)
    MOD1_VALUE = 47   # Modulator 1 amount
    MOD2_VALUE = 48   # Modulator 2 amount
    MOD3_VALUE = 49   # Modulator 3 amount
    MOD4_VALUE = 50   # Modulator 4 amount

    # Filter parameters
    FILTER_TYPE = 51  # Filter type selection
    CUTOFF = 52       # Filter cutoff frequency (0xFF = open)
    RESONANCE = 53    # Filter resonance

    # Mixer parameters
    AMP = 54          # Amplifier level
    LIMIT = 55        # Limiter amount
    PAN = 56          # Stereo pan (0x80 = center)
    DRY = 57          # Dry/wet mix level
    CHORUS_SEND = 58  # Send to chorus effect (mixer_mfx in M8)
    DELAY_SEND = 59   # Send to delay effect
    REVERB_SEND = 60  # Send to reverb effect

    # Modulators start at offset 61 (0x3D)


# FM Algorithm Enum (0x00-0x0B)
class M8FMAlgo(IntEnum):
    """FM synthesis algorithms - operator routing configurations.

    Based on m8-file-parser FM_ALGO_STRINGS array.
    """
    A_B_C_D = 0          # A>B>C>D - Linear cascade
    AB_C_D = 1           # [A+B]>C>D - Parallel A+B into cascade
    AB_C_D_ALT = 2       # [A>B+C]>D - Mixed modulation
    A_BC_D = 3           # [A>B+A>C]>D - A modulates both B and C
    ABC_D = 4            # [A+B+C]>D - Three parallel modulators
    A_B_C_D_PARALLEL = 5 # [A>B>C]+D - Cascade plus parallel D
    A_B_C_A_B_D = 6      # [A>B>C]+[A>B>D] - Two cascades sharing A>B
    A_B_C_D_TWO_PAIR = 7 # [A>B]+[C>D] - Two independent pairs
    A_B_A_C_A_D = 8      # [A>B]+[A>C]+[A>D] - A modulates B, C, and D
    A_B_A_C_D = 9        # [A>B]+[A>C]+D - A modulates B and C, D separate
    A_B_C_D_THREE = 10   # [A>B]+C+D - One modulation pair plus two carriers
    A_PLUS_B_PLUS_C_PLUS_D = 11  # A+B+C+D - Four parallel carriers


# FM Wave Shapes (Operator Waveforms)
class M8FMWave(IntEnum):
    """FM operator waveform shapes.

    Based on m8-file-parser FMWave enum.
    """
    # Basic waveforms (0x00-0x0F)
    SIN = 0      # Sine wave
    SW2 = 1      # Half sine
    SW3 = 2      # Third sine
    SW4 = 3      # Quarter sine
    SW5 = 4      # Fifth sine
    SW6 = 5      # Sixth sine
    TRI = 6      # Triangle
    SAW = 7      # Sawtooth
    SQR = 8      # Square
    PUL = 9      # Pulse
    IMP = 10     # Impulse
    NOI = 11     # Noise
    NLP = 12     # Noise lowpass
    NHP = 13     # Noise highpass
    NBP = 14     # Noise bandpass
    CLK = 15     # Clock

    # Additional waveforms (0x10-0x45)
    W09 = 16
    W0A = 17
    W0B = 18
    W0C = 19
    W0D = 20
    W0E = 21
    W0F = 22
    W10 = 23
    W11 = 24
    W12 = 25
    W13 = 26
    W14 = 27
    W15 = 28
    W16 = 29
    W17 = 30
    W18 = 31
    W19 = 32
    W1A = 33
    W1B = 34
    W1C = 35
    W1D = 36
    W1E = 37
    W1F = 38
    W20 = 39
    W21 = 40
    W22 = 41
    W23 = 42
    W24 = 43
    W25 = 44
    W26 = 45
    W27 = 46
    W28 = 47
    W29 = 48
    W2A = 49
    W2B = 50
    W2C = 51
    W2D = 52
    W2E = 53
    W2F = 54
    W30 = 55
    W31 = 56
    W32 = 57
    W33 = 58
    W34 = 59
    W35 = 60
    W36 = 61
    W37 = 62
    W38 = 63
    W39 = 64
    W3A = 65
    W3B = 66
    W3C = 67
    W3D = 68
    W3E = 69
    W3F = 70
    W40 = 71
    W41 = 72
    W42 = 73
    W43 = 74
    W44 = 75
    W45 = 76


# Modulator Destination Values
class M8FMSynthModDest(IntEnum):
    """FM synth modulator destination parameters.

    Based on m8-js and m8-file-parser DESTINATIONS array.
    """
    OFF = 0x00       # No modulation
    VOLUME = 0x01    # Volume modulation
    PITCH = 0x02     # Pitch modulation
    MOD1 = 0x03      # Modulator 1 amount
    MOD2 = 0x04      # Modulator 2 amount
    MOD3 = 0x05      # Modulator 3 amount
    MOD4 = 0x06      # Modulator 4 amount
    CUTOFF = 0x07    # Filter cutoff
    RES = 0x08       # Filter resonance
    AMP = 0x09       # Amplifier level
    PAN = 0x0A       # Stereo pan
    MOD_AMT = 0x0B   # Modulator amount
    MOD_RATE = 0x0C  # Modulator rate
    MOD_BOTH = 0x0D  # Modulator both (amount and rate)
    MOD_BINV = 0x0E  # Modulator bipolar inversion


# Default parameter values (offset, value) pairs for non-zero defaults
DEFAULT_PARAMETERS = [
    (17, 0x80),  # FINE_TUNE, default: 128 (center)
    (52, 0xFF),  # CUTOFF, default: 255 (fully open)
    (56, 0x80),  # PAN, default: 128 (center)
    (57, 0xC0),  # DRY, default: 192
]


class M8FMSynth(M8Instrument):
    """M8 FM Synth instrument - 4-operator frequency modulation synthesizer."""

    # Configuration for base class dict serialization
    PARAM_ENUM_CLASS = M8FMSynthParam
    MOD_DEST_ENUM_CLASS = M8FMSynthModDest
    PARAM_ENUM_TYPES = {
        'ALGO': M8FMAlgo,
        'OP_A_SHAPE': M8FMWave,
        'OP_B_SHAPE': M8FMWave,
        'OP_C_SHAPE': M8FMWave,
        'OP_D_SHAPE': M8FMWave,
        'FILTER_TYPE': None,  # Will be set below to avoid circular import
        'LIMIT': None,        # Will be set below to avoid circular import
    }

    def __init__(self, name=""):
        """Initialize an FM synth instrument with default parameters."""
        super().__init__(FMSYNTH_TYPE_ID)

        # Apply FM synth-specific defaults
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
        """Export FM synth parameters to a dictionary.

        Args:
            enum_mode: How to serialize enum values:
                      'value' (default) - use integer values
                      'name' - use enum names as strings (human-readable)

        Returns a dict with:
        - name: instrument name
        - params: dict of FM synth parameters using M8FMSynthParam names as keys
        - modulators: list of modulator parameter dicts
        """
        self._setup_enum_types()
        return super().to_dict(enum_mode=enum_mode)

    @classmethod
    def from_dict(cls, params):
        """Create an FM synth from a parameter dictionary.

        Args:
            params: Dict with keys: name, params, modulators
                   - params is a dict with M8FMSynthParam names as keys
                   - param values can be integers or enum names (strings)
                   - modulators is a list of modulator parameter dicts

        Returns:
            M8FMSynth instance configured with given parameters
        """
        cls._setup_enum_types()
        return super(M8FMSynth, cls).from_dict(params)

    @classmethod
    def read(cls, data):
        """Read instrument from binary data."""
        # Use base class read for common functionality
        instance = super(M8FMSynth, cls).read(data)

        # Apply non-zero defaults for parameters that are zero
        for offset, default_value in DEFAULT_PARAMETERS:
            if instance._data[offset] == 0:
                instance._data[offset] = default_value

        return instance
