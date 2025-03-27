import unittest
from tests.core.enums.test_logging_config import *  # Import to suppress context warnings
from m8.core.enums import EnumPropertyMixin
from tests.core.enums import TestFilterType, TestLimitType

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

if __name__ == '__main__':
    unittest.main()