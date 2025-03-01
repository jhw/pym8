from enum import IntEnum

class M8ModDestinations(IntEnum):
    """Generic modulation destinations that can be used across instruments."""
    NONE = 0x0
    VOLUME = 0x1
    PITCH = 0x2
    FILTER_CUTOFF = 0x3
    FILTER_RESONANCE = 0x4
    AMP_LEVEL = 0x5
    AMP_PAN = 0x6
    FX_AMOUNT = 0x7
    
    # MacroSynth specific destinations
    TIMBRE = 0x8
    COLOR = 0x9
    DEGRADE = 0xA
    REDUX = 0xB
    
    # Can add more instrument-specific destinations as needed


class M8LFOShapes(IntEnum):
    """LFO shape types."""
    TRIANGLE = 0x0
    SINE = 0x1
    SQUARE = 0x2
    SAW = 0x3
    EXPONENTIAL = 0x4
    RANDOM = 0x5


class M8LFOTriggerModes(IntEnum):
    """LFO trigger modes."""
    FREE = 0x0
    RETRIG = 0x1
    HOLD = 0x2
    ONE_SHOT = 0x3
