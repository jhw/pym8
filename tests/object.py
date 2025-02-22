import unittest
from m8.core.object import m8_object_class

class TestM8Object(unittest.TestCase):
    def setUp(self):
        # Create test class with one of each supported data type
        self.TestClass = m8_object_class([
            # name, default, start, end, format
            ("single_byte", 0x42, 0, 1, "UINT8"),
            ("upper|lower", 0x12, 1, 2, "UINT4_2"),  # 0x1 in upper nibble, 0x2 in lower
            ("floating", 1.5, 2, 6, "FLOAT32"),
            ("text", "TEST", 6, 10, "STRING")
        ])
        
    def test_default_initialization(self):
        """Test that object initializes with default values"""
        obj = self.TestClass()
        
        # Check direct values
        self.assertEqual(obj.single_byte, 0x42)
        self.assertEqual(obj.upper, 0x1)
        self.assertEqual(obj.lower, 0x2)
        self.assertAlmostEqual(obj.floating, 1.5)  # Use assertAlmostEqual for floats
        self.assertEqual(obj.text, "TEST")
        
        # Check underlying bytes
        data = obj.write()
        self.assertEqual(data[0], 0x42)  # single_byte
        self.assertEqual(data[1], 0x12)  # upper|lower combined
        # Skip checking float bytes as they're more complex
        self.assertEqual(data[6:10], b'TEST')  # text

    def test_constructor_values(self):
        """Test initialization with provided values"""
        obj = self.TestClass(
            single_byte=0x55,
            upper=0x7,
            lower=0x3,
            floating=2.5,
            text="ABCD"
        )
        
        # Check direct values
        self.assertEqual(obj.single_byte, 0x55)
        self.assertEqual(obj.upper, 0x7)
        self.assertEqual(obj.lower, 0x3)
        self.assertAlmostEqual(obj.floating, 2.5)
        self.assertEqual(obj.text, "ABCD")
        
        # Check underlying bytes
        data = obj.write()
        self.assertEqual(data[0], 0x55)  # single_byte
        self.assertEqual(data[1], 0x73)  # upper|lower combined (0x7 << 4 | 0x3)
        # Skip checking float bytes
        self.assertEqual(data[6:10], b'ABCD')  # text

    def test_setters(self):
        """Test setting values after initialization"""
        obj = self.TestClass()
        
        # Set new values
        obj.single_byte = 0x99
        obj.upper = 0xF
        obj.lower = 0x5
        obj.floating = 3.75
        obj.text = "WXYZ"
        
        # Check direct values
        self.assertEqual(obj.single_byte, 0x99)
        self.assertEqual(obj.upper, 0xF)
        self.assertEqual(obj.lower, 0x5)
        self.assertAlmostEqual(obj.floating, 3.75)
        self.assertEqual(obj.text, "WXYZ")
        
        # Check underlying bytes
        data = obj.write()
        self.assertEqual(data[0], 0x99)  # single_byte
        self.assertEqual(data[1], 0xF5)  # upper|lower combined
        # Skip checking float bytes
        self.assertEqual(data[6:10], b'WXYZ')  # text
        
    def test_read(self):
        """Test reading values from bytes"""
        # Create known byte pattern
        raw_bytes = bytearray([
            0x77,           # single_byte
            0x84,           # upper|lower (0x8 in upper, 0x4 in lower)
            0, 0, 0x20, 0x40,  # floating (2.5 in float32)
            ord('X'), ord('Y'), ord('Z'), ord('W')  # text
        ])
        
        # Read into object
        obj = self.TestClass.read(raw_bytes)
        
        # Check values were read correctly
        self.assertEqual(obj.single_byte, 0x77)
        self.assertEqual(obj.upper, 0x8)
        self.assertEqual(obj.lower, 0x4)
        self.assertAlmostEqual(obj.floating, 2.5)
        self.assertEqual(obj.text, "XYZW")

    def test_data_length_validation(self):
        """Test data length validation when reading"""
        # Create a byte array shorter than required
        short_data = bytearray([0x77, 0x84])  # Only 2 bytes
        
        # Attempting to read should raise an exception
        with self.assertRaises(Exception):
            self.TestClass.read(short_data)
            
        # Creating a longer array should work fine
        long_data = bytearray([0x77, 0x84, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        obj = self.TestClass.read(long_data)
        self.assertEqual(obj.single_byte, 0x77)

    def test_as_dict_with_enums(self):
        """Test as_dict method with enum fields"""
        # Create a sample M8Object class with enums
        from enum import Enum
        from m8.core.object import m8_object_class
        
        class TestEnum(Enum):
            FIRST = 0x01
            SECOND = 0x02
            THIRD = 0x03
        
        class TypeEnum(Enum):
            TYPE_A = 0x01
            TYPE_B = 0x02
            TYPE_C = 0x03
        
        class ModeEnum(Enum):
            MODE_X = 0x01
            MODE_Y = 0x02
            MODE_Z = 0x03
        
        # Create object class with enum fields
        TestObject = m8_object_class(
            field_map=[
                ("category", 0x02, 0, 1, "UINT8", TestEnum),
                ("type|mode", 0x12, 1, 2, "UINT4_2", (TypeEnum, ModeEnum)),
                ("value|_", 0x30, 2, 3, "UINT4_2", (TestEnum, None)),
                ("name", "TEST", 3, 7, "STRING"),
                ("level", 1.5, 7, 11, "FLOAT32")
            ]
        )
        
        # Create an instance with specific values
        obj = TestObject()
        obj.category = TestEnum.THIRD  # 0x03
        obj.type = TypeEnum.TYPE_B     # 0x02
        obj.mode = ModeEnum.MODE_Z     # 0x03
        obj.value = TestEnum.SECOND    # 0x02
        obj.name = "ENUM"
        obj.level = 2.5
        
        # Get dictionary representation
        result = obj.as_dict()
        
        # Verify enum values are converted to their names
        self.assertEqual(result["category"], "THIRD")
        self.assertEqual(result["type"], "TYPE_B")
        self.assertEqual(result["mode"], "MODE_Z")
        self.assertEqual(result["value"], "SECOND")
        
        # Regular fields should be unchanged
        self.assertEqual(result["name"], "ENUM")
        self.assertAlmostEqual(result["level"], 2.5)
        
        # Test with invalid enum value (not in enum)
        # Manually set raw value that doesn't correspond to an enum
        obj._data[0] = 0x99  # Invalid value for category field
        result = obj.as_dict()
        self.assertEqual(result["category"], 0x99)  # Should be raw integer
        

    def test_clone(self):
        """Test cloning an object"""
        # Create original object
        obj1 = self.TestClass(
            single_byte=0x55,
            upper=0x7,
            lower=0x3,
            floating=2.5,
            text="ABCD"
        )
        
        # Clone it
        obj2 = obj1.clone()
        
        # Verify values match
        self.assertEqual(obj1.single_byte, obj2.single_byte)
        self.assertEqual(obj1.upper, obj2.upper)
        self.assertEqual(obj1.lower, obj2.lower)
        self.assertAlmostEqual(obj1.floating, obj2.floating)
        self.assertEqual(obj1.text, obj2.text)
        
        # Verify modification of clone doesn't affect original
        obj2.single_byte = 0x99
        obj2.text = "WXYZ"
        
        self.assertEqual(obj1.single_byte, 0x55)  # Original unchanged
        self.assertEqual(obj2.single_byte, 0x99)  # Clone modified
        
        self.assertEqual(obj1.text, "ABCD")  # Original unchanged
        self.assertEqual(obj2.text, "WXYZ")  # Clone modified

    def test_attribute_errors(self):
        """Test handling of invalid attribute access"""
        obj = self.TestClass()
        
        # Accessing non-existent attribute should raise AttributeError
        with self.assertRaises(AttributeError):
            value = obj.non_existent_field
            
        # Setting non-existent attribute should add it as a regular Python attribute
        obj.custom_attribute = "custom value"
        self.assertEqual(obj.custom_attribute, "custom value")
        
        # This shouldn't affect the binary representation
        data1 = obj.write()
        del obj.custom_attribute
        data2 = obj.write()
        self.assertEqual(data1, data2)

    def test_is_empty(self):
        """Test is_empty() functionality"""
        # Test with default values
        obj = self.TestClass()
        self.assertTrue(obj.is_empty())
        
        # Modify each field and test is_empty
        orig_value = obj.single_byte
        obj.single_byte = 0x99
        self.assertFalse(obj.is_empty())
        obj.single_byte = orig_value
        self.assertTrue(obj.is_empty())
        
        orig_value = obj.upper
        obj.upper = 0x8
        self.assertFalse(obj.is_empty())
        obj.upper = orig_value
        self.assertTrue(obj.is_empty())
        
        orig_value = obj.lower
        obj.lower = 0x7
        self.assertFalse(obj.is_empty())
        obj.lower = orig_value
        self.assertTrue(obj.is_empty())
        
        orig_value = obj.floating
        obj.floating = 3.14
        self.assertFalse(obj.is_empty())
        obj.floating = orig_value
        self.assertTrue(obj.is_empty())
        
        orig_value = obj.text
        obj.text = "WXYZ"
        self.assertFalse(obj.is_empty())
        obj.text = orig_value
        self.assertTrue(obj.is_empty())

    def test_string_handling(self):
        """Test special handling for string fields"""
        obj = self.TestClass()
        
        # Test string truncation for too-long strings
        obj.text = "TOO_LONG_STRING"
        self.assertEqual(obj.text, "TOO_")  # Should be truncated to field size
        
        # Test null termination
        obj.text = "AB"
        raw_data = obj.write()
        self.assertEqual(raw_data[6:10], b'AB\x00\x00')  # Should be null-terminated
        
        # Test reading string with embedded nulls
        raw_bytes = bytearray([0x42, 0x12, 0, 0, 0, 0, ord('A'), ord('B'), 0, ord('D')])
        obj = self.TestClass.read(raw_bytes)
        self.assertEqual(obj.text, "AB")  # Should stop at first null

    def test_default_constructor_args(self):
        """Test constructor argument handling"""
        # Test partial initialization with defaults
        obj = self.TestClass(single_byte=0x77)  # Only set one field
        self.assertEqual(obj.single_byte, 0x77)
        self.assertEqual(obj.upper, 0x1)  # Should have default value
        self.assertEqual(obj.lower, 0x2)  # Should have default value
        self.assertAlmostEqual(obj.floating, 1.5)  # Should have default value
        self.assertEqual(obj.text, "TEST")  # Should have default value
        
        # Test UINT4_2 partial initialization
        obj = self.TestClass(upper=0x7)  # Only set upper nibble
        self.assertEqual(obj.upper, 0x7)
        self.assertEqual(obj.lower, 0x2)  # Should keep default
        
        obj = self.TestClass(lower=0x7)  # Only set lower nibble
        self.assertEqual(obj.upper, 0x1)  # Should keep default
        self.assertEqual(obj.lower, 0x7)
        
        # Test invalid field name
        with self.assertRaises(AttributeError):
            obj = self.TestClass(invalid_field=123)


if __name__ == '__main__':
    unittest.main()
