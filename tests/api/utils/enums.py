import unittest
from enum import IntEnum

from m8.api.utils.enums import (
    serialize_enum, deserialize_enum,
    get_enum_paths_for_instrument, load_enum_classes,
    serialize_param_enum_value, deserialize_param_enum,
    ensure_enum_int_value, EnumPropertyMixin,
    get_enum_names, get_enum_values,
    enum_name_to_value, enum_value_to_name
)
from m8.enums import M8EnumError

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

class TestEnumFunctions(unittest.TestCase):
    def test_serialize_enum(self):
        # Test with enum instance
        enum_value = TestEnum.VALUE_ONE
        self.assertEqual(serialize_enum(enum_value), "VALUE_ONE")
        
        # Test with non-enum value
        self.assertEqual(serialize_enum(5), 5)
    
    def test_deserialize_enum(self):
        # Test with string enum name
        self.assertEqual(deserialize_enum(TestEnum, "VALUE_TWO"), 2)
        
        # Test with numeric value
        self.assertEqual(deserialize_enum(TestEnum, 3), 3)
        
        # Test with invalid string
        with self.assertRaises(M8EnumError):
            deserialize_enum(TestEnum, "INVALID_VALUE")

class TestInstrumentEnumFunctions(unittest.TestCase):
    def test_get_enum_paths_for_instrument(self):
        # Setup test enum paths
        enum_paths = {
            "0x00": ["m8.enums.wavsynth.TestWavSynthEnum"],
            "0x01": ["m8.enums.macrosynth.TestMacroSynthEnum"],
            "0x02": ["m8.enums.sampler.TestSamplerEnum"]
        }
        
        # Test with different instrument types
        self.assertEqual(
            get_enum_paths_for_instrument(enum_paths, 0x00),
            ["m8.enums.wavsynth.TestWavSynthEnum"]
        )
        
        self.assertEqual(
            get_enum_paths_for_instrument(enum_paths, "0x01"),
            ["m8.enums.macrosynth.TestMacroSynthEnum"]
        )
        
        # Test with string numeric value
        self.assertEqual(
            get_enum_paths_for_instrument(enum_paths, "0"),
            ["m8.enums.wavsynth.TestWavSynthEnum"]
        )
        
        # Test with non-dict
        non_dict_paths = ["some.enum.path"]
        self.assertEqual(
            get_enum_paths_for_instrument(non_dict_paths, 0x00),
            non_dict_paths
        )
        
        # Test with None instrument type
        self.assertEqual(
            get_enum_paths_for_instrument(enum_paths, None),
            enum_paths
        )
        
        # Test with missing instrument type
        self.assertIsNone(
            get_enum_paths_for_instrument(enum_paths, 0x03)
        )
    
    def test_load_enum_classes(self):
        # This test uses real enums from the codebase
        enum_paths = ["m8.enums.M8FilterTypes", "m8.enums.M8LimitTypes"]
        
        # Load enum classes
        enum_classes = load_enum_classes(enum_paths)
        
        # Verify correct enum classes were loaded
        self.assertEqual(len(enum_classes), 2)
        self.assertEqual(enum_classes[0].__name__, "M8FilterTypes")
        self.assertEqual(enum_classes[1].__name__, "M8LimitTypes")
        
        # Test with single string path
        single_enum_class = load_enum_classes("m8.enums.M8FilterTypes")
        self.assertEqual(len(single_enum_class), 1)
        self.assertEqual(single_enum_class[0].__name__, "M8FilterTypes")
        
        # Test with empty path
        self.assertEqual(load_enum_classes(None), [])
        self.assertEqual(load_enum_classes([]), [])
        
        # Test with invalid path
        self.assertEqual(load_enum_classes(["invalid.module.path"]), [])

class TestParameterEnumFunctions(unittest.TestCase):
    def test_serialize_param_enum_value(self):
        # Setup test param definition with enum paths
        param_def = {
            "enums": ["m8.enums.M8FilterTypes"]
        }
        
        # Test with numeric value
        # Note: this test will use actual M8FilterTypes from m8.enums
        from m8.enums import M8FilterTypes
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
        
        from m8.enums import M8LimitTypes
        
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
        from m8.enums import M8FilterTypes, M8LimitTypes
        
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
        with self.assertRaises(M8EnumError):
            deserialize_param_enum(["m8.enums.M8FilterTypes"], "INVALID_FILTER", "filter_type")
    
    def test_ensure_enum_int_value(self):
        # Test with existing enum
        from m8.enums import M8FilterTypes
        
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
        with self.assertRaises(M8EnumError):
            ensure_enum_int_value("INVALID_VALUE", ["m8.enums.M8FilterTypes"])
        
        # Test with instrument-specific enums
        enum_paths = {
            "0x00": ["m8.enums.M8FilterTypes"],
            "0x01": ["m8.enums.M8LimitTypes"]
        }
        
        from m8.enums import M8LimitTypes
        
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

class TestEnumPropertyMixin(unittest.TestCase):
    class TestClass(EnumPropertyMixin):
        ENUM_MAPPINGS = {
            'filter_type': {'enum_class': TestFilterType},
            'limit_type': {'enum_class': TestLimitType}
        }
        
        def __init__(self):
            self._filter_type = TestFilterType.LOWPASS.value
            self._limit_type = TestLimitType.FOLD.value
        
        @property
        def filter_type(self):
            return self._get_enum_name('filter_type', self._filter_type)
        
        @filter_type.setter
        def filter_type(self, value):
            self._filter_type = self._get_enum_value('filter_type', value)
        
        @property
        def limit_type(self):
            return self._get_enum_name('limit_type', self._limit_type)
        
        @limit_type.setter
        def limit_type(self, value):
            self._limit_type = self._get_enum_value('limit_type', value)
    
    def test_enum_property_mixin(self):
        # Create test instance
        test_obj = self.TestClass()
        
        # Check default values
        self.assertEqual(test_obj.filter_type, "LOWPASS")
        self.assertEqual(test_obj.limit_type, "FOLD")
        
        # Test setting with string enum name
        test_obj.filter_type = "BANDPASS"
        self.assertEqual(test_obj.filter_type, "BANDPASS")
        self.assertEqual(test_obj._filter_type, TestFilterType.BANDPASS.value)
        
        # Test setting with int value
        test_obj.limit_type = TestLimitType.WRAP.value
        self.assertEqual(test_obj.limit_type, "WRAP")
        self.assertEqual(test_obj._limit_type, TestLimitType.WRAP.value)
        
        # Test setting invalid enum name
        with self.assertRaises(ValueError):
            test_obj.filter_type = "INVALID_FILTER"

class TestUtilityFunctions(unittest.TestCase):
    def test_get_enum_names(self):
        names = get_enum_names(TestFilterType)
        self.assertEqual(names, ["OFF", "LOWPASS", "HIGHPASS", "BANDPASS"])
    
    def test_get_enum_values(self):
        values = get_enum_values(TestFilterType)
        self.assertEqual(values, [0, 1, 2, 3])
    
    def test_enum_name_to_value(self):
        self.assertEqual(enum_name_to_value(TestFilterType, "HIGHPASS"), 2)
        
        with self.assertRaises(KeyError):
            enum_name_to_value(TestFilterType, "INVALID")
    
    def test_enum_value_to_name(self):
        self.assertEqual(enum_value_to_name(TestFilterType, 1), "LOWPASS")
        
        with self.assertRaises(ValueError):
            enum_value_to_name(TestFilterType, 99)

if __name__ == '__main__':
    unittest.main()