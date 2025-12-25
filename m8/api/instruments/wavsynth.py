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

    def __init__(self, name=""):
        """Initialize a wavsynth instrument with default parameters."""
        super().__init__(WAVSYNTH_TYPE_ID)

        # Apply wavsynth-specific defaults
        self._apply_defaults(DEFAULT_PARAMETERS)

        # Set name if provided
        if name:
            self.name = name

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
        result = {
            'name': self.name,
            'params': {},
            'modulators': self.modulators.to_dict(enum_mode=enum_mode)
        }

        # Mapping of parameters to their enum types (for human-readable mode)
        from m8.api.instrument import M8FilterType, M8LimiterType
        param_enum_types = {
            'SHAPE': M8WavShape,
            'FILTER_TYPE': M8FilterType,
            'LIMIT': M8LimiterType,
        }

        # Export all wavsynth parameters (excluding TYPE and NAME which are handled separately)
        for param in M8WavsynthParam:
            if param != M8WavsynthParam.TYPE and param != M8WavsynthParam.NAME:
                value = self.get(param)

                # Convert enum values to names if requested
                if enum_mode == 'name' and param.name in param_enum_types:
                    try:
                        enum_type = param_enum_types[param.name]
                        value = enum_type(value).name
                    except (ValueError, KeyError):
                        # If value doesn't map to enum, keep as integer
                        pass

                result['params'][param.name] = value

        return result

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
        # Create instance with name
        name = params.get('name', '')
        instance = cls(name=name)

        # Mapping of parameters to their enum types
        from m8.api.instrument import M8FilterType, M8LimiterType
        param_enum_types = {
            'SHAPE': M8WavShape,
            'FILTER_TYPE': M8FilterType,
            'LIMIT': M8LimiterType,
        }

        # Apply parameter overrides
        wavsynth_params = params.get('params', {})
        for param_name, value in wavsynth_params.items():
            try:
                param_offset = M8WavsynthParam[param_name]

                # Handle string enum names
                if isinstance(value, str) and param_name in param_enum_types:
                    try:
                        enum_type = param_enum_types[param_name]
                        value = enum_type[value].value
                    except KeyError:
                        # Unknown enum name, skip
                        continue

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
        instance = super(M8Wavsynth, cls).read(data)

        # Apply non-zero defaults for parameters that are zero
        for offset, default_value in DEFAULT_PARAMETERS:
            if instance._data[offset] == 0:
                instance._data[offset] = default_value

        return instance
