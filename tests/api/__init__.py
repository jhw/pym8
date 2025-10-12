import unittest
from m8.api import M8Block

class TestM8ApiInit(unittest.TestCase):
    def test_m8block_read(self):
        # Test M8Block read functionality
        test_data = b'\x01\x02\x03\x04'
        block = M8Block.read(test_data)
        self.assertEqual(block.data, bytearray(b'\x01\x02\x03\x04'))

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