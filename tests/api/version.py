import unittest
from m8.api.version import M8Version
from m8.api import split_byte, join_nibbles

class TestM8Version(unittest.TestCase):
    def test_read_from_binary(self):
        # Test case 1: Valid binary data (minor=3, patch=5, major=2)
        test_data = bytes([0x35, 0x02])  # 0x35 = (3 << 4) | 5, 0x02 = (0 << 4) | 2
        version = M8Version.read(test_data)
        self.assertEqual(version.major, 2)
        self.assertEqual(version.minor, 3)
        self.assertEqual(version.patch, 5)
        
        # Test case 2: Empty binary data - should create with defaults
        test_data = bytes([])
        version = M8Version.read(test_data)
        self.assertEqual(version.major, 0)
        self.assertEqual(version.minor, 0)
        self.assertEqual(version.patch, 0)
        
        # Test case 3: Valid data with large values
        test_data = bytes([0xFE, 0x0F])  # 0xFE = (15 << 4) | 14, 0x0F = (0 << 4) | 15
        version = M8Version.read(test_data)
        self.assertEqual(version.major, 15)
        self.assertEqual(version.minor, 15)
        self.assertEqual(version.patch, 14)

    def test_write_to_binary(self):
        # Test case 1: Regular values
        version = M8Version(major=2, minor=3, patch=5)
        result = version.write()
        self.assertEqual(len(result), M8Version.BLOCK_SIZE)
        self.assertEqual(result, bytes([0x35, 0x02]))
        
        # Test case 2: Default values
        version = M8Version()
        result = version.write()
        self.assertEqual(result, bytes([0x00, 0x00]))
        
        # Test case 3: Maximum values (assuming 4-bit nibbles)
        version = M8Version(major=15, minor=15, patch=15)
        result = version.write()
        self.assertEqual(result, bytes([0xFF, 0x0F]))

    def test_read_write_consistency(self):
        # Test binary serialization/deserialization consistency
        test_cases = [
            (1, 2, 3),
            (0, 0, 0),
            (15, 15, 15),
            (10, 5, 2)
        ]
        
        for major, minor, patch in test_cases:
            # Create a version object
            original = M8Version(major=major, minor=minor, patch=patch)
            
            # Serialize to binary
            binary = original.write()
            
            # Deserialize from binary
            deserialized = M8Version.read(binary)
            
            # Verify all properties match
            self.assertEqual(deserialized.major, original.major)
            self.assertEqual(deserialized.minor, original.minor)
            self.assertEqual(deserialized.patch, original.patch)
            self.assertEqual(str(deserialized), str(original))

    def test_constructor_and_defaults(self):
        # Test case 1: Default constructor
        version = M8Version()
        self.assertEqual(version.major, 0)
        self.assertEqual(version.minor, 0)
        self.assertEqual(version.patch, 0)
        
        # Test case 2: Constructor with arguments
        version = M8Version(major=1, minor=2, patch=3)
        self.assertEqual(version.major, 1)
        self.assertEqual(version.minor, 2)
        self.assertEqual(version.patch, 3)
        
        # Test case 3: Partial arguments
        version = M8Version(major=4)
        self.assertEqual(version.major, 4)
        self.assertEqual(version.minor, 0)
        self.assertEqual(version.patch, 0)

    def test_is_empty(self):
        # Test is_empty method
        self.assertTrue(M8Version().is_empty())
        self.assertTrue(M8Version(0, 0, 0).is_empty())
        self.assertFalse(M8Version(1, 0, 0).is_empty())
        self.assertFalse(M8Version(0, 1, 0).is_empty())
        self.assertFalse(M8Version(0, 0, 1).is_empty())

    def test_clone(self):
        # Test clone method
        original = M8Version(major=2, minor=3, patch=4)
        clone = original.clone()
        
        # Verify clone has the same values
        self.assertEqual(clone.major, original.major)
        self.assertEqual(clone.minor, original.minor)
        self.assertEqual(clone.patch, original.patch)
        
        # Verify clone is a different object
        self.assertIsNot(clone, original)
        
        # Modify clone and verify original remains unchanged
        clone.major = 5
        self.assertEqual(original.major, 2)

    def test_from_str(self):
        # Test case 1: Valid version string
        version = M8Version.from_str("1.2.3")
        self.assertEqual(version.major, 1)
        self.assertEqual(version.minor, 2)
        self.assertEqual(version.patch, 3)
        
        # Test case 2: Partial version string
        version = M8Version.from_str("4.5")
        self.assertEqual(version.major, 4)
        self.assertEqual(version.minor, 5)
        self.assertEqual(version.patch, 0)
        
        # Test case 3: Single number version string
        version = M8Version.from_str("6")
        self.assertEqual(version.major, 6)
        self.assertEqual(version.minor, 0)
        self.assertEqual(version.patch, 0)
        
        # Test case 4: Invalid version string
        version = M8Version.from_str("not.a.version")
        self.assertEqual(version.major, 0)
        self.assertEqual(version.minor, 0)
        self.assertEqual(version.patch, 0)
        
        # Test case 5: Non-string input
        version = M8Version.from_str(None)
        self.assertEqual(version.major, 0)
        self.assertEqual(version.minor, 0)
        self.assertEqual(version.patch, 0)

    def test_repr(self):
        # Test string representation
        version = M8Version(major=1, minor=2, patch=3)
        self.assertEqual(str(version), "1.2.3")
        self.assertEqual(repr(version), "1.2.3")

if __name__ == '__main__':
    unittest.main()