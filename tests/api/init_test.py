import unittest
from m8.api import split_byte, join_nibbles, get_bits, set_bits, M8Block

class TestM8ApiInit(unittest.TestCase):
    def test_split_byte(self):
        # Test splitting bytes into upper and lower nibbles
        self.assertEqual(split_byte(0x00), (0, 0))
        self.assertEqual(split_byte(0xFF), (15, 15))
        self.assertEqual(split_byte(0x12), (1, 2))
        self.assertEqual(split_byte(0xAB), (10, 11))
        self.assertEqual(split_byte(0x5C), (5, 12))

    def test_join_nibbles(self):
        # Test joining upper and lower nibbles into a byte
        self.assertEqual(join_nibbles(0, 0), 0x00)
        self.assertEqual(join_nibbles(15, 15), 0xFF)
        self.assertEqual(join_nibbles(1, 2), 0x12)
        self.assertEqual(join_nibbles(10, 11), 0xAB)
        self.assertEqual(join_nibbles(5, 12), 0x5C)
        
        # Test with values larger than 4 bits (should mask to 4 bits)
        self.assertEqual(join_nibbles(0xFF, 0xFF), 0xFF)
        self.assertEqual(join_nibbles(0x1F, 0x0F), 0xFF)
        self.assertEqual(join_nibbles(0xF1, 0xF2), 0x12)

    def test_get_bits(self):
        # Test extracting specific bits
        # Get a single bit
        self.assertEqual(get_bits(0b0001, 0), 1)  # Least significant bit
        self.assertEqual(get_bits(0b0010, 1), 1)  # Second bit
        self.assertEqual(get_bits(0b0100, 2), 1)  # Third bit
        self.assertEqual(get_bits(0b1000, 3), 1)  # Fourth bit
        self.assertEqual(get_bits(0b0000, 0), 0)  # Zero value
        
        # Get multiple bits
        self.assertEqual(get_bits(0b1010, 0, 2), 0b10)  # Two least significant bits
        self.assertEqual(get_bits(0b1010, 1, 2), 0b01)  # Bits 1-2
        self.assertEqual(get_bits(0b1111, 0, 4), 0b1111)  # All 4 bits
        self.assertEqual(get_bits(0xA5, 0, 8), 0xA5)  # All 8 bits
        self.assertEqual(get_bits(0xA5, 4, 4), 0xA)  # Upper nibble

    def test_set_bits(self):
        # Test setting specific bits
        # Set a single bit
        self.assertEqual(set_bits(0b0000, 1, 0), 0b0001)  # Set least significant bit
        self.assertEqual(set_bits(0b0000, 1, 1), 0b0010)  # Set second bit
        self.assertEqual(set_bits(0b0000, 1, 2), 0b0100)  # Set third bit
        self.assertEqual(set_bits(0b0000, 1, 3), 0b1000)  # Set fourth bit
        self.assertEqual(set_bits(0b1111, 0, 0), 0b1110)  # Clear least significant bit
        
        # Set multiple bits
        self.assertEqual(set_bits(0b0000, 0b11, 0, 2), 0b0011)  # Set two least significant bits
        self.assertEqual(set_bits(0b0000, 0b11, 1, 2), 0b0110)  # Set bits 1-2
        self.assertEqual(set_bits(0b0000, 0b1111, 0, 4), 0b1111)  # Set all 4 bits
        self.assertEqual(set_bits(0b1111, 0b0000, 0, 4), 0b0000)  # Clear all 4 bits
        self.assertEqual(set_bits(0x05, 0xA, 4, 4), 0xA5)  # Set upper nibble

    def test_m8block_read(self):
        # Test M8Block read functionality
        test_data = b'\x01\x02\x03\x04'
        block = M8Block.read(test_data)
        self.assertEqual(block.data, bytearray(b'\x01\x02\x03\x04'))

    def test_m8block_is_empty(self):
        # Test M8Block is_empty functionality
        empty_block = M8Block()
        self.assertTrue(empty_block.is_empty())
        
        empty_block.data = bytearray(b'\x00\x00\x00')
        self.assertTrue(empty_block.is_empty())
        
        non_empty_block = M8Block()
        non_empty_block.data = bytearray(b'\x01\x00\x00')
        self.assertFalse(non_empty_block.is_empty())

    def test_m8block_write(self):
        # Test M8Block write functionality
        block = M8Block()
        block.data = bytearray(b'\x01\x02\x03\x04')
        self.assertEqual(block.write(), bytearray(b'\x01\x02\x03\x04'))

    def test_m8block_as_dict(self):
        # Test M8Block as_dict functionality
        block = M8Block()
        block.data = bytearray(b'\x01\x02\x03')
        expected = {"data": [1, 2, 3]}
        self.assertEqual(block.as_dict(), expected)

    def test_m8block_from_dict(self):
        # Test M8Block from_dict functionality
        dict_data = {"data": [1, 2, 3]}
        block = M8Block.from_dict(dict_data)
        self.assertEqual(block.data, bytearray(b'\x01\x02\x03'))
        
        # Test with empty dict
        empty_block = M8Block.from_dict({})
        self.assertEqual(empty_block.data, bytearray())

if __name__ == '__main__':
    unittest.main()