import unittest
import logging
from m8.enums import M8EnumError
from m8.enums import M8FilterTypes, M8LimitTypes
from m8.api import deserialize_enum, deserialize_param_enum, ensure_enum_int_value
from m8.api.instruments import M8InstrumentParams

class TestEnumErrorHandling(unittest.TestCase):
    """Test that invalid enum values raise M8EnumError."""
    
    def setUp(self):
        # Suppress warning logs during tests
        logging.getLogger().setLevel(logging.ERROR)
    
    def test_deserialize_enum_raises_on_invalid_string(self):
        """Test that deserialize_enum raises M8EnumError for invalid strings."""
        with self.assertRaises(M8EnumError):
            deserialize_enum(M8FilterTypes, "INVALID_FILTER_TYPE")
    
    def test_deserialize_param_enum_raises_on_invalid_string(self):
        """Test that deserialize_param_enum raises M8EnumError for invalid strings."""
        with self.assertRaises(M8EnumError):
            deserialize_param_enum(['m8.enums.M8FilterTypes'], "INVALID_FILTER_TYPE")
    
    def test_ensure_enum_int_value_raises_on_invalid_string(self):
        """Test that ensure_enum_int_value raises M8EnumError for invalid strings."""
        with self.assertRaises(M8EnumError):
            ensure_enum_int_value("INVALID_FILTER_TYPE", ['m8.enums.M8FilterTypes'])
    
    def test_constructor_raises_on_invalid_enum_string(self):
        """Test that instrument constructor raises M8EnumError with invalid enum string."""
        # From format_config.yaml, we can see 'filter' is the field name for the filter type
        with self.assertRaises(M8EnumError):
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