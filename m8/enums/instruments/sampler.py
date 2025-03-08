from enum import IntEnum

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

