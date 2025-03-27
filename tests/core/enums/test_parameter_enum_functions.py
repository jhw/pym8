import unittest
from tests.core.enums.test_logging_config import *  # Import to suppress context warnings
from m8.enums import M8FilterTypes, M8LimitTypes
from m8.core.enums import (
    serialize_param_enum_value, 
    deserialize_param_enum,
    ensure_enum_int_value,
    M8EnumValueError
)
from tests.core.enums import TestFilterType, TestLimitType

class TestParameterEnumFunctions(unittest.TestCase):
    def test_serialize_param_enum_value(self):
        # Setup test param definition with enum paths
        param_def = {
            "enums": ["m8.enums.M8FilterTypes"]
        }
        
        # Test with numeric value
        # Note: this test will use actual M8FilterTypes from m8.enums
        self.assertEqual(
            serialize_param_enum_value(M8FilterTypes.LOWPASS.value, param_def),
            "LOWPASS"
        )
        
        # Test with enum instance
        self.assertEqual(
            serialize_param_enum_value(M8FilterTypes.HIGHPASS, param_def),
            "HIGHPASS"
        )
        
        # Test with instrument-specific enums
        instrument_param_def = {
            "enums": {
                "0x00": ["m8.enums.M8FilterTypes"],
                "0x01": ["m8.enums.M8LimitTypes"]
            }
        }
        
        # WavSynth (0x00) - Should use FilterTypes
        self.assertEqual(
            serialize_param_enum_value(M8FilterTypes.BANDPASS.value, instrument_param_def, 0x00),
            "BANDPASS"
        )
        
        # MacroSynth (0x01) - Should use LimitTypes
        self.assertEqual(
            serialize_param_enum_value(M8LimitTypes.FOLD.value, instrument_param_def, 0x01),
            "FOLD"
        )
        
        # Test with no enum definition
        self.assertEqual(
            serialize_param_enum_value(5, {}, 0x00),
            5
        )
    
    def test_deserialize_param_enum(self):
        # Test string-to-int conversion with a real enum
        
        # Test deserializing a string enum name
        self.assertEqual(
            deserialize_param_enum(["m8.enums.M8FilterTypes"], "BANDPASS", "filter_type"),
            M8FilterTypes.BANDPASS.value
        )
        
        # Test with instrument-specific enums
        enum_paths = {
            "0x00": ["m8.enums.M8FilterTypes"],
            "0x01": ["m8.enums.M8LimitTypes"]
        }
        
        # Test WavSynth (0x00) - Should use FilterTypes
        self.assertEqual(
            deserialize_param_enum(enum_paths, "HIGHPASS", "filter_type", 0x00),
            M8FilterTypes.HIGHPASS.value
        )
        
        # Test MacroSynth (0x01) - Should use LimitTypes
        self.assertEqual(
            deserialize_param_enum(enum_paths, "FOLD", "limit_type", 0x01),
            M8LimitTypes.FOLD.value
        )
        
        # Test with non-string value (should return as-is)
        self.assertEqual(
            deserialize_param_enum(enum_paths, 3, "filter_type", 0x00),
            3
        )
        
        # Test with invalid string
        with self.assertRaises(M8EnumValueError):
            deserialize_param_enum(["m8.enums.M8FilterTypes"], "INVALID_FILTER", "filter_type")
    
    def test_ensure_enum_int_value(self):
        # Test with existing enum
        
        self.assertEqual(
            ensure_enum_int_value("BANDPASS", ["m8.enums.M8FilterTypes"]),
            M8FilterTypes.BANDPASS.value
        )
        
        # Test with numeric value
        self.assertEqual(
            ensure_enum_int_value(2, ["m8.enums.M8FilterTypes"]),
            2
        )
        
        # Test with invalid string
        with self.assertRaises(M8EnumValueError):
            ensure_enum_int_value("INVALID_VALUE", ["m8.enums.M8FilterTypes"])
        
        # Test with instrument-specific enums
        enum_paths = {
            "0x00": ["m8.enums.M8FilterTypes"],
            "0x01": ["m8.enums.M8LimitTypes"]
        }
        
        # Test with WavSynth (0x00)
        self.assertEqual(
            ensure_enum_int_value("LOWPASS", enum_paths, 0x00),
            M8FilterTypes.LOWPASS.value
        )
        
        # Test with MacroSynth (0x01)
        self.assertEqual(
            ensure_enum_int_value("WRAP", enum_paths, 0x01),
            M8LimitTypes.WRAP.value
        )

if __name__ == '__main__':
    unittest.main()