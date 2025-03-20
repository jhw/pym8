import unittest
from m8.api.fx import M8FXTuple, M8FXTuples, BLOCK_SIZE, BLOCK_COUNT

class TestM8FXTuple(unittest.TestCase):
    def test_read_from_binary(self):
        # Test case 1: Regular data
        test_data = bytes([10, 20])  # key=10, value=20
        fx_tuple = M8FXTuple.read(test_data)
        
        self.assertEqual(fx_tuple.key, 10)
        self.assertEqual(fx_tuple.value, 20)
        
        # Test case 2: Empty tuple
        test_data = bytes([M8FXTuple.EMPTY_KEY, 0])
        fx_tuple = M8FXTuple.read(test_data)
        
        self.assertEqual(fx_tuple.key, M8FXTuple.EMPTY_KEY)
        self.assertEqual(fx_tuple.value, 0)
        self.assertTrue(fx_tuple.is_empty())
        
        # Test case 3: Extra data (should only read first 2 bytes)
        test_data = bytes([20, 30, 40, 50])
        fx_tuple = M8FXTuple.read(test_data)
        
        self.assertEqual(fx_tuple.key, 20)
        self.assertEqual(fx_tuple.value, 30)
    
    def test_write_to_binary(self):
        # Test case 1: Regular tuple
        fx_tuple = M8FXTuple(key=5, value=10)
        binary = fx_tuple.write()
        
        self.assertEqual(len(binary), BLOCK_SIZE)
        self.assertEqual(binary, bytes([5, 10]))
        
        # Test case 2: Empty tuple
        fx_tuple = M8FXTuple()  # Default is empty
        binary = fx_tuple.write()
        
        self.assertEqual(binary, bytes([M8FXTuple.EMPTY_KEY, M8FXTuple.DEFAULT_VALUE]))
    
    def test_read_write_consistency(self):
        # Test binary serialization/deserialization consistency
        test_cases = [
            (10, 20),  # Regular values
            (M8FXTuple.EMPTY_KEY, 0),  # Empty tuple
            (0, 30),  # Zero key
            (100, 200)  # Large values
        ]
        
        for key, value in test_cases:
            # Create an FX tuple
            original = M8FXTuple(key=key, value=value)
            
            # Write to binary
            binary = original.write()
            
            # Read from binary
            deserialized = M8FXTuple.read(binary)
            
            # Compare attributes
            self.assertEqual(deserialized.key, original.key)
            self.assertEqual(deserialized.value, original.value)
    
    def test_constructor_and_defaults(self):
        # Test default constructor
        fx_tuple = M8FXTuple()
        self.assertEqual(fx_tuple.key, M8FXTuple.EMPTY_KEY)
        self.assertEqual(fx_tuple.value, M8FXTuple.DEFAULT_VALUE)
        
        # Test with parameters
        fx_tuple = M8FXTuple(key=10, value=20)
        self.assertEqual(fx_tuple.key, 10)
        self.assertEqual(fx_tuple.value, 20)
        
        # Test with partial parameters
        fx_tuple = M8FXTuple(key=5)
        self.assertEqual(fx_tuple.key, 5)
        self.assertEqual(fx_tuple.value, M8FXTuple.DEFAULT_VALUE)
    
    def test_property_accessors(self):
        # Test property getters and setters
        fx_tuple = M8FXTuple()
        
        # Test setters
        fx_tuple.key = 15
        fx_tuple.value = 25
        
        # Test getters
        self.assertEqual(fx_tuple.key, 15)
        self.assertEqual(fx_tuple.value, 25)
    
    def test_is_empty(self):
        # Test is_empty method
        fx_tuple = M8FXTuple()
        self.assertTrue(fx_tuple.is_empty())
        
        fx_tuple.key = 10
        self.assertFalse(fx_tuple.is_empty())
        
        fx_tuple.key = M8FXTuple.EMPTY_KEY
        self.assertTrue(fx_tuple.is_empty())
        
        # Value shouldn't affect emptiness
        fx_tuple.value = 50
        self.assertTrue(fx_tuple.is_empty())
    
    def test_as_dict(self):
        # Test as_dict method
        fx_tuple = M8FXTuple(key=10, value=20)
        result = fx_tuple.as_dict()
        
        expected = {
            "key": 10,
            "value": 20
        }
        
        self.assertEqual(result, expected)
    
    def test_from_dict(self):
        # Test from_dict method
        data = {
            "key": 15,
            "value": 25
        }
        
        fx_tuple = M8FXTuple.from_dict(data)
        
        self.assertEqual(fx_tuple.key, 15)
        self.assertEqual(fx_tuple.value, 25)
        
        # Test dict/object round trip
        original = M8FXTuple(key=30, value=40)
        dict_data = original.as_dict()
        roundtrip = M8FXTuple.from_dict(dict_data)
        
        self.assertEqual(roundtrip.key, original.key)
        self.assertEqual(roundtrip.value, original.value)


class TestM8FXTuples(unittest.TestCase):
    def test_read_from_binary(self):
        # Create test binary data for M8FXTuples
        test_data = bytearray()
        
        # Tuple 0: key=10, value=20
        test_data.extend([10, 20])
        
        # Tuple 1: empty
        test_data.extend([M8FXTuple.EMPTY_KEY, 0])
        
        # Tuple 2: key=30, value=40
        test_data.extend([30, 40])
        
        # Read from binary
        fx_tuples = M8FXTuples.read(test_data)
        
        # Verify specific tuples
        self.assertEqual(fx_tuples[0].key, 10)
        self.assertEqual(fx_tuples[0].value, 20)
        
        self.assertEqual(fx_tuples[1].key, M8FXTuple.EMPTY_KEY)
        self.assertEqual(fx_tuples[1].value, 0)
        self.assertTrue(fx_tuples[1].is_empty())
        
        self.assertEqual(fx_tuples[2].key, 30)
        self.assertEqual(fx_tuples[2].value, 40)
        
        # Verify number of tuples
        self.assertEqual(len(fx_tuples), BLOCK_COUNT)
    
    def test_write_to_binary(self):
        # Create M8FXTuples with some data
        fx_tuples = M8FXTuples()
        
        # Set up tuples
        fx_tuples[0] = M8FXTuple(key=10, value=20)
        fx_tuples[2] = M8FXTuple(key=30, value=40)
        
        # Write to binary
        binary = fx_tuples.write()
        
        # Verify size
        self.assertEqual(len(binary), BLOCK_COUNT * BLOCK_SIZE)
        
        # Verify specific bytes for tuples
        self.assertEqual(binary[0], 10)  # Tuple 0 key
        self.assertEqual(binary[1], 20)  # Tuple 0 value
        
        self.assertEqual(binary[2], M8FXTuple.EMPTY_KEY)  # Tuple 1 key (empty)
        self.assertEqual(binary[3], 0)                    # Tuple 1 value
        
        self.assertEqual(binary[4], 30)  # Tuple 2 key
        self.assertEqual(binary[5], 40)  # Tuple 2 value
    
    def test_read_write_consistency(self):
        # Create M8FXTuples with some data
        fx_tuples = M8FXTuples()
        
        # Set up tuples
        fx_tuples[0] = M8FXTuple(key=10, value=20)
        fx_tuples[2] = M8FXTuple(key=30, value=40)
        
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
        
        # All tuples should be empty
        for fx_tuple in fx_tuples:
            self.assertTrue(fx_tuple.is_empty())
    
    def test_is_empty(self):
        # Test is_empty method
        fx_tuples = M8FXTuples()
        self.assertTrue(fx_tuples.is_empty())
        
        # Modify one tuple
        fx_tuples[0] = M8FXTuple(key=10, value=20)
        self.assertFalse(fx_tuples.is_empty())
        
        # Reset to empty
        fx_tuples[0] = M8FXTuple()
        self.assertTrue(fx_tuples.is_empty())
    
    def test_clone(self):
        # Test clone method
        original = M8FXTuples()
        original[0] = M8FXTuple(key=10, value=20)
        original[2] = M8FXTuple(key=30, value=40)
        
        clone = original.clone()
        
        # Verify clone has the same values
        for i in range(BLOCK_COUNT):
            self.assertEqual(clone[i].key, original[i].key)
            self.assertEqual(clone[i].value, original[i].value)
        
        # Verify clone is a different object
        self.assertIsNot(clone, original)
        
        # Modify clone and verify original remains unchanged
        clone[0].key = 50
        clone[0].value = 60
        self.assertEqual(original[0].key, 10)
        self.assertEqual(original[0].value, 20)
    
    def test_as_list(self):
        # Test as_list method
        fx_tuples = M8FXTuples()
        
        # Add some tuples
        fx_tuples[0] = M8FXTuple(key=10, value=20)
        fx_tuples[2] = M8FXTuple(key=30, value=40)
        
        result = fx_tuples.as_list()
        
        # Should only contain non-empty tuples
        self.assertEqual(len(result), 2)
        
        # Check specific tuples
        tuple0 = next(t for t in result if t["index"] == 0)
        self.assertEqual(tuple0["key"], 10)
        self.assertEqual(tuple0["value"], 20)
        
        tuple2 = next(t for t in result if t["index"] == 2)
        self.assertEqual(tuple2["key"], 30)
        self.assertEqual(tuple2["value"], 40)
        
        # Test empty tuples
        fx_tuples = M8FXTuples()
        result = fx_tuples.as_list()
        self.assertEqual(result, [])
    
    def test_from_list(self):
        # Test from_list method
        data = [
            {"index": 0, "key": 10, "value": 20},
            {"index": 2, "key": 30, "value": 40}
        ]
        
        fx_tuples = M8FXTuples.from_list(data)
        
        # Check specific tuples
        self.assertEqual(fx_tuples[0].key, 10)
        self.assertEqual(fx_tuples[0].value, 20)
        
        self.assertTrue(fx_tuples[1].is_empty())
        
        self.assertEqual(fx_tuples[2].key, 30)
        self.assertEqual(fx_tuples[2].value, 40)
        
        # Test with invalid index
        data = [
            {"index": BLOCK_COUNT + 5, "key": 50, "value": 60}  # Out of range
        ]
        
        fx_tuples = M8FXTuples.from_list(data)
        self.assertTrue(fx_tuples.is_empty())
        
        # Test with empty list
        fx_tuples = M8FXTuples.from_list([])
        self.assertTrue(fx_tuples.is_empty())
        
        # Verify number of tuples is correct
        self.assertEqual(len(fx_tuples), BLOCK_COUNT)

if __name__ == '__main__':
    unittest.main()