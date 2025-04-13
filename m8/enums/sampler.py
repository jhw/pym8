from enum import IntEnum

class M8SamplerFX(IntEnum):
    VOL = 0x80
    PIT = 0x81
    FIN = 0x82
    PLY = 0x83
    STA = 0x84
    LOP = 0x85
    LEN = 0x86
    DEG = 0x87
    FIL = 0x88
    CUT = 0x89
    RES = 0x8A
    AMP = 0x8B
    LIM = 0x8C
    PAN = 0x8D
    DRY = 0x8E
    SCH = 0x8F
    SDL = 0x90
    SRV = 0x91
    SLI = 0xA6  # Extra command for slice

class M8SamplerPlayMode(IntEnum):
    FWD = 0x00
    REV = 0x01
    FWDLOOP = 0x02
    REVLOOP = 0x03
    FWD_PP = 0x04
    REV_PP = 0x05
    OSC = 0x06
    OSC_REV = 0x07
    OSC_PP = 0x08

class M8SamplerModDestinations(IntEnum):
    OFF = 0x00
    VOLUME = 0x01
    PITCH = 0x02
    LOOP_START = 0x03
    LENGTH = 0x04
    DEGRADE = 0x05
    CUTOFF = 0x06
    RES = 0x07
    AMP = 0x08
    PAN = 0x09
    MOD_AMT = 0x0A
    MOD_RATE = 0x0B
    MOD_BOTH = 0x0C
    MOD_BINV = 0x0D

