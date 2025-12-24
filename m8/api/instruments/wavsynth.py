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

    # Synth parameters (shared with other synths)
    TRANSPOSE = 13    # Pitch transpose
    TABLE_TICK = 14   # Table tick rate
    VOLUME = 15       # Master volume
    PITCH = 16        # Pitch offset
    FINE_TUNE = 17    # Fine pitch adjustment (0x80 = center)

    # Filter parameters
    FILTER_TYPE = 18  # Filter type selection
    CUTOFF = 19       # Filter cutoff frequency (0xFF = open)
    RESONANCE = 20    # Filter resonance

    # Mixer parameters
    AMP = 21          # Amplifier level
    LIMIT = 22        # Limiter amount
    PAN = 23          # Stereo pan (0x80 = center)
    DRY = 24          # Dry/wet mix level
    CHORUS_SEND = 25  # Send to chorus effect
    DELAY_SEND = 26   # Send to delay effect
    REVERB_SEND = 27  # Send to reverb effect

    # WavSynth-specific parameters
    SHAPE = 28        # Waveform shape (see M8WavShape enum)
    SIZE = 29         # Wavetable size
    MULT = 30         # Frequency multiplier
    WARP = 31         # Waveform warp amount
    MIRROR = 32       # Waveform mirror amount

    # Modulators start at offset 63


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
    (17, 0x80),  # FINETUNE, default: 128
    (19, 0xFF),  # CUTOFF, default: 255
    (23, 0x80),  # PAN, default: 128
    (24, 0xC0),  # DRY, default: 192
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
