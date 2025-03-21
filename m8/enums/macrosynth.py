from enum import IntEnum

class M8MacroSynthFX(IntEnum):
    VOL = 0x80
    PIT = 0x81
    FIN = 0x82
    OSC = 0x83
    TBR = 0x84
    COL = 0x85
    DEG = 0x86
    RED = 0x87
    FIL = 0x88
    CUT = 0x89
    RES = 0x8a
    AMP = 0x8b
    LIM = 0x8c
    PAD = 0x8d
    TRG = 0xa6
    DRY = 0x8e
    SCH = 0x8f
    SDL = 0x90
    SRV = 0x91


class M8MacroSynthModDestinations(IntEnum):
    OFF = 0x00
    VOLUME = 0x01
    PITCH = 0x02
    TIMBRE = 0x03
    COLOR = 0x04
    DEGRADE = 0x05
    REDUX = 0x06
    CUTOFF = 0x07        # Renamed from FILTER_CUTOFF
    RES = 0x08           # Renamed from RESONANCE (previously FILTER_RESONANCE)
    AMP = 0x09           # Renamed from AMP_LEVEL
    PAN = 0x0A           # Renamed from MIXER_PAN
    MOD_AMP = 0x0B
    MOD_RATE = 0x0C
    MOD_BOTH = 0x0D
    MOD_BINV = 0x0E

class M8MacroSynthShapes(IntEnum):
    CSAW = 0x00
    MORPH = 0x01
    SAW_SQUARE = 0x02
    SINE_TRIANGLE = 0x03
    BUZZ = 0x04
    SQUARE_SUB = 0x05
    SAW_SUB = 0x06
    SQUARE_SYNC = 0x07
    SAW_SYNC = 0x08
    TRIPLE_SAW = 0x09
    TRIPLE_SQUARE = 0x0A
    TRIPLE_TRIANGLE = 0x0B
    TRIPLE_SIN = 0x0C
    TRIPLE_RNG = 0x0D
    SAW_SWARM = 0x0E
    SAW_COMB = 0x0F
    TOY = 0x10
    DIGITAL_FILTER_LP = 0x11
    DIGITAL_FILTER_PK = 0x12
    DIGITAL_FILTER_BP = 0x13
    DIGITAL_FILTER_HP = 0x14
    VOSIM = 0x15
    VOWEL = 0x16
    VOWEL_FOF = 0x17
    HARMONICS = 0x18
    FM = 0x19
    FEEDBACK_FM = 0x1A
    CHAOTIC_FEEDBACK_FM = 0x1B
    PLUCKED = 0x1C
    BOWED = 0x1D
    BLOWN = 0x1E
    FLUTED = 0x1F
    STRUCK_BELL = 0x20
    STRUCK_DRUM = 0x21
    KICK = 0x22
    CYMBAL = 0x23
    SNARE = 0x24
    WAVETABLES = 0x25
    WAVE_MAP = 0x26
    WAV_LINE = 0x27
    WAV_PARAPHONIC = 0x28
    FILTERED_NOISE = 0x29
    TWIN_PEAKS_NOISE = 0x2A
    CLOCKED_NOISE = 0x2B
    GRANULAR_CLOUD = 0x2C
    PARTICLE_NOISE = 0x2D
    DIGITAL_MOD = 0x2E
    MORSE_NOISE = 0x2F

