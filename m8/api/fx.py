from enum import IntEnum

# FX configuration
FX_BLOCK_SIZE = 2
FX_BLOCK_COUNT = 3

# Field offsets within FX tuple
FX_KEY_OFFSET = 0
FX_VALUE_OFFSET = 1

# Constants
EMPTY_KEY = 255
DEFAULT_VALUE = 0

# Module-level constants
BLOCK_SIZE = FX_BLOCK_SIZE
BLOCK_COUNT = FX_BLOCK_COUNT


# Sequence FX Commands (Global, work with all instrument types)
class M8SequenceFX(IntEnum):
    """Global FX commands that affect playback behavior across all instruments."""
    ARP = 0x00  # Arpeggio
    CHA = 0x01  # Chance
    DEL = 0x02  # Delay
    GRV = 0x03  # Groove
    HOP = 0x04  # Jump to step
    KIL = 0x05  # Kill/stop note
    RND = 0x06  # Random
    RNL = 0x07  # Random limited
    RET = 0x08  # Retrigger
    REP = 0x09  # Repeat
    RMX = 0x0A  # Remix
    NTH = 0x0B  # N-th conditional
    PSL = 0x0C  # Pan slide left
    PBN = 0x0D  # Probability note
    PVB = 0x0E  # Pitch vibrato
    PVX = 0x0F  # Pitch vibrato extended
    SCA = 0x10  # Scale
    SCG = 0x11  # Scale global
    SED = 0x12  # Set delay
    SNG = 0x13  # Song
    TBL = 0x14  # Table
    THO = 0x15  # Tempo hop
    TIC = 0x16  # Tick
    TBX = 0x17  # Table extended
    TPO = 0x18  # Tempo
    TSP = 0x19  # Transpose
    OFF = 0x1A  # Note off


# Sampler FX Commands (Instrument-specific, sampler only)
class M8SamplerFX(IntEnum):
    """FX commands specific to sampler instruments."""
    VOL = 0x80  # Volume
    PIT = 0x81  # Pitch
    FIN = 0x82  # Fine tune
    PLY = 0x83  # Play mode (0x00=FWD, 0x01=REV)
    STA = 0x84  # Start position
    LOP = 0x85  # Loop start
    LEN = 0x86  # Length/cut
    DEG = 0x87  # Degrade
    FLT = 0x88  # Filter type
    CUT = 0x89  # Cutoff frequency
    RES = 0x8A  # Resonance
    AMP = 0x8B  # Amplifier
    LIM = 0x8C  # Limiter
    PAN = 0x8D  # Pan
    DRY = 0x8E  # Dry/wet mix
    SCH = 0x8F  # Send chorus (also SMX on V6.2)
    SDL = 0x90  # Send delay
    SRV = 0x91  # Send reverb
    SLI = 0xA6  # Slice
    ERR = 0xA7  # Sample error / debug


# HyperSynth FX Commands (firmware 6.0+ layout)
# Like every instrument-specific FX class, these share the 0x80-0xA7
# byte range with M8SamplerFX — the M8 firmware interprets the byte
# according to the playing instrument's type. The HyperSynth ordering
# is sourced from m8-file-parser/src/instruments/hypersynth.rs
# (HYPERSYNTH_COMMAND_NAMES_6 / _6_2). The crucial one is CRD (0x83),
# which selects one of the 16 rows in M8HyperSynth.chords mid-phrase —
# letting a single HyperSynth instrument play a sequence of different
# chord shapes from successive phrase steps.
class M8HypersynthFX(IntEnum):
    """FX commands specific to HyperSynth instruments (firmware 6.0+)."""
    VOL = 0x80  # Volume
    PIT = 0x81  # Pitch
    FIN = 0x82  # Fine tune
    CRD = 0x83  # Chord select — slot index into M8HyperSynth.chords
    CVO = 0x84  # Chord voice (per-oscillator on/off mask shortcut)
    SWM = 0x85  # Swarm
    WID = 0x86  # Width
    SUB = 0x87  # Sub-oscillator
    FLT = 0x88  # Filter type
    CUT = 0x89  # Cutoff frequency
    RES = 0x8A  # Resonance
    AMP = 0x8B  # Amplifier
    LIM = 0x8C  # Limiter
    PAN = 0x8D  # Pan
    DRY = 0x8E  # Dry/wet mix
    SCH = 0x8F  # Send chorus (= SMX on V6.2)
    SDL = 0x90  # Send delay
    SRV = 0x91  # Send reverb
    SNC = 0xA6  # Sync
    ERR = 0xA7  # Error / debug


# Modulator FX Commands (apply to all instrument types that have modulators)
# Five commands per modulator slot, four slots. Layout per slot:
#   AHD env:  EA, AT, HO, DE, ET
#   ADSR env: EA, AT, DE, SU, ET
#   LFO:      LA, LO, LS, LF, LT
# Byte codes are constant; mnemonics on the M8 display change with the
# modulator type at that slot. Enum names use the AHD layout as canonical.
class M8ModulatorFX(IntEnum):
    """FX commands that modify modulator (envelope/LFO) parameters.

    Naming follows the AHD-envelope convention; the same byte code displays
    as different mnemonics on the M8 depending on what modulator type
    occupies that slot:

    - AHD envelope:  EA{n} AT{n} HO{n} DE{n} ET{n}
    - ADSR envelope: EA{n} AT{n} DE{n} SU{n} ET{n}
    - LFO:           LA{n} LO{n} LS{n} LF{n} LT{n}
    """
    # Modulator slot 1 (mod_id 0)
    EA1 = 0x92  # Envelope/LFO amount
    AT1 = 0x93  # Attack (env) / oscillator (LFO)
    HO1 = 0x94  # Hold (AHD) / Decay (ADSR) / Shape (LFO)
    DE1 = 0x95  # Decay (AHD) / Sustain (ADSR) / Frequency (LFO)
    ET1 = 0x96  # Envelope target / LFO trigger

    # Modulator slot 2 (mod_id 1)
    EA2 = 0x97
    AT2 = 0x98
    HO2 = 0x99
    DE2 = 0x9A
    ET2 = 0x9B

    # Modulator slot 3 (mod_id 2)
    EA3 = 0x9C
    AT3 = 0x9D
    HO3 = 0x9E
    DE3 = 0x9F
    ET3 = 0xA0

    # Modulator slot 4 (mod_id 3)
    EA4 = 0xA1
    AT4 = 0xA2
    HO4 = 0xA3
    DE4 = 0xA4
    ET4 = 0xA5


# Mixer FX Commands (firmware 6.2, global - mixer/voice controls)
# Sequence FX occupy 0x00..0x1A; mixer FX start at 0x1B.
class M8MixerFX(IntEnum):
    """Mixer FX commands (M8 firmware 6.2)."""
    VMV = 0x1B  # Volume master volume
    XMM = 0x1C  # Chorus mod mix
    XMF = 0x1D  # Chorus mod feedback
    XMW = 0x1E  # Chorus mod width
    XMR = 0x1F  # Chorus mod rate
    XDT = 0x20  # Delay time
    XDF = 0x21  # Delay feedback
    XDW = 0x22  # Delay width
    XDR = 0x23  # Delay rate
    XRS = 0x24  # Reverb size
    XRD = 0x25  # Reverb damping
    XRM = 0x26  # Reverb mix
    XRF = 0x27  # Reverb filter
    XRW = 0x28  # Reverb width
    XRZ = 0x29  # Reverb resonance
    VMX = 0x2A  # Master mix
    VDE = 0x2B  # Voice delay send
    VRE = 0x2C  # Voice reverb send
    VT1 = 0x2D  # Track 1 volume
    VT2 = 0x2E  # Track 2 volume
    VT3 = 0x2F  # Track 3 volume
    VT4 = 0x30  # Track 4 volume
    VT5 = 0x31  # Track 5 volume
    VT6 = 0x32  # Track 6 volume
    VT7 = 0x33  # Track 7 volume
    VT8 = 0x34  # Track 8 volume
    DJC = 0x35  # DJ filter cutoff
    VIN = 0x36  # Input volume
    IMX = 0x37  # Input mix
    IDE = 0x38  # Input delay send
    IRE = 0x39  # Input reverb send
    VI2 = 0x3A  # Input 2 volume
    IM2 = 0x3B  # Input 2 mix
    ID2 = 0x3C  # Input 2 delay send
    IR2 = 0x3D  # Input 2 reverb send
    USB = 0x3E  # USB level
    DJR = 0x3F  # DJ filter resonance
    DJT = 0x40  # DJ filter type
    EQM = 0x41  # EQ mid
    EQI = 0x42  # EQ initialise
    INS = 0x43  # Instrument send
    RTO = 0x44  # Retrigger off
    ARC = 0x45  # Arc
    GGR = 0x46  # Global groove
    NXT = 0x47  # Next
    XRH = 0x48  # Reverb HP
    XMT = 0x49  # Chorus type
    OTT = 0x4A  # OTT amount
    OTC = 0x4B  # OTT compression
    OTI = 0x4C  # OTT input
    MTT = 0x4D  # Master tempo


class M8FXTuple:
    """Key-value pair for M8 effects with key (effect type) and value (effect parameter)."""

    def __init__(self, key=EMPTY_KEY, value=DEFAULT_VALUE):
        self._data = bytearray([0, 0])  # Initialize with zeros

        # Set values directly - clients should pass enum.value for enum keys
        self._data[FX_KEY_OFFSET] = key
        self._data[FX_VALUE_OFFSET] = value
    
    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)  # Create instance without calling __init__
        instance._data = bytearray(data[:BLOCK_SIZE])
        return instance
    
    def write(self):
        return bytes(self._data)
    
    @property
    def key(self):
        return self._data[FX_KEY_OFFSET]

    @key.setter
    def key(self, value):
        self._data[FX_KEY_OFFSET] = value

    @property
    def value(self):
        return self._data[FX_VALUE_OFFSET]

    @value.setter
    def value(self, value):
        self._data[FX_VALUE_OFFSET] = value
    
    def clone(self):
        """Create a copy of this FX tuple."""
        return self.__class__(
            key=self.key,
            value=self.value
        )


class M8FXTuples(list):
    """Collection of effect settings that can be applied to phrases, instruments, and chains."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize with empty FX tuples
        for _ in range(BLOCK_COUNT):
            self.append(M8FXTuple())
    
    @classmethod
    def read(cls, data):
        instance = cls.__new__(cls)  # Create instance without calling __init__
        list.__init__(instance)  # Initialize the list properly
        
        for i in range(BLOCK_COUNT):
            start = i * BLOCK_SIZE
            tuple_data = data[start:start + BLOCK_SIZE]
            instance.append(M8FXTuple.read(tuple_data))
        
        return instance
    
    def clone(self):
        instance = self.__class__()
        instance.clear()  # Remove default items
        
        for fx_tuple in self:
            if hasattr(fx_tuple, 'clone'):
                instance.append(fx_tuple.clone())
            else:
                cloned_tuple = M8FXTuple.read(fx_tuple.write())
                instance.append(cloned_tuple)
        
        return instance
    
    def write(self):
        result = bytearray()
        for fx_tuple in self:
            tuple_data = fx_tuple.write()
            result.extend(tuple_data)
        return bytes(result)