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

    def test_edge_cases(self):
        """Test edge cases and boundary values"""
        obj = self.TestClass()
        
        # Test maximum values
        obj.single_byte = 0xFF
        self.assertEqual(obj.single_byte, 0xFF)
        
        obj.upper = 0xF
        obj.lower = 0xF
        self.assertEqual(obj.upper, 0xF)
        self.assertEqual(obj.lower, 0xF)
        self.assertEqual(obj.write()[1], 0xFF)  # Combined byte should be 0xFF
        
        # Test string truncation and padding
        obj.text = "TOO_LONG_STRING"
        self.assertEqual(obj.text, "TOO_")  # Should truncate to field size (4)
        
        obj.text = "AB"
        self.assertEqual(obj.write()[6:10], b'AB  ')  # Should pad with spaces
        
        # Test zero values
        obj.single_byte = 0
        obj.upper = 0
        obj.lower = 0
        obj.floating = 0.0
        self.assertEqual(obj.single_byte, 0)
        self.assertEqual(obj.upper, 0)
        self.assertEqual(obj.lower, 0)
        self.assertEqual(obj.floating, 0.0)

    def test_read_write_operations(self):
        """Test comprehensive read/write operations"""
        # Create object with known values
        obj1 = self.TestClass(
            single_byte=0x42,
            upper=0x5,
            lower=0x6,
            floating=1.234,
            text="TEST"
        )
        
        # Write to bytes
        data = obj1.write()
        
        # Read into new object
        obj2 = self.TestClass.read(data)
        
        # Verify all values match
        self.assertEqual(obj1.single_byte, obj2.single_byte)
        self.assertEqual(obj1.upper, obj2.upper)
        self.assertEqual(obj1.lower, obj2.lower)
        self.assertAlmostEqual(obj1.floating, obj2.floating)
        self.assertEqual(obj1.text, obj2.text)
        
        # Verify the actual bytes match
        self.assertEqual(obj1.write(), obj2.write())
        
        # Test reading with different data sizes
        with self.assertRaises(Exception):  # Should handle too-short data
            self.TestClass.read(data[:-1])

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
