import unittest
from m8.api.fx import M8FXTuple, M8FXTuples, BLOCK_SIZE, BLOCK_COUNT
from m8.enums import M8InstrumentType
from m8.enums import M8SequencerFX
from m8.enums.wavsynth import M8WavSynthFX

class TestM8FXTuple(unittest.TestCase):
    def test_read_from_binary(self):
        # Test case 1: Regular data with instrument type
        test_data = bytes([M8WavSynthFX.VOL.value, 20])  # key=VOL, value=20
        fx_tuple = M8FXTuple.read(test_data, instrument_type=M8InstrumentType.WAVSYNTH)
        
        # Should return the string enum name for the key
        self.assertEqual(fx_tuple.key, "VOL")
        self.assertEqual(fx_tuple.value, 20)
        
        # Test case 2: Empty tuple
        test_data = bytes([M8FXTuple.EMPTY_KEY, 0])
        fx_tuple = M8FXTuple.read(test_data, instrument_type=M8InstrumentType.WAVSYNTH)
        
        self.assertEqual(fx_tuple.key, M8FXTuple.EMPTY_KEY)
        self.assertEqual(fx_tuple.value, 0)
        self.assertTrue(fx_tuple.is_empty())
        
        # Test case 3: Extra data (should only read first 2 bytes)
        test_data = bytes([M8SequencerFX.ARP.value, 30, 40, 50])
        fx_tuple = M8FXTuple.read(test_data, instrument_type=M8InstrumentType.WAVSYNTH)
        
        self.assertEqual(fx_tuple.key, "ARP")
        self.assertEqual(fx_tuple.value, 30)
    
    def test_write_to_binary(self):
        # Test case 1: Regular tuple with string enum
        fx_tuple = M8FXTuple(key="VOL", value=10, instrument_type=M8InstrumentType.WAVSYNTH)
        binary = fx_tuple.write()
        
        self.assertEqual(len(binary), BLOCK_SIZE)
        self.assertEqual(binary, bytes([M8WavSynthFX.VOL.value, 10]))
        
        # Test case 2: Empty tuple
        fx_tuple = M8FXTuple(instrument_type=M8InstrumentType.WAVSYNTH)  # Default is empty
        binary = fx_tuple.write()
        
        self.assertEqual(binary, bytes([M8FXTuple.EMPTY_KEY, M8FXTuple.DEFAULT_VALUE]))
    
    def test_read_write_consistency(self):
        # Test binary serialization/deserialization consistency with enum values
        test_cases = [
            ("VOL", 20),  # WavSynth FX
            ("ARP", 30),  # Sequencer FX
            (M8FXTuple.EMPTY_KEY, 0),  # Empty tuple
            (0, 40)  # Numeric key
        ]
        
        for key, value in test_cases:
            # Create an FX tuple
            original = M8FXTuple(key=key, value=value, instrument_type=M8InstrumentType.WAVSYNTH)
            
            # Write to binary
            binary = original.write()
            
            # Read from binary
            deserialized = M8FXTuple.read(binary, instrument_type=M8InstrumentType.WAVSYNTH)
            
            # Compare attributes - both should have string enum keys where applicable
            self.assertEqual(deserialized.key, original.key)
            self.assertEqual(deserialized.value, original.value)
    
    def test_constructor_and_defaults(self):
        # Test default constructor
        fx_tuple = M8FXTuple()
        self.assertEqual(fx_tuple.key, M8FXTuple.EMPTY_KEY)
        self.assertEqual(fx_tuple.value, M8FXTuple.DEFAULT_VALUE)
        
        # Test with string enum parameters
        fx_tuple = M8FXTuple(key="VOL", value=20, instrument_type=M8InstrumentType.WAVSYNTH)
        self.assertEqual(fx_tuple.key, "VOL")
        self.assertEqual(fx_tuple.value, 20)
        
        # Test with numeric parameters
        fx_tuple = M8FXTuple(key=5, value=25)
        self.assertEqual(fx_tuple.key, 5)
        self.assertEqual(fx_tuple.value, 25)
    
    def test_property_accessors(self):
        # Test property getters and setters
        fx_tuple = M8FXTuple(instrument_type=M8InstrumentType.WAVSYNTH)
        
        # Test setters with string enum
        fx_tuple.key = "VOL"
        fx_tuple.value = 25
        
        # Test getters
        self.assertEqual(fx_tuple.key, "VOL")
        self.assertEqual(fx_tuple.value, 25)
        
        # Test with numeric values
        fx_tuple.key = M8WavSynthFX.PAN.value
        self.assertEqual(fx_tuple.key, "PAN")
    
    def test_is_empty(self):
        # Test is_empty method
        fx_tuple = M8FXTuple(instrument_type=M8InstrumentType.WAVSYNTH)
        self.assertTrue(fx_tuple.is_empty())
        
        fx_tuple.key = "VOL"
        self.assertFalse(fx_tuple.is_empty())
        
        fx_tuple.key = M8FXTuple.EMPTY_KEY
        self.assertTrue(fx_tuple.is_empty())
        
        # Value shouldn't affect emptiness
        fx_tuple.value = 50
        self.assertTrue(fx_tuple.is_empty())
        
    def test_is_complete(self):
        # Test is_complete method
        fx_tuple = M8FXTuple(instrument_type=M8InstrumentType.WAVSYNTH)
        # Empty tuple is not complete because key isn't set
        self.assertFalse(fx_tuple.is_complete())
        
        # Tuple with key set is complete
        fx_tuple.key = "VOL"
        self.assertTrue(fx_tuple.is_complete())
        
        # Tuple is complete regardless of value
        fx_tuple.value = 0
        self.assertTrue(fx_tuple.is_complete())
        fx_tuple.value = 50
        self.assertTrue(fx_tuple.is_complete())
    
    def test_as_dict(self):
        # Test as_dict method with enum values
        fx_tuple = M8FXTuple(key="VOL", value=20, instrument_type=M8InstrumentType.WAVSYNTH)
        result = fx_tuple.as_dict()
        
        expected = {
            "key": "VOL",  # Should be string enum name
            "value": 20
        }
        
        self.assertEqual(result, expected)
    
    def test_from_dict(self):
        # Test from_dict method with string enum values
        data = {
            "key": "VOL",
            "value": 25
        }
        
        fx_tuple = M8FXTuple.from_dict(data, instrument_type=M8InstrumentType.WAVSYNTH)
        
        self.assertEqual(fx_tuple.key, "VOL")
        self.assertEqual(fx_tuple.value, 25)
        
        # Test dict/object round trip
        original = M8FXTuple(key="DEL", value=40, instrument_type=M8InstrumentType.WAVSYNTH)
        dict_data = original.as_dict()
        roundtrip = M8FXTuple.from_dict(dict_data, instrument_type=M8InstrumentType.WAVSYNTH)
        
        self.assertEqual(roundtrip.key, original.key)
        self.assertEqual(roundtrip.value, original.value)


class TestM8FXTuples(unittest.TestCase):
    def test_read_from_binary(self):
        # Create test binary data for M8FXTuples
        test_data = bytearray()
        
        # Tuple 0: key=VOL, value=20
        test_data.extend([M8WavSynthFX.VOL.value, 20])
        
        # Tuple 1: empty
        test_data.extend([M8FXTuple.EMPTY_KEY, 0])
        
        # Tuple 2: key=ARP (sequencer FX), value=40
        test_data.extend([M8SequencerFX.ARP.value, 40])
        
        # Read from binary with instrument type
        fx_tuples = M8FXTuples.read(test_data, instrument_type=M8InstrumentType.WAVSYNTH)
        
        # Verify specific tuples
        self.assertEqual(fx_tuples[0].key, "VOL")
        self.assertEqual(fx_tuples[0].value, 20)
        
        self.assertEqual(fx_tuples[1].key, M8FXTuple.EMPTY_KEY)
        self.assertEqual(fx_tuples[1].value, 0)
        self.assertTrue(fx_tuples[1].is_empty())
        
        self.assertEqual(fx_tuples[2].key, "ARP")
        self.assertEqual(fx_tuples[2].value, 40)
        
        # Verify number of tuples
        self.assertEqual(len(fx_tuples), BLOCK_COUNT)
    
    def test_write_to_binary(self):
        # Create M8FXTuples with some data
        fx_tuples = M8FXTuples(instrument_type=M8InstrumentType.WAVSYNTH)
        
        # Set up tuples
        fx_tuples[0] = M8FXTuple(key="VOL", value=20, instrument_type=M8InstrumentType.WAVSYNTH)
        fx_tuples[2] = M8FXTuple(key="ARP", value=40, instrument_type=M8InstrumentType.WAVSYNTH)
        
        # Write to binary
        binary = fx_tuples.write()
        
        # Verify size
        self.assertEqual(len(binary), BLOCK_COUNT * BLOCK_SIZE)
        
        # Verify specific bytes for tuples
        self.assertEqual(binary[0], M8WavSynthFX.VOL.value)  # Tuple 0 key
        self.assertEqual(binary[1], 20)                     # Tuple 0 value
        
        self.assertEqual(binary[2], M8FXTuple.EMPTY_KEY)    # Tuple 1 key (empty)
        self.assertEqual(binary[3], 0)                      # Tuple 1 value
        
        self.assertEqual(binary[4], M8SequencerFX.ARP.value)  # Tuple 2 key
        self.assertEqual(binary[5], 40)                     # Tuple 2 value
    
    def test_read_write_consistency(self):
        # Create M8FXTuples with some data using string enum values
        fx_tuples = M8FXTuples(instrument_type=M8InstrumentType.WAVSYNTH)
        
        # Set up tuples
        fx_tuples[0] = M8FXTuple(key="VOL", value=20, instrument_type=M8InstrumentType.WAVSYNTH)
        fx_tuples[2] = M8FXTuple(key="ARP", value=40, instrument_type=M8InstrumentType.WAVSYNTH)
        
        # Write to binary
        binary = fx_tuples.write()
        
        # Read back from binary
        deserialized = M8FXTuples.read(binary, instrument_type=M8InstrumentType.WAVSYNTH)
        
        # Verify all tuples match
        for i in range(BLOCK_COUNT):
            self.assertEqual(deserialized[i].key, fx_tuples[i].key)
            self.assertEqual(deserialized[i].value, fx_tuples[i].value)
    
    def test_constructor(self):
        # Test default constructor
        fx_tuples = M8FXTuples(instrument_type=M8InstrumentType.WAVSYNTH)
        
        # Should have BLOCK_COUNT tuples
        self.assertEqual(len(fx_tuples), BLOCK_COUNT)
        
        # All tuples should be empty
        for fx_tuple in fx_tuples:
            self.assertTrue(fx_tuple.is_empty())
    
    def test_is_empty(self):
        # Test is_empty method
        fx_tuples = M8FXTuples(instrument_type=M8InstrumentType.WAVSYNTH)
        self.assertTrue(fx_tuples.is_empty())
        
        # Modify one tuple
        fx_tuples[0] = M8FXTuple(key="VOL", value=20, instrument_type=M8InstrumentType.WAVSYNTH)
        self.assertFalse(fx_tuples.is_empty())
        
        # Reset to empty
        fx_tuples[0] = M8FXTuple(instrument_type=M8InstrumentType.WAVSYNTH)
        self.assertTrue(fx_tuples.is_empty())
        
    def test_is_complete(self):
        # Create a custom test class that inherits from M8FXTuple but overrides is_complete
        class MockIncompleteM8FXTuple(M8FXTuple):
            def is_empty(self):
                return False  # Always non-empty
                
            def is_complete(self):
                return False  # Always incomplete
        
        # Test the normal case first
        fx_tuples = M8FXTuples(instrument_type=M8InstrumentType.WAVSYNTH)
        # Empty tuples collection is complete since there are no non-empty tuples
        self.assertTrue(fx_tuples.is_complete())
        
        # Add a complete tuple (with key)
        fx_tuples[0] = M8FXTuple(key="VOL", value=20, instrument_type=M8InstrumentType.WAVSYNTH)
        self.assertTrue(fx_tuples.is_complete())
        
        # Test with our mock incomplete tuple
        fx_tuples = M8FXTuples(instrument_type=M8InstrumentType.WAVSYNTH)
        fx_tuples[0] = MockIncompleteM8FXTuple()
        
        # Now verify the collection is incomplete
        self.assertFalse(fx_tuples.is_complete())
    
    def test_clone(self):
        # Test clone method
        original = M8FXTuples(instrument_type=M8InstrumentType.WAVSYNTH)
        original[0] = M8FXTuple(key="VOL", value=20, instrument_type=M8InstrumentType.WAVSYNTH)
        original[2] = M8FXTuple(key="ARP", value=40, instrument_type=M8InstrumentType.WAVSYNTH)
        
        clone = original.clone()
        
        # Verify clone has the same values
        for i in range(BLOCK_COUNT):
            self.assertEqual(clone[i].key, original[i].key)
            self.assertEqual(clone[i].value, original[i].value)
        
        # Verify clone is a different object
        self.assertIsNot(clone, original)
        
        # Modify clone and verify original remains unchanged
        clone[0].key = "CUT"
        clone[0].value = 60
        self.assertEqual(original[0].key, "VOL")
        self.assertEqual(original[0].value, 20)
    
    def test_as_list(self):
        # Test as_list method with enum values
        fx_tuples = M8FXTuples(instrument_type=M8InstrumentType.WAVSYNTH)
        
        # Add some tuples
        fx_tuples[0] = M8FXTuple(key="VOL", value=20, instrument_type=M8InstrumentType.WAVSYNTH)
        fx_tuples[2] = M8FXTuple(key="ARP", value=40, instrument_type=M8InstrumentType.WAVSYNTH)
        
        result = fx_tuples.as_list()
        
        # Should only contain non-empty tuples
        self.assertEqual(len(result), 2)
        
        # Check specific tuples
        tuple0 = next(t for t in result if t["index"] == 0)
        self.assertEqual(tuple0["key"], "VOL")
        self.assertEqual(tuple0["value"], 20)
        
        tuple2 = next(t for t in result if t["index"] == 2)
        self.assertEqual(tuple2["key"], "ARP")
        self.assertEqual(tuple2["value"], 40)
        
        # Test empty tuples
        fx_tuples = M8FXTuples(instrument_type=M8InstrumentType.WAVSYNTH)
        result = fx_tuples.as_list()
        self.assertEqual(result, [])
    
    def test_from_list(self):
        # Test from_list method with string enum values
        data = [
            {"index": 0, "key": "VOL", "value": 20},
            {"index": 2, "key": "ARP", "value": 40}
        ]
        
        fx_tuples = M8FXTuples.from_list(data, instrument_type=M8InstrumentType.WAVSYNTH)
        
        # Check specific tuples
        self.assertEqual(fx_tuples[0].key, "VOL")
        self.assertEqual(fx_tuples[0].value, 20)
        
        self.assertTrue(fx_tuples[1].is_empty())
        
        self.assertEqual(fx_tuples[2].key, "ARP")
        self.assertEqual(fx_tuples[2].value, 40)
        
        # Test with invalid index
        data = [
            {"index": BLOCK_COUNT + 5, "key": "VOL", "value": 60}  # Out of range
        ]
        
        fx_tuples = M8FXTuples.from_list(data, instrument_type=M8InstrumentType.WAVSYNTH)
        self.assertTrue(fx_tuples.is_empty())
        
        # Test with empty list
        fx_tuples = M8FXTuples.from_list([], instrument_type=M8InstrumentType.WAVSYNTH)
        self.assertTrue(fx_tuples.is_empty())
        
        # Verify number of tuples is correct
        self.assertEqual(len(fx_tuples), BLOCK_COUNT)

if __name__ == '__main__':
    unittest.main()