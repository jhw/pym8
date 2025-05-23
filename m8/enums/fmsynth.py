from enum import IntEnum

class M8FMSynthAlgos(IntEnum):
    A_B_C_D = 0x00               # "A>B>C>D"
    A_PLUS_B_C_D = 0x01          # "[A+B]>C>D"
    A_B_PLUS_C_D = 0x02          # "[A>B+C]>D"
    A_B_PLUS_A_C_D = 0x03        # "[A>B+A>C]>D"
    A_PLUS_B_PLUS_C_D = 0x04     # "[A+B+C]>D"
    A_B_C_PLUS_D = 0x05          # "[A>B>C]+D"
    A_B_C_PLUS_A_B_D = 0x06      # "[A>B>C]+[A>B>D]"
    A_B_PLUS_C_D_1 = 0x07        # "[A>B]+[C>D]"
    A_B_PLUS_A_C_PLUS_A_D = 0x08 # "[A>B]+[A>C]+[A>D]"
    A_B_PLUS_A_C_PLUS_D = 0x09   # "[A>B]+[A>C]+D"
    A_B_PLUS_C_PLUS_D = 0x0A     # "[A>B]+C+D"
    A_PLUS_B_PLUS_C_PLUS_D = 0x0B # "A+B+C+D"

class M8FMSynthFX(IntEnum):
    VOL = 0x80
    PIT = 0x81
    FIN = 0x82
    ALG = 0x83
    FM1 = 0x84
    FM2 = 0x85
    FM3 = 0x86
    FM4 = 0x87
    FLT = 0x88
    CUT = 0x89
    RES = 0x8A
    AMP = 0x8B
    LIM = 0x8C
    PAN = 0x8D
    DRY = 0x8E
    SCH = 0x8F
    SDL = 0x90
    SRV = 0x91
    FMP = 0x92

class M8FMSynthModDestinations(IntEnum):
    OFF = 0x00
    VOLUME = 0x01
    PITCH = 0x02
    MOD1 = 0x03
    MOD2 = 0x04
    MOD3 = 0x05
    MOD4 = 0x06
    CUTOFF = 0x07
    RES = 0x08
    AMP = 0x09
    PAN = 0x0A
    MOD_AMT = 0x0B
    MOD_RATE = 0x0C
    MOD_BOTH = 0x0D
    MOD_BINV = 0x0E
    
class M8FMSynthModABValues(IntEnum):
    LEV1 = 0x01
    LEV2 = 0x02
    LEV3 = 0x03
    LEV4 = 0x04
    RAT1 = 0x05
    RAT2 = 0x06
    RAT3 = 0x07
    RAT4 = 0x08
    PIT1 = 0x09
    PIT2 = 0x0A
    PIT3 = 0x0B
    PIT4 = 0x0C
    FBK1 = 0x0D
    FBK2 = 0x0E
    FBK3 = 0x0F
    FBK4 = 0x10

class M8FMSynthShapes(IntEnum):
    SIN = 0x00
    SW2 = 0x01
    SW3 = 0x02
    SW4 = 0x03
    SW5 = 0x04
    SW6 = 0x05
    TRI = 0x06
    SAW = 0x07
    SQR = 0x08
    PUL = 0x09
    IMP = 0x0A
    NOI = 0x0B
    NLP = 0x0C
    NHP = 0x0D
    NBP = 0x0E
    CLK = 0x0F
    # v4.1 additions
    W09 = 0x10
    W0A = 0x11
    W0B = 0x12
    W0C = 0x13
    W0D = 0x14
    W0E = 0x15
    W0F = 0x16
    W10 = 0x17
    W11 = 0x18
    W12 = 0x19
    W13 = 0x1A
    W14 = 0x1B
    W15 = 0x1C
    W16 = 0x1D
    W17 = 0x1E
    W18 = 0x1F
    W19 = 0x20
    W1A = 0x21
    W1B = 0x22
    W1C = 0x23
    W1D = 0x24
    W1E = 0x25
    W1F = 0x26
    W20 = 0x27
    W21 = 0x28
    W22 = 0x29
    W23 = 0x2A
    W24 = 0x2B
    W25 = 0x2C
    W26 = 0x2D
    W27 = 0x2E
    W28 = 0x2F
    W29 = 0x30
    W2A = 0x31
    W2B = 0x32
    W2C = 0x33
    W2D = 0x34
    W2E = 0x35
    W2F = 0x36
    W30 = 0x37
    W31 = 0x38
    W32 = 0x39
    W33 = 0x3A
    W34 = 0x3B
    W35 = 0x3C
    W36 = 0x3D
    W37 = 0x3E
    W38 = 0x3F
    W39 = 0x40
    W3A = 0x41
    W3B = 0x42
    W3C = 0x43
    W3D = 0x44
    W3E = 0x45
    W3F = 0x46
    W40 = 0x47
    W41 = 0x48
    W42 = 0x49
    W43 = 0x4A
    W44 = 0x4B
    W45 = 0x4C