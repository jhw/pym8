from enum import IntEnum

class M8HyperSynthShapes(IntEnum):
    SIN = 0x00
    SAW = 0x01
    SQR = 0x02
    TRI = 0x03
    PULSE = 0x04
    NOISE = 0x05
    WAVETABLE = 0x06
    FORMANT = 0x07
    HARMONIC = 0x08

class M8HyperSynthFX(IntEnum):
    VOL = 0xA0  # Volume
    PIT = 0xA1  # Pitch
    FIN = 0xA2  # Fine tune
    SHP = 0xA3  # Shape
    HRM = 0xA4  # Harmonics
    MIX = 0xA5  # Mix
    MOR = 0xA6  # Morph
    SPR = 0xA7  # Spread
    FLT = 0xA8  # Filter type
    CUT = 0xA9  # Cutoff
    RES = 0xAA  # Resonance
    AMP = 0xAB  # Amp
    LIM = 0xAC  # Limit
    PAN = 0xAD  # Pan
    DRY = 0xAE  # Dry
    SCH = 0xAF  # Chorus send
    SDL = 0xB0  # Delay send
    SRV = 0xB1  # Reverb send

class M8HyperSynthModDestinations(IntEnum):
    OFF = 0x00
    VOLUME = 0x01
    PITCH = 0x02
    SHAPE = 0x03
    HARMONICS = 0x04
    MIX = 0x05
    MORPH = 0x06
    SPREAD = 0x07
    CUTOFF = 0x08
    RES = 0x09
    AMP = 0x0A
    PAN = 0x0B
    MOD_AMT = 0x0C
    MOD_RATE = 0x0D
    MOD_BOTH = 0x0E