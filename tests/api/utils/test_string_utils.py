import unittest
from m8.api.utils.string_utils import read_fixed_string, write_fixed_string

class TestStringUtils(unittest.TestCase):
    def test_read_fixed_string(self):
        # Test reading strings with different padding
        data = bytearray(b'TEST\x00\x00\x00\x00')
        self.assertEqual(read_fixed_string(data, 0, 8), 'TEST')
        
        # Test with 0xFF padding (common in M8 files)
        data = bytearray(b'MYWAV\xff\xff\xff\xff\xff')
        self.assertEqual(read_fixed_string(data, 0, 10), 'MYWAV')
        
        # Test with null terminator and trailing data
        data = bytearray(b'NAME\x00DATA')
        self.assertEqual(read_fixed_string(data, 0, 8), 'NAME')
        
        # Test with mix of padding types
        data = bytearray(b'MIX\x00\xff\xff')
        self.assertEqual(read_fixed_string(data, 0, 6), 'MIX')
        
        # Test with offset
        data = bytearray(b'SKIP_MESTRING')
        self.assertEqual(read_fixed_string(data, 7, 6), 'STRING')
    
    def test_write_fixed_string(self):
        # Test writing strings with padding
        self.assertEqual(write_fixed_string('TEST', 8), b'TEST\x00\x00\x00\x00')
        
        # Test truncating long strings
        self.assertEqual(write_fixed_string('TOOLONGSTRING', 8), b'TOOLONGS')
        
        # Test writing empty string
        self.assertEqual(write_fixed_string('', 4), b'\x00\x00\x00\x00')
        
        # Test with Unicode characters
        self.assertEqual(write_fixed_string('Café', 5), b'Caf\xc3\xa9')
        
        # Test with exact length
        self.assertEqual(write_fixed_string('EXACT', 5), b'EXACT')

if __name__ == '__main__':
    unittest.main()