from m8 import M8Block, NULL, BLANK
from m8.core.list import m8_list_class
from m8.core.object import m8_object_class
from m8.utils.bits import split_byte

import struct

BLOCK_SIZE = 6
BLOCK_COUNT = 4

M8AHDEnvelope = m8_object_class(
    field_map=[
        ("type|destination", 0x00, 0, 1, "UINT4_2"),  # type in upper nibble, destination in lower
        ("amount", BLANK, 1, 2, "UINT8"),
        ("attack", NULL, 2, 3, "UINT8"),
        ("hold", NULL, 3, 4, "UINT8"),
        ("decay", 0x80, 4, 5, "UINT8")
    ]
)

M8ADSREnvelope = m8_object_class(
    field_map=[
        ("type|destination", 0x10, 0, 1, "UINT4_2"),  # type in upper nibble, destination in lower
        ("amount", BLANK, 1, 2, "UINT8"),
        ("attack", NULL, 2, 3, "UINT8"),
        ("decay", 0x80, 3, 4, "UINT8"),
        ("sustain", 0x80, 4, 5, "UINT8"),
        ("release", 0x80, 5, 6, "UINT8")
    ]
)

M8LFO = m8_object_class(
    field_map=[
        ("type|destination", 0x30, 0, 1, "UINT4_2"), 
        ("amount", BLANK, 1, 2, "UINT8"),
        ("shape", NULL, 2, 3, "UINT8"),
        ("trigger", NULL, 3, 4, "UINT8"),
        ("freq", 0x10, 4, 5, "UINT8"),
        ("retrigger", NULL, 5, 6, "UINT8")
    ]
)

def modulator_row_class(data):
    first_byte = struct.unpack("B", data[:1])[0]
    mod_type, _ = split_byte(first_byte)  # Extract type from upper nibble, ignore destination    
    if mod_type == 0x00:
        return M8AHDEnvelope
    elif mod_type == 0x01:
        return M8ADSREnvelope
    elif mod_type == 0x03:
        return M8LFO
    else:
        return M8Block

M8Modulators = m8_list_class(
    row_size=BLOCK_SIZE,
    row_count=BLOCK_COUNT,
    row_class_resolver=modulator_row_class
)


