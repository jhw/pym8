from m8 import M8Block
from m8.utils.bits import split_byte
from m8.core.object import m8_object_class
from m8.core.list import m8_list_class

import struct

BLOCK_SIZE = 6
BLOCK_COUNT = 4

M8AHDEnvelope = m8_object_class(
    field_map=[
        ("type|destination", 0x00, 0, 1, "UINT4_2"),  # type in upper nibble, destination in lower
        ("amount", 0xFF, 1, 2, "UINT8"),
        ("attack", 0x00, 2, 3, "UINT8"),
        ("hold", 0x00, 3, 4, "UINT8"),
        ("decay", 0x00, 4, 5, "UINT8")
    ]
)

M8ADSREnvelope = m8_object_class(
    field_map=[
        ("type|destination", 0x01, 0, 1, "UINT4_2"),  # type in upper nibble, destination in lower
        ("amount", 0xFF, 1, 2, "UINT8"),
        ("attack", 0x00, 2, 3, "UINT8"),
        ("decay", 0x00, 3, 4, "UINT8"),
        ("sustain", 0x00, 4, 5, "UINT8"),
        ("release", 0x00, 5, 6, "UINT8")
    ]
)

def modulator_row_class(data):
    first_byte = struct.unpack("B", data[:1])[0]
    mod_type, _ = split_byte(first_byte)  # Extract type from upper nibble, ignore destination
    
    if mod_type == 0x00:
        return M8AHDEnvelope
    elif mod_type == 0x01:
        return M8ADSREnvelope
    else:
        return M8Block

M8ModulatorsBase = m8_list_class(
    row_size=BLOCK_SIZE,
    row_count=BLOCK_COUNT,
    row_class_resolver=modulator_row_class
)

class M8Modulators(M8ModulatorsBase):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

