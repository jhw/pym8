import unittest
from m8.api.fx import M8FXTuple, M8FXTuples, BLOCK_SIZE, BLOCK_COUNT, EMPTY_KEY, DEFAULT_VALUE

# Test FX values - use hardcoded integers since we removed enums
TEST_FX_VOL = 0x01
TEST_FX_PAN = 0x02
TEST_FX_CUT = 0x04
TEST_FX_ARP = 0x05
TEST_FX_DEL = 0x06

class TestM8FXTuple(unittest.TestCase):
    def test_read_from_binary(self):
        # Test case 1: Regular data 
        test_data = bytes([TEST_FX_VOL, 20])  # key=VOL, value=20
        fx_tuple = M8FXTuple.read(test_data)
        
        # Should return the integer enum value for the key
        self.assertEqual(fx_tuple.key, TEST_FX_VOL)
        self.assertEqual(fx_tuple.value, 20)
        
        # Test case 2: Empty tuple
        test_data = bytes([EMPTY_KEY, 0])
        fx_tuple = M8FXTuple.read(test_data)

        self.assertEqual(fx_tuple.key, EMPTY_KEY)
        self.assertEqual(fx_tuple.value, 0)
        
        # Test case 3: Extra data (should only read first 2 bytes)
        test_data = bytes([TEST_FX_ARP, 30, 40, 50])
        fx_tuple = M8FXTuple.read(test_data)
        
        self.assertEqual(fx_tuple.key, TEST_FX_ARP)
        self.assertEqual(fx_tuple.value, 30)
    
    def test_write_to_binary(self):
        # Test case 1: Regular tuple with enum value
        fx_tuple = M8FXTuple(key=TEST_FX_VOL, value=10)
        binary = fx_tuple.write()
        
        self.assertEqual(len(binary), BLOCK_SIZE)
        self.assertEqual(binary, bytes([TEST_FX_VOL, 10]))
        
        # Test case 2: Empty tuple
        fx_tuple = M8FXTuple()  # Default is empty
        binary = fx_tuple.write()

        self.assertEqual(binary, bytes([EMPTY_KEY, DEFAULT_VALUE]))
    
    def test_read_write_consistency(self):
        # Test binary serialization/deserialization consistency with enum values
        test_cases = [
            (TEST_FX_VOL, 20),  # WavSynth FX
            (TEST_FX_ARP, 30),  # Sequencer FX
            (EMPTY_KEY, 0),  # Empty tuple
            (0, 40)  # Numeric key
        ]
        
        for key, value in test_cases:
            # Create an FX tuple
            original = M8FXTuple(key=key, value=value)
            
            # Write to binary
            binary = original.write()
            
            # Read from binary
            deserialized = M8FXTuple.read(binary)
            
            # Compare attributes - both should have integer enum values
            self.assertEqual(deserialized.key, original.key)
            self.assertEqual(deserialized.value, original.value)
    
    def test_constructor_and_defaults(self):
        # Test default constructor
        fx_tuple = M8FXTuple()
        self.assertEqual(fx_tuple.key, EMPTY_KEY)
        self.assertEqual(fx_tuple.value, DEFAULT_VALUE)
        
        # Test with enum value parameters
        fx_tuple = M8FXTuple(key=TEST_FX_VOL, value=20)
        self.assertEqual(fx_tuple.key, TEST_FX_VOL)
        self.assertEqual(fx_tuple.value, 20)
        
        # Test with numeric parameters
        fx_tuple = M8FXTuple(key=5, value=25)
        self.assertEqual(fx_tuple.key, 5)
        self.assertEqual(fx_tuple.value, 25)
    
    def test_property_accessors(self):
        # Test property getters and setters
        fx_tuple = M8FXTuple()
        
        # Test setters with enum value
        fx_tuple.key = TEST_FX_VOL
        fx_tuple.value = 25
        
        # Test getters
        self.assertEqual(fx_tuple.key, TEST_FX_VOL)
        self.assertEqual(fx_tuple.value, 25)
        
        # Test with numeric values
        fx_tuple.key = TEST_FX_PAN
        self.assertEqual(fx_tuple.key, TEST_FX_PAN)
    


class TestM8FXTuples(unittest.TestCase):
    def test_read_from_binary(self):
        # Create test binary data for M8FXTuples
        test_data = bytearray()
        
        # Tuple 0: key=VOL, value=20
        test_data.extend([TEST_FX_VOL, 20])
        
        # Tuple 1: empty
        test_data.extend([EMPTY_KEY, 0])
        
        # Tuple 2: key=ARP (sequencer FX), value=40
        test_data.extend([TEST_FX_ARP, 40])
        
        # Read from binary
        fx_tuples = M8FXTuples.read(test_data)
        
        # Verify specific tuples - should have integer enum values
        self.assertEqual(fx_tuples[0].key, TEST_FX_VOL)
        self.assertEqual(fx_tuples[0].value, 20)
        
        self.assertEqual(fx_tuples[1].key, EMPTY_KEY)
        self.assertEqual(fx_tuples[1].value, 0)
        
        self.assertEqual(fx_tuples[2].key, TEST_FX_ARP)
        self.assertEqual(fx_tuples[2].value, 40)
        
        # Verify number of tuples
        self.assertEqual(len(fx_tuples), BLOCK_COUNT)
    
    def test_write_to_binary(self):
        # Create M8FXTuples with some data
        fx_tuples = M8FXTuples()
        
        # Set up tuples with enum values
        fx_tuples[0] = M8FXTuple(key=TEST_FX_VOL, value=20)
        fx_tuples[2] = M8FXTuple(key=TEST_FX_ARP, value=40)
        
        # Write to binary
        binary = fx_tuples.write()
        
        # Verify size
        self.assertEqual(len(binary), BLOCK_COUNT * BLOCK_SIZE)
        
        # Verify specific bytes for tuples
        self.assertEqual(binary[0], TEST_FX_VOL)  # Tuple 0 key
        self.assertEqual(binary[1], 20)                     # Tuple 0 value
        
        self.assertEqual(binary[2], EMPTY_KEY)    # Tuple 1 key (empty)
        self.assertEqual(binary[3], 0)                      # Tuple 1 value
        
        self.assertEqual(binary[4], TEST_FX_ARP)  # Tuple 2 key
        self.assertEqual(binary[5], 40)                     # Tuple 2 value
    
    def test_read_write_consistency(self):
        # Create M8FXTuples with some data using enum values
        fx_tuples = M8FXTuples()
        
        # Set up tuples
        fx_tuples[0] = M8FXTuple(key=TEST_FX_VOL, value=20)
        fx_tuples[2] = M8FXTuple(key=TEST_FX_ARP, value=40)
        
        # Write to binary
        binary = fx_tuples.write()
        
        # Read back from binary
        deserialized = M8FXTuples.read(binary)
        
        # Verify all tuples match
        for i in range(BLOCK_COUNT):
            self.assertEqual(deserialized[i].key, fx_tuples[i].key)
            self.assertEqual(deserialized[i].value, fx_tuples[i].value)
    
    def test_constructor(self):
        # Test default constructor
        fx_tuples = M8FXTuples()
        
        # Should have BLOCK_COUNT tuples
        self.assertEqual(len(fx_tuples), BLOCK_COUNT)

        # All tuples should have empty key by default
        for fx_tuple in fx_tuples:
            self.assertEqual(fx_tuple.key, EMPTY_KEY)
    


    def test_clone(self):
        # Test clone method
        original = M8FXTuples()
        original[0] = M8FXTuple(key=TEST_FX_VOL, value=20)
        original[2] = M8FXTuple(key=TEST_FX_ARP, value=40)
        
        clone = original.clone()
        
        # Verify clone has the same values
        for i in range(BLOCK_COUNT):
            self.assertEqual(clone[i].key, original[i].key)
            self.assertEqual(clone[i].value, original[i].value)
        
        # Verify clone is a different object
        self.assertIsNot(clone, original)
        
        # Modify clone and verify original remains unchanged
        clone[0].key = TEST_FX_CUT
        clone[0].value = 60
        self.assertEqual(original[0].key, TEST_FX_VOL)
        self.assertEqual(original[0].value, 20)

if __name__ == '__main__':
    unittest.main()