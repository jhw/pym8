# m8/api/instruments/external.py
"""M8 External instrument - MIDI output to external hardware."""

from enum import IntEnum
from m8.api import _read_fixed_string, _write_fixed_string
from m8.api.instrument import M8Instrument, M8InstrumentType, BLOCK_SIZE, BLOCK_COUNT


# External Instrument Parameter Offsets
class M8ExternalParam(IntEnum):
    """Byte offsets for external instrument parameters."""
    # Common parameters
    TYPE = 0          # Instrument type (always 6 for external)
    NAME = 1          # Name starts at offset 1 (12 bytes)

    # Common synth parameters
    TRANSPOSE = 13    # Pitch transpose (bool-like: 0 or 1)
    TABLE_TICK = 14   # Table tick rate
    VOLUME = 15       # Master volume
    PITCH = 16        # Pitch offset
    FINE_TUNE = 17    # Fine pitch adjustment (0x80 = center)

    # External-specific MIDI parameters
    INPUT = 18        # MIDI input source
    PORT = 19         # MIDI port selection
    CHANNEL = 20      # MIDI channel (0-15)
    BANK = 21         # Bank select (0-127)
    PROGRAM = 22      # Program/patch number (0-127)

    # Control Change mappings (4 CC slots)
    CCA_NUM = 23      # CC A controller number (0-127)
    CCA_VAL = 24      # CC A value (0-127)
    CCB_NUM = 25      # CC B controller number (0-127)
    CCB_VAL = 26      # CC B value (0-127)
    CCC_NUM = 27      # CC C controller number (0-127)
    CCC_VAL = 28      # CC C value (0-127)
    CCD_NUM = 29      # CC D controller number (0-127)
    CCD_VAL = 30      # CC D value (0-127)

    # Filter parameters
    FILTER_TYPE = 31  # Filter type selection
    CUTOFF = 32       # Filter cutoff frequency (0xFF = open)
    RESONANCE = 33    # Filter resonance

    # Mixer parameters
    AMP = 34          # Amplifier level
    LIMIT = 35        # Limiter amount
    PAN = 36          # Stereo pan (0x80 = center)
    DRY = 37          # Dry/wet mix level
    CHORUS_SEND = 38  # Send to chorus effect (mixer_mfx in M8)
    DELAY_SEND = 39   # Send to delay effect
    REVERB_SEND = 40  # Send to reverb effect

    # Modulators start at offset 63


# Audio Input Source Values
class M8ExternalInput(IntEnum):
    """External instrument audio input source."""
    OFF = 0x00        # No input
    LINE_IN_L = 0x01  # Line In Left
    LINE_IN_R = 0x02  # Line In Right
    LINE_IN_LR = 0x03 # Line In Left+Right


# MIDI Port Values
class M8ExternalPort(IntEnum):
    """External instrument MIDI output port."""
    DISABLED = 0x00   # No output
    USB = 0x01        # USB MIDI output
    MIDI = 0x02       # Hardware MIDI output
    USB_MIDI = 0x03   # Both USB and hardware MIDI output


# Modulator Destination Values
class M8ExternalModDest(IntEnum):
    """External instrument modulator destination parameters.

    Based on m8-file-parser EXTERNAL_INST_DESTINATIONS array.
    """
    OFF = 0x00       # No modulation
    VOLUME = 0x01    # Volume modulation
    CUTOFF = 0x02    # Filter cutoff
    RES = 0x03       # Filter resonance
    AMP = 0x04       # Amplifier level
    PAN = 0x05       # Stereo pan
    CCA = 0x06       # CC A value
    CCB = 0x07       # CC B value
    CCC = 0x08       # CC C value
    CCD = 0x09       # CC D value
    MOD_AMT = 0x0A   # Modulator amount
    MOD_RATE = 0x0B  # Modulator rate
    MOD_BOTH = 0x0C  # Modulator both (amount and rate)
    MOD_BINV = 0x0D  # Modulator bipolar inversion


# Default parameter values (offset, value) pairs for non-zero defaults
DEFAULT_PARAMETERS = [
    (17, 0x80),  # FINE_TUNE, default: 128 (center)
    (32, 0xFF),  # CUTOFF, default: 255 (fully open)
    (36, 0x80),  # PAN, default: 128 (center)
    (37, 0xC0),  # DRY, default: 192
]


class M8External(M8Instrument):
    """M8 External instrument - MIDI output to external hardware."""

    # Configuration for base class dict serialization
    PARAM_ENUM_CLASS = M8ExternalParam
    MOD_DEST_ENUM_CLASS = M8ExternalModDest
    PARAM_ENUM_TYPES = {
        'INPUT': M8ExternalInput,
        'PORT': M8ExternalPort,
        'FILTER_TYPE': None,  # Will be set below to avoid circular import
        'LIMIT': None,        # Will be set below to avoid circular import
    }

    def __init__(self, name=""):
        """Initialize an external instrument with default parameters."""
        super().__init__(M8InstrumentType.EXTERNAL)

        # Apply external-specific defaults
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
        """Export external instrument parameters to a dictionary.

        Args:
            enum_mode: How to serialize enum values:
                      'value' (default) - use integer values
                      'name' - use enum names as strings (human-readable)

        Returns a dict with:
        - name: instrument name
        - params: dict of external parameters using M8ExternalParam names as keys
        - modulators: list of modulator parameter dicts
        """
        self._setup_enum_types()
        return super().to_dict(enum_mode=enum_mode)

    @classmethod
    def from_dict(cls, params):
        """Create an external instrument from a parameter dictionary.

        Args:
            params: Dict with keys: name, params, modulators
                   - params is a dict with M8ExternalParam names as keys
                   - param values can be integers or enum names (strings)
                   - modulators is a list of modulator parameter dicts

        Returns:
            M8External instance configured with given parameters
        """
        cls._setup_enum_types()
        return super(M8External, cls).from_dict(params)

    @classmethod
    def read(cls, data):
        """Read instrument from binary data."""
        # Use base class read for common functionality
        instance = super(M8External, cls).read(data)

        # Apply non-zero defaults for parameters that are zero
        for offset, default_value in DEFAULT_PARAMETERS:
            if instance._data[offset] == 0:
                instance._data[offset] = default_value

        return instance
