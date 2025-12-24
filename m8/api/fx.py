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
    SCH = 0x8F  # Send chorus
    SDL = 0x90  # Send delay
    SRV = 0x91  # Send reverb
    SLI = 0xA6  # Slice

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