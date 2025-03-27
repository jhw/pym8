import unittest
from m8.api.chains import (
    M8ChainStep, M8Chain, M8Chains,
    STEP_BLOCK_SIZE, STEP_COUNT, CHAIN_BLOCK_SIZE, CHAIN_COUNT
)
from m8.api import M8ValidationResult

class TestM8ChainStep(unittest.TestCase):
    def test_read_from_binary(self):
        # Test case 1: Regular data
        test_data = bytes([10, 5])  # phrase=10, transpose=5
        step = M8ChainStep.read(test_data)
        
        self.assertEqual(step.phrase, 10)
        self.assertEqual(step.transpose, 5)
        
        # Test case 2: Empty step
        test_data = bytes([M8ChainStep.EMPTY_PHRASE, 0])
        step = M8ChainStep.read(test_data)
        
        self.assertEqual(step.phrase, M8ChainStep.EMPTY_PHRASE)
        self.assertEqual(step.transpose, 0)
        self.assertTrue(step.is_empty())
        
        # Test case 3: Extra data (should only read first 2 bytes)
        test_data = bytes([20, 10, 30, 40])
        step = M8ChainStep.read(test_data)
        
        self.assertEqual(step.phrase, 20)
        self.assertEqual(step.transpose, 10)
    
    def test_write_to_binary(self):
        # Test case 1: Regular step
        step = M8ChainStep(phrase=15, transpose=7)
        binary = step.write()
        
        self.assertEqual(len(binary), STEP_BLOCK_SIZE)
        self.assertEqual(binary, bytes([15, 7]))
        
        # Test case 2: Empty step
        step = M8ChainStep()  # Default should be empty
        binary = step.write()
        
        self.assertEqual(binary, bytes([M8ChainStep.EMPTY_PHRASE, M8ChainStep.DEFAULT_TRANSPOSE]))
    
    def test_read_write_consistency(self):
        # Test binary serialization/deserialization consistency
        test_cases = [
            (10, 5),  # Regular values
            (M8ChainStep.EMPTY_PHRASE, 0),  # Empty step
            (0, 20),  # Zero phrase
            (100, 10)  # Large phrase number
        ]
        
        for phrase, transpose in test_cases:
            # Create a step
            original = M8ChainStep(phrase=phrase, transpose=transpose)
            
            # Write to binary
            binary = original.write()
            
            # Read from binary
            deserialized = M8ChainStep.read(binary)
            
            # Compare attributes
            self.assertEqual(deserialized.phrase, original.phrase)
            self.assertEqual(deserialized.transpose, original.transpose)
    
    def test_constructor_and_defaults(self):
        # Test default constructor
        step = M8ChainStep()
        self.assertEqual(step.phrase, M8ChainStep.EMPTY_PHRASE)
        self.assertEqual(step.transpose, M8ChainStep.DEFAULT_TRANSPOSE)
        
        # Test with parameters
        step = M8ChainStep(phrase=10, transpose=5)
        self.assertEqual(step.phrase, 10)
        self.assertEqual(step.transpose, 5)
        
        # Test with partial parameters
        step = M8ChainStep(phrase=20)
        self.assertEqual(step.phrase, 20)
        self.assertEqual(step.transpose, M8ChainStep.DEFAULT_TRANSPOSE)
    
    def test_property_accessors(self):
        # Test property getters and setters
        step = M8ChainStep()
        
        # Test setters
        step.phrase = 25
        step.transpose = 10
        
        # Test getters
        self.assertEqual(step.phrase, 25)
        self.assertEqual(step.transpose, 10)
    
    def test_is_empty(self):
        # Test is_empty method
        step = M8ChainStep()
        self.assertTrue(step.is_empty())
        
        step.phrase = 10
        self.assertFalse(step.is_empty())
        
        step.phrase = M8ChainStep.EMPTY_PHRASE
        self.assertTrue(step.is_empty())
    
    def test_as_dict(self):
        # Test as_dict method
        step = M8ChainStep(phrase=10, transpose=5)
        result = step.as_dict()
        
        expected = {
            "phrase": 10,
            "transpose": 5
        }
        
        self.assertEqual(result, expected)
    
    def test_from_dict(self):
        # Test from_dict method
        data = {
            "phrase": 20,
            "transpose": 15
        }
        
        step = M8ChainStep.from_dict(data)
        
        self.assertEqual(step.phrase, 20)
        self.assertEqual(step.transpose, 15)
        
        # Test dict/object round trip
        original = M8ChainStep(phrase=30, transpose=10)
        dict_data = original.as_dict()
        roundtrip = M8ChainStep.from_dict(dict_data)
        
        self.assertEqual(roundtrip.phrase, original.phrase)
        self.assertEqual(roundtrip.transpose, original.transpose)
    
    def test_clone(self):
        # Test clone method
        original = M8ChainStep(phrase=25, transpose=7)
        clone = original.clone()
        
        # Verify clone has the same values
        self.assertEqual(clone.phrase, original.phrase)
        self.assertEqual(clone.transpose, original.transpose)
        
        # Verify clone is a different object
        self.assertIsNot(clone, original)
        
        # Modify clone and verify original remains unchanged
        clone.phrase = 30
        clone.transpose = 12
        self.assertEqual(original.phrase, 25)
        self.assertEqual(original.transpose, 7)


class TestM8Chain(unittest.TestCase):
    def test_read_from_binary(self):
        # Create test binary data for a chain with some steps
        test_data = bytearray()
        
        # Step 0: phrase=10, transpose=5
        test_data.extend([10, 5])
        
        # Step 1: empty
        test_data.extend([M8ChainStep.EMPTY_PHRASE, 0])
        
        # Step 2: phrase=20, transpose=10
        test_data.extend([20, 10])
        
        # Fill remaining steps with empty data
        for _ in range(STEP_COUNT - 3):
            test_data.extend([M8ChainStep.EMPTY_PHRASE, 0])
        
        # Read from binary
        chain = M8Chain.read(test_data)
        
        # Verify specific steps
        self.assertEqual(chain[0].phrase, 10)
        self.assertEqual(chain[0].transpose, 5)
        
        self.assertEqual(chain[1].phrase, M8ChainStep.EMPTY_PHRASE)
        self.assertEqual(chain[1].transpose, 0)
        
        self.assertEqual(chain[2].phrase, 20)
        self.assertEqual(chain[2].transpose, 10)
        
        # Verify number of steps
        self.assertEqual(len(chain), STEP_COUNT)
        
        # Verify remaining steps are empty
        for i in range(3, STEP_COUNT):
            self.assertTrue(chain[i].is_empty())
    
    def test_write_to_binary(self):
        # Create a chain with some data
        chain = M8Chain()
        
        # Set up steps
        chain[0] = M8ChainStep(phrase=10, transpose=5)
        chain[2] = M8ChainStep(phrase=20, transpose=10)
        
        # Write to binary
        binary = chain.write()
        
        # Verify size
        self.assertEqual(len(binary), CHAIN_BLOCK_SIZE)
        
        # Verify specific bytes for steps
        self.assertEqual(binary[0], 10)  # Step 0 phrase
        self.assertEqual(binary[1], 5)   # Step 0 transpose
        
        self.assertEqual(binary[2], M8ChainStep.EMPTY_PHRASE)  # Step 1 phrase (empty)
        self.assertEqual(binary[3], 0)                        # Step 1 transpose
        
        self.assertEqual(binary[4], 20)  # Step 2 phrase
        self.assertEqual(binary[5], 10)  # Step 2 transpose
        
        # Verify remaining steps are empty
        for i in range(3, STEP_COUNT):
            offset = i * STEP_BLOCK_SIZE
            self.assertEqual(binary[offset], M8ChainStep.EMPTY_PHRASE)
            self.assertEqual(binary[offset + 1], 0)
    
    def test_read_write_consistency(self):
        # Create a chain with some data
        chain = M8Chain()
        
        # Set up steps
        chain[0] = M8ChainStep(phrase=10, transpose=5)
        chain[3] = M8ChainStep(phrase=20, transpose=10)
        chain[8] = M8ChainStep(phrase=30, transpose=15)
        
        # Write to binary
        binary = chain.write()
        
        # Read back from binary
        deserialized = M8Chain.read(binary)
        
        # Verify all steps match
        for i in range(STEP_COUNT):
            self.assertEqual(deserialized[i].phrase, chain[i].phrase)
            self.assertEqual(deserialized[i].transpose, chain[i].transpose)
    
    def test_constructor(self):
        # Test default constructor
        chain = M8Chain()
        
        # Should have STEP_COUNT steps
        self.assertEqual(len(chain), STEP_COUNT)
        
        # All steps should be empty
        for step in chain:
            self.assertTrue(step.is_empty())
    
    def test_is_empty(self):
        # Test is_empty method
        chain = M8Chain()
        self.assertTrue(chain.is_empty())
        
        # Modify one step
        chain[0] = M8ChainStep(phrase=10, transpose=5)
        self.assertFalse(chain.is_empty())
        
        # Reset to empty
        chain[0] = M8ChainStep()
        self.assertTrue(chain.is_empty())
    
    def test_clone(self):
        # Test clone method
        original = M8Chain()
        original[0] = M8ChainStep(phrase=10, transpose=5)
        original[5] = M8ChainStep(phrase=20, transpose=10)
        
        clone = original.clone()
        
        # Verify clone has the same values
        for i in range(STEP_COUNT):
            self.assertEqual(clone[i].phrase, original[i].phrase)
            self.assertEqual(clone[i].transpose, original[i].transpose)
        
        # Verify clone is a different object
        self.assertIsNot(clone, original)
        
        # Modify clone and verify original remains unchanged
        clone[0].phrase = 30
        self.assertEqual(original[0].phrase, 10)
    
    def test_validate_references_phrases(self):
        # Create a mock phrases list
        mock_phrases = [None] * 20  # Just need a list of the right length
        
        # Test case 1: Valid chain
        chain = M8Chain()
        chain[0] = M8ChainStep(phrase=10, transpose=5)
        chain[1] = M8ChainStep(phrase=15, transpose=10)
        result = chain.validate_references_phrases(mock_phrases)
        self.assertTrue(result.valid)
        
        # Test case 2: Reference to non-existent phrase
        chain = M8Chain()
        chain[0] = M8ChainStep(phrase=30, transpose=5)  # Phrase 30 doesn't exist
        result = chain.validate_references_phrases(mock_phrases)
        self.assertFalse(result.valid)
        self.assertTrue(any("non-existent" in err for err in result.errors))
        
        # Test case 3: Empty chain should be valid
        chain = M8Chain()
        chain.validate_references_phrases([])  # Should not raise even with empty phrases list
        
    def test_validate_one_to_one_pattern(self):
        # Test case 1: Valid one-to-one pattern (chain 5 with phrase 5)
        chain = M8Chain()
        chain[0] = M8ChainStep(phrase=5, transpose=0)
        # All other steps are empty by default
        
        result = chain.validate_one_to_one_pattern(5)
        self.assertTrue(result.valid)
        
        # Test case 2: Invalid - phrase ID doesn't match chain ID
        chain = M8Chain()
        chain[0] = M8ChainStep(phrase=10, transpose=0)
        
        result = chain.validate_one_to_one_pattern(5)
        self.assertFalse(result.valid)
        self.assertTrue(any("should reference" in err.lower() for err in result.errors))
        
        # Test case 3: Invalid - has a second phrase
        chain = M8Chain()
        chain[0] = M8ChainStep(phrase=5, transpose=0)
        chain[1] = M8ChainStep(phrase=6, transpose=0)
        
        result = chain.validate_one_to_one_pattern(5)
        self.assertFalse(result.valid)
        self.assertTrue(any("must be empty" in err.lower() for err in result.errors))
        
        # Test case 4: Invalid - empty chain (no phrases)
        chain = M8Chain()
        result = chain.validate_one_to_one_pattern(5)
        self.assertFalse(result.valid)
        self.assertTrue(any("must have a phrase" in err.lower() for err in result.errors))
    
    def test_available_step_slot(self):
        # Test available_step_slot property
        chain = M8Chain()  # All slots empty
        self.assertEqual(chain.available_step_slot, 0)
        
        # Fill first slot
        chain[0] = M8ChainStep(phrase=10, transpose=5)
        self.assertEqual(chain.available_step_slot, 1)
        
        # Fill all slots
        for i in range(STEP_COUNT):
            chain[i] = M8ChainStep(phrase=i, transpose=0)
        self.assertIsNone(chain.available_step_slot)
    
    def test_add_step(self):
        # Test add_step method
        chain = M8Chain()
        step = M8ChainStep(phrase=10, transpose=5)
        
        # Add step to empty chain
        slot = chain.add_step(step)
        self.assertEqual(slot, 0)
        self.assertEqual(chain[0].phrase, 10)
        self.assertEqual(chain[0].transpose, 5)
        
        # Add another step
        step2 = M8ChainStep(phrase=20, transpose=10)
        slot = chain.add_step(step2)
        self.assertEqual(slot, 1)
        self.assertEqual(chain[1].phrase, 20)
        self.assertEqual(chain[1].transpose, 10)
        
        # Fill all slots and test error
        for i in range(2, STEP_COUNT):
            chain[i] = M8ChainStep(phrase=i, transpose=0)
        
        with self.assertRaises(IndexError):
            chain.add_step(step)
    
    def test_set_step(self):
        # Test set_step method
        chain = M8Chain()
        step = M8ChainStep(phrase=10, transpose=5)
        
        # Set step at specific slot
        chain.set_step(step, 3)
        self.assertEqual(chain[3].phrase, 10)
        self.assertEqual(chain[3].transpose, 5)
        
        # Test invalid slot
        with self.assertRaises(IndexError):
            chain.set_step(step, STEP_COUNT)
        
        with self.assertRaises(IndexError):
            chain.set_step(step, -1)
    
    def test_as_dict(self):
        # Test as_dict method
        chain = M8Chain()
        
        # Add some steps
        chain[0] = M8ChainStep(phrase=10, transpose=5)
        chain[3] = M8ChainStep(phrase=20, transpose=10)
        chain[8] = M8ChainStep(phrase=30, transpose=15)
        
        result = chain.as_dict()
        
        # Should only contain non-empty steps
        self.assertEqual(len(result["steps"]), 3)
        
        # Check specific steps
        step0 = next(s for s in result["steps"] if s["index"] == 0)
        self.assertEqual(step0["phrase"], 10)
        self.assertEqual(step0["transpose"], 5)
        
        step3 = next(s for s in result["steps"] if s["index"] == 3)
        self.assertEqual(step3["phrase"], 20)
        self.assertEqual(step3["transpose"], 10)
        
        step8 = next(s for s in result["steps"] if s["index"] == 8)
        self.assertEqual(step8["phrase"], 30)
        self.assertEqual(step8["transpose"], 15)
        
        # Test empty chain
        chain = M8Chain()
        result = chain.as_dict()
        self.assertEqual(result, {"steps": []})
    
    def test_from_dict(self):
        # Test from_dict method
        data = {
            "steps": [
                {"index": 0, "phrase": 10, "transpose": 5},
                {"index": 3, "phrase": 20, "transpose": 10},
                {"index": 8, "phrase": 30, "transpose": 15}
            ]
        }
        
        chain = M8Chain.from_dict(data)
        
        # Check specific steps
        self.assertEqual(chain[0].phrase, 10)
        self.assertEqual(chain[0].transpose, 5)
        
        self.assertEqual(chain[3].phrase, 20)
        self.assertEqual(chain[3].transpose, 10)
        
        self.assertEqual(chain[8].phrase, 30)
        self.assertEqual(chain[8].transpose, 15)
        
        # Other steps should be empty
        for i in [1, 2, 4, 5, 6, 7] + list(range(9, STEP_COUNT)):
            self.assertTrue(chain[i].is_empty())
        
        # Test with invalid step index
        data = {
            "steps": [
                {"index": STEP_COUNT + 5, "phrase": 40, "transpose": 20}  # Out of range
            ]
        }
        
        chain = M8Chain.from_dict(data)
        self.assertTrue(chain.is_empty())
        
        # Test with empty dict
        chain = M8Chain.from_dict({})
        self.assertTrue(chain.is_empty())


class TestM8Chains(unittest.TestCase):
    def test_read_from_binary(self):
        # Create minimal test data for simplicity (full data would be too large)
        test_data = bytearray()
        
        # Chain 0: First step has phrase=10, transpose=5, rest empty
        chain0_data = bytearray([10, 5])
        chain0_data.extend([M8ChainStep.EMPTY_PHRASE, 0] * (STEP_COUNT - 1))
        test_data.extend(chain0_data)
        
        # Chain 1: All empty
        test_data.extend([M8ChainStep.EMPTY_PHRASE, 0] * STEP_COUNT)
        
        # Chain 2: Second step has phrase=20, transpose=10, rest empty
        chain2_data = bytearray([M8ChainStep.EMPTY_PHRASE, 0])
        chain2_data.extend([20, 10])
        chain2_data.extend([M8ChainStep.EMPTY_PHRASE, 0] * (STEP_COUNT - 2))
        test_data.extend(chain2_data)
        
        # Fill the rest with empty chains
        for _ in range(CHAIN_COUNT - 3):
            test_data.extend([M8ChainStep.EMPTY_PHRASE, 0] * STEP_COUNT)
        
        # Read from binary
        chains = M8Chains.read(test_data)
        
        # Check number of chains
        self.assertEqual(len(chains), CHAIN_COUNT)
        
        # Check chain 0
        self.assertEqual(chains[0][0].phrase, 10)
        self.assertEqual(chains[0][0].transpose, 5)
        for i in range(1, STEP_COUNT):
            self.assertTrue(chains[0][i].is_empty())
        
        # Check chain 1
        self.assertTrue(chains[1].is_empty())
        
        # Check chain 2
        self.assertTrue(chains[2][0].is_empty())
        self.assertEqual(chains[2][1].phrase, 20)
        self.assertEqual(chains[2][1].transpose, 10)
        for i in range(2, STEP_COUNT):
            self.assertTrue(chains[2][i].is_empty())
        
        # Check remaining chains
        for i in range(3, CHAIN_COUNT):
            self.assertTrue(chains[i].is_empty())
    
    def test_write_to_binary(self):
        # Create chains with some data
        chains = M8Chains()
        
        # Set up chain 0
        chains[0][0] = M8ChainStep(phrase=10, transpose=5)
        
        # Set up chain 2
        chains[2][1] = M8ChainStep(phrase=20, transpose=10)
        
        # Write to binary
        binary = chains.write()
        
        # Check size
        self.assertEqual(len(binary), CHAIN_COUNT * CHAIN_BLOCK_SIZE)
        
        # Check chain 0
        self.assertEqual(binary[0], 10)  # First step phrase
        self.assertEqual(binary[1], 5)   # First step transpose
        
        # Check chain 2
        offset = 2 * CHAIN_BLOCK_SIZE
        self.assertEqual(binary[offset], M8ChainStep.EMPTY_PHRASE)  # First step phrase (empty)
        self.assertEqual(binary[offset + 1], 0)                    # First step transpose
        self.assertEqual(binary[offset + 2], 20)                   # Second step phrase
        self.assertEqual(binary[offset + 3], 10)                   # Second step transpose
    
    def test_read_write_consistency(self):
        # Create chains with some data
        chains = M8Chains()
        
        # Set up chain 0
        chains[0][0] = M8ChainStep(phrase=10, transpose=5)
        
        # Set up chain 5
        chains[5][3] = M8ChainStep(phrase=20, transpose=10)
        
        # Set up chain 10
        chains[10][8] = M8ChainStep(phrase=30, transpose=15)
        
        # Write to binary
        binary = chains.write()
        
        # Read back from binary
        deserialized = M8Chains.read(binary)
        
        # Check chain 0
        self.assertEqual(deserialized[0][0].phrase, 10)
        self.assertEqual(deserialized[0][0].transpose, 5)
        
        # Check chain 5
        self.assertEqual(deserialized[5][3].phrase, 20)
        self.assertEqual(deserialized[5][3].transpose, 10)
        
        # Check chain 10
        self.assertEqual(deserialized[10][8].phrase, 30)
        self.assertEqual(deserialized[10][8].transpose, 15)
        
        # Verify all other chains/steps are empty
        for chain_idx in range(CHAIN_COUNT):
            for step_idx in range(STEP_COUNT):
                if (chain_idx == 0 and step_idx == 0) or \
                   (chain_idx == 5 and step_idx == 3) or \
                   (chain_idx == 10 and step_idx == 8):
                    continue  # Skip the steps we set
                self.assertTrue(deserialized[chain_idx][step_idx].is_empty())
    
    def test_constructor(self):
        # Test default constructor
        chains = M8Chains()
        
        # Should have CHAIN_COUNT chains
        self.assertEqual(len(chains), CHAIN_COUNT)
        
        # Each chain should have STEP_COUNT steps
        for chain in chains:
            self.assertEqual(len(chain), STEP_COUNT)
        
        # All chains should be empty
        for chain in chains:
            self.assertTrue(chain.is_empty())
    
    def test_is_empty(self):
        # Test is_empty method
        chains = M8Chains()
        self.assertTrue(chains.is_empty())
        
        # Modify one chain
        chains[0][0] = M8ChainStep(phrase=10, transpose=5)
        self.assertFalse(chains.is_empty())
        
        # Reset to empty
        chains[0][0] = M8ChainStep()
        self.assertTrue(chains.is_empty())
    
    def test_clone(self):
        # Test clone method
        original = M8Chains()
        original[0][0] = M8ChainStep(phrase=10, transpose=5)
        original[5][3] = M8ChainStep(phrase=20, transpose=10)
        
        clone = original.clone()
        
        # Check clone has the same values
        self.assertEqual(clone[0][0].phrase, 10)
        self.assertEqual(clone[0][0].transpose, 5)
        self.assertEqual(clone[5][3].phrase, 20)
        self.assertEqual(clone[5][3].transpose, 10)
        
        # Verify clone is a different object
        self.assertIsNot(clone, original)
        
        # Modify clone and verify original remains unchanged
        clone[0][0].phrase = 30
        self.assertEqual(original[0][0].phrase, 10)
    
    def test_validate_references_phrases(self):
        # Create a mock phrases list
        mock_phrases = [None] * 20  # Just need a list of the right length
        
        # Test case 1: Valid chains
        chains = M8Chains()
        chains[0][0] = M8ChainStep(phrase=10, transpose=5)
        chains[5][3] = M8ChainStep(phrase=15, transpose=10)
        result = chains.validate_references_phrases(mock_phrases)
        self.assertTrue(result.valid)
        
        # Test case 2: Reference to non-existent phrase
        chains = M8Chains()
        chains[0][0] = M8ChainStep(phrase=30, transpose=5)  # Phrase 30 doesn't exist
        result = chains.validate_references_phrases(mock_phrases)
        self.assertFalse(result.valid)
        self.assertTrue(any("non-existent" in err.lower() for err in result.errors))
        
        # Test case 3: Empty chains should be valid
        chains = M8Chains()
        chains.validate_references_phrases([])  # Should not raise even with empty phrases list
    
    def test_as_list(self):
        # Test as_list method
        chains = M8Chains()
        
        # Add some chains with steps
        chains[0][0] = M8ChainStep(phrase=10, transpose=5)
        chains[5][3] = M8ChainStep(phrase=20, transpose=10)
        chains[10][8] = M8ChainStep(phrase=30, transpose=15)
        
        result = chains.as_list()
        
        # Should only contain non-empty chains
        self.assertEqual(len(result), 3)
        
        # Check specific chains
        chain0 = next(c for c in result if c["index"] == 0)
        self.assertEqual(len(chain0["steps"]), 1)
        self.assertEqual(chain0["steps"][0]["index"], 0)
        self.assertEqual(chain0["steps"][0]["phrase"], 10)
        self.assertEqual(chain0["steps"][0]["transpose"], 5)
        
        chain5 = next(c for c in result if c["index"] == 5)
        self.assertEqual(len(chain5["steps"]), 1)
        self.assertEqual(chain5["steps"][0]["index"], 3)
        self.assertEqual(chain5["steps"][0]["phrase"], 20)
        self.assertEqual(chain5["steps"][0]["transpose"], 10)
        
        chain10 = next(c for c in result if c["index"] == 10)
        self.assertEqual(len(chain10["steps"]), 1)
        self.assertEqual(chain10["steps"][0]["index"], 8)
        self.assertEqual(chain10["steps"][0]["phrase"], 30)
        self.assertEqual(chain10["steps"][0]["transpose"], 15)
        
        # Test empty chains
        chains = M8Chains()
        result = chains.as_list()
        self.assertEqual(result, [])
    
    def test_from_list(self):
        # Test from_list method
        data = [
            {
                "index": 0,
                "steps": [
                    {"index": 0, "phrase": 10, "transpose": 5}
                ]
            },
            {
                "index": 5,
                "steps": [
                    {"index": 3, "phrase": 20, "transpose": 10}
                ]
            },
            {
                "index": 10,
                "steps": [
                    {"index": 8, "phrase": 30, "transpose": 15}
                ]
            }
        ]
        
        chains = M8Chains.from_list(data)
        
        # Check specific chains and steps
        self.assertEqual(chains[0][0].phrase, 10)
        self.assertEqual(chains[0][0].transpose, 5)
        
        self.assertEqual(chains[5][3].phrase, 20)
        self.assertEqual(chains[5][3].transpose, 10)
        
        self.assertEqual(chains[10][8].phrase, 30)
        self.assertEqual(chains[10][8].transpose, 15)
        
        # All other chains/steps should be empty
        for chain_idx in range(CHAIN_COUNT):
            for step_idx in range(STEP_COUNT):
                if (chain_idx == 0 and step_idx == 0) or \
                   (chain_idx == 5 and step_idx == 3) or \
                   (chain_idx == 10 and step_idx == 8):
                    continue  # Skip the steps we set
                self.assertTrue(chains[chain_idx][step_idx].is_empty())
        
        # Test with invalid indices
        data = [
            {
                "index": CHAIN_COUNT + 5,  # Out of range
                "steps": [
                    {"index": 0, "phrase": 40, "transpose": 20}
                ]
            }
        ]
        
        chains = M8Chains.from_list(data)
        self.assertTrue(chains.is_empty())
        
        # Test with empty list
        chains = M8Chains.from_list([])
        self.assertTrue(chains.is_empty())

if __name__ == '__main__':
    unittest.main()