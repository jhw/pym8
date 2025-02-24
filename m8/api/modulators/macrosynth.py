from m8 import NULL
from m8.api import BLANK
from m8.core.object import m8_object_class

M8MacroSynthAHDEnvelope = m8_object_class(
    field_map=[
        ("type|destination", 0x00, 0, 1, "UINT4_2"),
        ("amount", BLANK, 1, 2, "UINT8"),
        ("attack", NULL, 2, 3, "UINT8"),
        ("hold", NULL, 3, 4, "UINT8"),
        ("decay", 0x80, 4, 5, "UINT8")
    ]
)

M8MacroSynthADSREnvelope = m8_object_class(
    field_map=[
        ("type|destination", 0x10, 0, 1, "UINT4_2"),
        ("amount", BLANK, 1, 2, "UINT8"),
        ("attack", NULL, 2, 3, "UINT8"),
        ("decay", 0x80, 3, 4, "UINT8"),
        ("sustain", 0x80, 4, 5, "UINT8"),
        ("release", 0x80, 5, 6, "UINT8")
    ]
)

M8MacroSynthLFO = m8_object_class(
    field_map=[
        ("type|destination", 0x30, 0, 1, "UINT4_2"), 
        ("amount", BLANK, 1, 2, "UINT8"),
        ("shape", NULL, 2, 3, "UINT8"),
        ("trigger", NULL, 3, 4, "UINT8"),
        ("freq", 0x10, 4, 5, "UINT8"),
        ("retrigger", NULL, 5, 6, "UINT8")
    ]
)

