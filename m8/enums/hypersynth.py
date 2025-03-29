from enum import IntEnum

class M8HyperSynthFX(IntEnum):
    VOL = 0xA0  # Volume
    PIT = 0xA1  # Pitch
    FIN = 0xA2  # Fine tune
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
    CUTOFF = 0x08
    RES = 0x09
    AMP = 0x0A
    PAN = 0x0B
    MOD_AMT = 0x0C
    MOD_RATE = 0x0D
    MOD_BOTH = 0x0E