from enum import IntEnum

class M8FXEnum(IntEnum):
    """
    Enumeration of FX commands for Dirtywave M8 format v4.0.1.
    
    Commands are divided into two categories:
    1. Sequencer commands (0x00-0x1A)
    2. Mixer/FX commands (0x1B-0x46)
    """
    # Sequencer commands (from SEQ_COMMAND_V3)
    ARP = 0x00  # Arpeggio
    CHA = 0x01  # Chain
    DEL = 0x02  # Delay
    GRV = 0x03  # Groove
    HOP = 0x04  # Hop
    KIL = 0x05  # Kill
    RND = 0x06  # Random
    RNL = 0x07  # Random level
    RET = 0x08  # Retrigger
    REP = 0x09  # Repeat
    RMX = 0x0A  # Remix
    NTH = 0x0B  # Nth
    PSL = 0x0C  # Phrase scale
    PBN = 0x0D  # Phrase bank
    PVB = 0x0E  # Phrase vibrato
    PVX = 0x0F  # Phrase vibrato shape
    SCA = 0x10  # Scale
    SCG = 0x11  # Scale key
    SED = 0x12  # Seed
    SNG = 0x13  # Song
    TBL = 0x14  # Table
    THO = 0x15  # Threshold
    TIC = 0x16  # Tick
    TBX = 0x17  # Table index
    TPO = 0x18  # Tempo
    TSP = 0x19  # Transpose
    OFF = 0x1A  # Off
    
    # Mixer/FX commands (from FX_MIXER_COMMAND_V4)
    VMV = 0x1B  # Volume master
    XCM = 0x1C  # Chorus mix
    XCF = 0x1D  # Chorus feedback
    XCW = 0x1E  # Chorus width
    XCR = 0x1F  # Chorus reverb
    XDT = 0x20  # Delay time
    XDF = 0x21  # Delay feedback
    XDW = 0x22  # Delay width
    XDR = 0x23  # Delay reverb
    XRS = 0x24  # Reverb size
    XRD = 0x25  # Reverb damping
    XRM = 0x26  # Reverb mod depth
    XRF = 0x27  # Reverb mod freq
    XRW = 0x28  # Reverb width
    XRZ = 0x29  # Reverb freeze
    VCH = 0x2A  # Volume chorus
    VDE = 0x2B  # Volume delay
    VRE = 0x2C  # Volume reverb
    VT1 = 0x2D  # Volume track 1
    VT2 = 0x2E  # Volume track 2
    VT3 = 0x2F  # Volume track 3
    VT4 = 0x30  # Volume track 4
    VT5 = 0x31  # Volume track 5
    VT6 = 0x32  # Volume track 6
    VT7 = 0x33  # Volume track 7
    VT8 = 0x34  # Volume track 8
    DJC = 0x35  # DJ filter cutoff
    VIN = 0x36  # Volume input
    ICH = 0x37  # Input chorus
    IDE = 0x38  # Input delay
    IRE = 0x39  # Input reverb
    VI2 = 0x3A  # Volume input 2
    IC2 = 0x3B  # Input 2 chorus
    ID2 = 0x3C  # Input 2 delay
    IR2 = 0x3D  # Input 2 reverb
    USB = 0x3E  # USB
    DJR = 0x3F  # DJ filter resonance
    DJT = 0x40  # DJ filter type
    EQM = 0x41  # EQ mode
    EQI = 0x42  # EQ input
    INS = 0x43  # Insert
    RTO = 0x44  # Retrigger offset
    ARC = 0x45  # Arpeggio chance
    GGR = 0x46  # Groove grid
    
    
