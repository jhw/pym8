from enum import IntEnum

class M8InstrumentTypes(IntEnum):
    MACROSYNTH = 0x01

class M8ModTypes(IntEnum):
    AHD = 0x00
    ADSR = 0x01
    LFO = 0x03
    
class M8FilterTypes(IntEnum):
    OFF = 0x00
    LOWPASS = 0x01
    HIGHPASS = 0x02
    BANDPASS = 0x03
    BANDSTOP = 0x04
    LP_TO_HP = 0x05
    ZDF_LP = 0x06
    ZDF_HP = 0x07

class M8AmpLimitTypes(IntEnum):
    CLIP = 0x00
    SIN = 0x01
    FOLD = 0x02
    WRAP = 0x03
    POST = 0x04
    POSTAD = 0x05
    POST_W1 = 0x06
    POST_W2 = 0x07
