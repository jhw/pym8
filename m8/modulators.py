from m8 import M8Block, NULL, BLANK
from m8.utils.bits import split_byte
from m8.core.object import m8_object_class
from m8.core.list import m8_list_class

import struct

BLOCK_SIZE = 6
BLOCK_COUNT = 4

M8AHDEnvelope = m8_object_class(
    field_map=[
        ("type|destination", NULL, 0, 1, "UINT4_2"),  # type in upper nibble, destination in lower
        ("amount", BLANK, 1, 2, "UINT8"),
        ("attack", NULL, 2, 3, "UINT8"),
        ("hold", NULL, 3, 4, "UINT8"),
        ("decay", NULL, 4, 5, "UINT8")
    ]
)

M8ADSREnvelope = m8_object_class(
    field_map=[
        ("type|destination", 0x01, 0, 1, "UINT4_2"),  # type in upper nibble, destination in lower
        ("amount", BLANK, 1, 2, "UINT8"),
        ("attack", NULL, 2, 3, "UINT8"),
        ("decay", NULL, 3, 4, "UINT8"),
        ("sustain", NULL, 4, 5, "UINT8"),
        ("release", NULL, 5, 6, "UINT8")
    ]
)

def modulator_row_class(data):
    first_byte = struct.unpack("B", data[:1])[0]
    mod_type, _ = split_byte(first_byte)  # Extract type from upper nibble, ignore destination    
    if mod_type == NULL:
        return M8AHDEnvelope
    elif mod_type == 0x01:
        return M8ADSREnvelope
    else:
        return M8Block

M8Modulators = m8_list_class(
    row_size=BLOCK_SIZE,
    row_count=BLOCK_COUNT,
    row_class_resolver=modulator_row_class
)


