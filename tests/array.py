import unittest
import struct
from m8 import NULL
from m8.core.array import m8_array_class

class TestM8Array(unittest.TestCase):
    def setUp(self):
        """Create test array class for bytes"""
        self.TestClass = m8_array_class(
            length=3,
            fmt="B",  # unsigned byte
            default=0x42
        )

    def test_initialization(self):
        """Test array initialization with defaults"""
        array = self.TestClass()
        self.assertEqual(len(array.as_list()), 3)
        self.assertTrue(all(x == 0x42 for x in array.as_list()))

    def test_array_access(self):
        """Test array access and modification"""
        array = self.TestClass()
        array[0] = 0xFF
        array[2] = 0x00
        
        self.assertEqual(array[0], 0xFF)
        self.assertEqual(array[1], 0x42)  # Default value
        self.assertEqual(array[2], 0x00)

    def test_data_persistence(self):
        """Test write/read cycle preserves data"""
        array1 = self.TestClass()
        array1[0] = 0xFF
        array1[1] = 0x00
        
        data = array1.write()
        array2 = self.TestClass.read(data)
        
        self.assertEqual(array2[0], 0xFF)
        self.assertEqual(array2[1], 0x00)
        self.assertEqual(array2[2], 0x42)  # Default preserved

    def test_empty_check(self):
        """Test is_empty() functionality"""
        array = self.TestClass()
        
        # Set a non-default value
        array[0] = 0xFF
        self.assertFalse(array.is_empty())
        
        # Set back to default values
        array[0] = 0x42
        array[1] = 0x42
        array[2] = 0x42
        self.assertTrue(array.is_empty())

    def test_bounds_checking(self):
        """Test array bounds checking"""
        array = self.TestClass()
        
        with self.assertRaises(IndexError):
            array[3] = 0x00
            
        with self.assertRaises(IndexError):
            _ = array[-1]

    def test_value_validation(self):
        """Test value handling"""
        array = self.TestClass()
        
        # Test upper bound
        array[0] = 0xFF  # Maximum valid value
        self.assertEqual(array[0], 0xFF)
        
        # Test lower bound
        array[0] = 0x00  # Minimum valid value
        self.assertEqual(array[0], 0x00)
        
        # Test out of range values
        with self.assertRaises(struct.error):
            array[0] = 0x100  # Too large
        with self.assertRaises(struct.error):
            array[0] = -1  # Too small

    def test_clone(self):
        """Test array cloning"""
        array1 = self.TestClass()
        array1[0] = 0xFF
        
        array2 = array1.clone()
        array2[0] = 0x00
        
        self.assertEqual(array1[0], 0xFF)
        self.assertEqual(array2[0], 0x00)

    def test_size_validation(self):
        """Test size validation in read()"""
        # Our test array needs 3 bytes (length=3, fmt="B")
        
        # Test data too short
        short_data = bytes([0xFF, 0xFF])  # Only 2 bytes
        with self.assertRaises(ValueError) as ctx:
            self.TestClass.read(short_data)
        self.assertIn("Data too short", str(ctx.exception))
    
        # Test exact size works
        exact_data = bytes([0xFF, 0xFF, 0xFF])
        array = self.TestClass.read(exact_data)
        self.assertEqual(len(array.as_list()), 3)
    
        # Test longer data works (extra bytes ignored)
        long_data = bytes([0xFF, 0xFF, 0xFF, 0xFF])
        array = self.TestClass.read(long_data)
        self.assertEqual(len(array.as_list()), 3)

if __name__ == '__main__':
    unittest.main()
