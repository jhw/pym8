import unittest
from m8.utils.bits import split_byte, join_nibbles, get_bits, set_bits

class TestBitOperations(unittest.TestCase):
    def test_split_byte(self):
        """Test splitting bytes into upper and lower nibbles"""
        test_cases = [
            (0x00, (0x0, 0x0)),  # Zero
            (0xFF, (0xF, 0xF)),  # All bits set
            (0x12, (0x1, 0x2)),  # Mixed value
            (0xF0, (0xF, 0x0)),  # Upper nibble only
            (0x0F, (0x0, 0xF)),  # Lower nibble only
        ]
        for input_byte, expected in test_cases:
            upper, lower = split_byte(input_byte)
            self.assertEqual((upper, lower), expected)

    def test_join_nibbles(self):
        """Test joining upper and lower nibbles into a byte"""
        test_cases = [
            ((0x0, 0x0), 0x00),  # Zero
            ((0xF, 0xF), 0xFF),  # All bits set
            ((0x1, 0x2), 0x12),  # Mixed value
            ((0xF, 0x0), 0xF0),  # Upper nibble only
            ((0x0, 0xF), 0x0F),  # Lower nibble only
        ]
        for (upper, lower), expected in test_cases:
            result = join_nibbles(upper, lower)
            self.assertEqual(result, expected)

    def test_get_bits(self):
        """Test extracting bits from values"""
        test_cases = [
            # (value, start, length, expected)
            (0xFF, 0, 1, 1),     # Single bit from start
            (0xFF, 7, 1, 1),     # Single bit from end
            (0xF0, 4, 4, 0xF),   # Multiple bits
            (0x0F, 0, 4, 0xF),   # Lower bits
            (0xFF, 2, 3, 0x7),   # Middle bits
            (0x00, 0, 8, 0x00),  # All zeros
        ]
        for value, start, length, expected in test_cases:
            result = get_bits(value, start, length)
            self.assertEqual(result, expected)

    def test_set_bits(self):
        """Test setting bits in values"""
        test_cases = [
            # (initial, bits, start, length, expected)
            (0x00, 1, 0, 1, 0x01),      # Set single bit
            (0x00, 0xF, 4, 4, 0xF0),    # Set upper nibble
            (0xFF, 0, 4, 4, 0x0F),      # Clear upper nibble
            (0x00, 0x3, 2, 2, 0x0C),    # Set middle bits
            (0xFF, 0, 0, 8, 0x00),      # Clear all bits
            (0x00, 0xFF, 0, 8, 0xFF),   # Set all bits
        ]
        for initial, bits, start, length, expected in test_cases:
            result = set_bits(initial, bits, start, length)
            self.assertEqual(result, expected)

    def test_boundary_conditions(self):
        """Test boundary conditions and error cases"""
        # Overflow in upper/lower nibbles is handled by masking
        self.assertEqual(join_nibbles(0xFF, 0xFF), 0xFF)
        self.assertEqual(join_nibbles(0x1FF, 0x1FF), 0xFF)

        # get_bits with zero length returns 0
        self.assertEqual(get_bits(0xFF, 0, 0), 0)

        # set_bits with zero length doesn't modify value
        self.assertEqual(set_bits(0xFF, 0xFF, 0, 0), 0xFF)

if __name__ == '__main__':
    unittest.main()
