from enum import IntEnum

def generate_notes_enum():
    # Define all notes without the # symbol
    raw_note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    enum_names = ['C', 'C_SHARP', 'D', 'D_SHARP', 'E', 'F', 'F_SHARP', 'G', 'G_SHARP', 'A', 'A_SHARP', 'B']
    
    enum_values = {}
    note_value = 0
    
    # Generate note values starting with C_1 (0x00)
    for octave in range(1, 10):  # From octave 1 to 9
        for i, enum_name in enumerate(enum_names):
            # Create the enum key with octave
            key = f"{enum_name}_{octave}"
            enum_values[key] = note_value
            note_value += 1
            
            # Stop at G_9 if that's the highest note
            if octave == 9 and enum_name == 'G':
                break
    
    return IntEnum('M8Notes', enum_values)

# Create the notes enum
M8Notes = generate_notes_enum()

class M8InstrumentType(IntEnum):
    # Instrument types in the M8 tracker.
    # 
    # This enum is the single source of truth for instrument type IDs and is used
    # to generate the instrument type mappings used throughout the codebase.
    # Instrument types in the M8 tracker.
    # 
    # This enum is the single source of truth for instrument type IDs and is used
    # to generate the instrument type mappings used throughout the codebase.
    WAVSYNTH = 0x00
    MACROSYNTH = 0x01
    SAMPLER = 0x02
    FMSYNTH = 0x04
    HYPERSYNTH = 0x05
    
    @classmethod
    def from_id(cls, type_id):
        """Get the enum value from a numeric type ID."""
        try:
            return cls(type_id)
        except ValueError:
            return None

class M8ModulatorType(IntEnum):
    # Modulator types in the M8 tracker.
    # 
    # This enum is the single source of truth for modulator type IDs and is used
    # to generate the modulator type mappings used throughout the codebase.
    AHD_ENVELOPE = 0x00
    ADSR_ENVELOPE = 0x01
    DRUM_ENVELOPE = 0x02
    LFO = 0x03
    TRIGGER_ENVELOPE = 0x04
    TRACKING_ENVELOPE = 0x05
    
    @classmethod
    def from_id(cls, type_id):
        """Get the enum value from a numeric type ID."""
        try:
            return cls(type_id)
        except ValueError:
            return None

class M8SequencerFX(IntEnum):
    ARP = 0x0
    ARC = 0x45
    CHA = 0x1
    DEL = 0x2
    GRV = 0x3
    HOP = 0x4
    RND = 0x6
    RNL = 0x7
    RET = 0x8
    REP = 0x9
    RTO = 0x44
    NTH = 0xb
    PSL = 0xc
    PBN = 0xd
    PVB = 0xe
    PVX = 0xf
    SCA = 0x10
    SCG = 0x11
    SED = 0x12
    SNG = 0x13
    TBL = 0x14
    THO = 0x15
    TIC = 0x16
    TBX = 0x17
    TPO = 0x18
    TSP = 0x19
    GGR = 0x46
    RMX = 0xa
    INS = 0x43
    KIL = 0x5
    OFF = 0x1a

class M8MixerFX(IntEnum):
    VMV = 0x1b
    VCH = 0x2a
    VDE = 0x2b
    VRE = 0x2c
    VIN = 0x36
    USB = 0x3e
    EQI = 0x42
    EQM = 0x41
    VT1 = 0x2d
    VT2 = 0x2e
    VT3 = 0x2f
    VT4 = 0x30
    VT5 = 0x31
    VT6 = 0x32
    VT7 = 0x33
    VT8 = 0x34
    XCM = 0x1c
    XCF = 0x1d
    XCW = 0x1e
    XCR = 0x1f
    XDT = 0x20
    XDF = 0x21
    XDW = 0x22
    XDR = 0x23
    XRS = 0x24
    XRD = 0x25
    XRM = 0x26
    XRF = 0x27
    XRW = 0x28
    XRZ = 0x29
    ICH = 0x37
    IDE = 0x38
    IRE = 0x39
    VI2 = 0x3a
    IC2 = 0x3b
    ID2 = 0x3c
    IR2 = 0x3d
    DJC = 0x35
    DJR = 0x3f
    DJT = 0x40

class M8ModulatorFX(IntEnum):
    EA1 = 0x92
    AT1 = 0x93
    HO1 = 0x94
    DE1 = 0x95
    ET1 = 0x96
    EA2 = 0x97
    AT2 = 0x98
    HO2 = 0x99
    DE2 = 0x9A
    ET2 = 0x9B
    LA3 = 0x9C
    LO3 = 0x9D
    LS3 = 0x9E
    LF3 = 0x9F
    LT3 = 0xA0
    LA4 = 0xA1
    LO4 = 0xA2
    LS4 = 0xA3
    LF4 = 0xA4
    LT4 = 0xA5

class M8FilterTypes(IntEnum):
    OFF = 0x00
    LOWPASS = 0x01
    HIGHPASS = 0x02
    BANDPASS = 0x03
    BANDSTOP = 0x04
    LP_TO_HP = 0x05
    ZDF_LP = 0x06
    ZDF_HP = 0x07

class M8LimitTypes(IntEnum):
    CLIP = 0x00
    SIN = 0x01
    FOLD = 0x02
    WRAP = 0x03
    POST = 0x04
    POSTAD = 0x05
    POST_W1 = 0x06
    POST_W2 = 0x07
