import unittest
from enum import IntEnum
# Import logging configuration to suppress context warnings
from tests.core.enums.test_logging_config import *

from m8.core.enums import (
    serialize_enum, deserialize_enum,
    get_enum_paths_for_instrument, load_enum_classes,
    serialize_param_enum_value, deserialize_param_enum,
    ensure_enum_int_value, EnumPropertyMixin,
    get_enum_names, get_enum_values,
    enum_name_to_value, enum_value_to_name
)
from m8.core.enums import M8EnumValueError

# Test enum classes
class TestEnum(IntEnum):
    VALUE_ONE = 1
    VALUE_TWO = 2
    VALUE_THREE = 3

class TestLimitType(IntEnum):
    CLIP = 0
    SIN = 1
    FOLD = 2
    WRAP = 3

class TestFilterType(IntEnum):
    OFF = 0
    LOWPASS = 1
    HIGHPASS = 2
    BANDPASS = 3