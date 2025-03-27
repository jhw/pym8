import unittest
import logging
from m8.enums import M8FilterTypes, M8LimitTypes
from m8.api import deserialize_enum, deserialize_param_enum, ensure_enum_int_value
from m8.core.enums import M8EnumValueError
from m8.api.instruments import M8InstrumentParams
from tests.core.enums import TestEnum, TestFilterType, TestLimitType

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
        with self.assertRaises(M8EnumValueError):
            deserialize_enum(TestEnum, "INVALID_VALUE")

class TestEnumErrorHandling(unittest.TestCase):
    """Test that invalid enum values raise M8EnumValueError."""
    
    def setUp(self):
        # Suppress warning logs during tests
        logging.getLogger().setLevel(logging.ERROR)
    
    def test_deserialize_enum_raises_on_invalid_string(self):
        """Test that deserialize_enum raises M8EnumValueError for invalid strings."""
        with self.assertRaises(M8EnumValueError):
            deserialize_enum(M8FilterTypes, "INVALID_FILTER_TYPE")
    
    def test_deserialize_param_enum_raises_on_invalid_string(self):
        """Test that deserialize_param_enum raises M8EnumValueError for invalid strings."""
        with self.assertRaises(M8EnumValueError):
            deserialize_param_enum(['m8.enums.M8FilterTypes'], "INVALID_FILTER_TYPE")
    
    def test_ensure_enum_int_value_raises_on_invalid_string(self):
        """Test that ensure_enum_int_value raises M8EnumValueError for invalid strings."""
        with self.assertRaises(M8EnumValueError):
            ensure_enum_int_value("INVALID_FILTER_TYPE", ['m8.enums.M8FilterTypes'])
    
    def test_constructor_raises_on_invalid_enum_string(self):
        """Test that instrument constructor raises M8EnumValueError with invalid enum string."""
        # From format_config.yaml, we can see 'filter' is the field name for the filter type
        with self.assertRaises(M8EnumValueError):
            M8InstrumentParams.from_config("WAVSYNTH", filter="INVALID_FILTER_TYPE")
    
    def test_integers_do_not_raise_errors(self):
        """Test that integer values don't raise errors even if invalid."""
        # These should not raise errors even if they don't match any enum value
        self.assertEqual(deserialize_enum(M8FilterTypes, 99), 99)
        self.assertEqual(deserialize_param_enum(['m8.enums.M8FilterTypes'], 99), 99)
        self.assertEqual(ensure_enum_int_value(99, ['m8.enums.M8FilterTypes']), 99)
        
        # Should not raise an error with invalid integer
        params = M8InstrumentParams.from_config("WAVSYNTH", filter=99)
        # From format_config.yaml, 'filter' is the field name
        self.assertEqual(getattr(params, "filter"), 99)

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