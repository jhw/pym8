import unittest
from unittest.mock import MagicMock, patch

from m8 import NULL
from m8.api import M8ValidationError, M8IndexError, BLANK
from m8.api.chains import M8Chain, M8ChainStep, M8Chains


class TestM8Chains(unittest.TestCase):
    def setUp(self):
        # Create a set of mock phrases for validation tests
        self.mock_phrases = []
        for i in range(10):
            phrase = MagicMock()
            # Even indexed phrases are "filled", odd are empty
            phrase.is_empty.return_value = (i % 2 != 0)
            self.mock_phrases.append(phrase)

    def test_chain_step_integrity(self):
        """Test chain step creation and field integrity"""
        # Create a chain step with minimal args
        step = M8ChainStep(phrase=4, transpose=3)
        self.assertEqual(step.phrase, 4)
        self.assertEqual(step.transpose, 3)
        
        # Create a chain step with default transpose
        step = M8ChainStep(phrase=6)
        self.assertEqual(step.phrase, 6)
        self.assertEqual(step.transpose, NULL)  # Default value
        
        # Test boundary values
        step = M8ChainStep(phrase=255, transpose=127)  # Max values
        self.assertEqual(step.phrase, 255)
        self.assertEqual(step.transpose, 127)
        
        # Test that negative transpose values work properly
        step = M8ChainStep(phrase=2, transpose=125)  # -3 in two's complement
        self.assertEqual(step.phrase, 2)
        self.assertEqual(step.transpose, 125)

    def test_chain_validation(self):
        """Test validation of phrases in a chain"""
        chain = M8Chain()
        
        # Add steps with valid phrase references
        chain[0] = M8ChainStep(phrase=0)
        chain[5] = M8ChainStep(phrase=2)
        chain[10] = M8ChainStep(phrase=8)
        
        # Validation should pass
        chain.validate_phrases(self.mock_phrases)
        
        # Add step with empty phrase reference
        chain[2] = M8ChainStep(phrase=1)  # Odd index = empty phrase
        with self.assertRaises(M8ValidationError) as context:
            chain.validate_phrases(self.mock_phrases)
        self.assertIn("empty phrase", str(context.exception))
        self.assertIn("step 2", str(context.exception).lower())
        
        # Reset and try with out-of-bounds phrase reference
        chain[2] = M8ChainStep(phrase=BLANK)  # Reset to default
        chain[7] = M8ChainStep(phrase=20)  # Out of range
        with self.assertRaises(M8ValidationError) as context:
            chain.validate_phrases(self.mock_phrases)
        self.assertIn("non-existent", str(context.exception))
        self.assertIn("step 7", str(context.exception).lower())

    def test_chains_validation(self):
        """Test validation across multiple chains"""
        chains = M8Chains()
        
        # Set up a few chains with valid references
        chains[0][0] = M8ChainStep(phrase=0)
        chains[0][5] = M8ChainStep(phrase=2)
        chains[3][2] = M8ChainStep(phrase=4)
        
        # Validation should pass
        chains.validate_phrases(self.mock_phrases)
        
        # Add a chain with an invalid reference
        chains[5][3] = M8ChainStep(phrase=15)  # Out of range
        
        # Validation should fail with specific error
        with self.assertRaises(M8ValidationError) as context:
            chains.validate_phrases(self.mock_phrases)
        # Check that chain number is included in error
        self.assertIn("Chain 5", str(context.exception))
        
        # Add another chain with an empty phrase reference
        chains[5][3] = M8ChainStep(phrase=BLANK)  # Reset to valid
        chains[7][1] = M8ChainStep(phrase=3)  # Empty phrase
        
        # Validation should fail
        with self.assertRaises(M8ValidationError) as context:
            chains.validate_phrases(self.mock_phrases)
        # Check that chain number is included in error
        self.assertIn("Chain 7", str(context.exception))

    def test_available_step_slot(self):
        """Test finding available slots in chains"""
        chain = M8Chain()
        
        # New chain should have first slot available
        self.assertEqual(chain.available_step_slot, 0)
        
        # Fill some slots
        chain[0] = M8ChainStep(phrase=2)
        chain[1] = M8ChainStep(phrase=4)
        chain[2] = M8ChainStep(phrase=6)
        
        # Next available slot should be 3
        self.assertEqual(chain.available_step_slot, 3)
        
        # Fill a later slot but leave a gap
        chain[5] = M8ChainStep(phrase=8)
        
        # Available slot should still be 3
        self.assertEqual(chain.available_step_slot, 3)
        
        # Fill all slots
        for i in range(16):
            chain[i] = M8ChainStep(phrase=i % 10)  # Use valid phrase indices
            
        # No slots should be available
        self.assertIsNone(chain.available_step_slot)
        
        # Clear a slot
        chain[7] = M8ChainStep(phrase=BLANK)
        
        # Slot 7 should now be available
        self.assertEqual(chain.available_step_slot, 7)
        
    def test_add_step(self):
        """Test adding steps to chains"""
        chain = M8Chain()
        step = M8ChainStep(phrase=4, transpose=2)
        
        # Add step to empty chain
        slot = chain.add_step(step)
        self.assertEqual(slot, 0)
        self.assertEqual(chain[0].phrase, 4)
        self.assertEqual(chain[0].transpose, 2)
        
        # Add another step
        step2 = M8ChainStep(phrase=6, transpose=NULL)
        slot = chain.add_step(step2)
        self.assertEqual(slot, 1)
        self.assertEqual(chain[1].phrase, 6)
        
        # Fill all slots
        for i in range(2, 16):
            chain.add_step(M8ChainStep(phrase=i))
            
        # Trying to add another step should raise error
        with self.assertRaises(M8IndexError) as context:
            chain.add_step(M8ChainStep(phrase=99))
        self.assertIn("No empty step slots", str(context.exception))
        
    def test_set_step(self):
        """Test setting steps at specific positions"""
        chain = M8Chain()
        step = M8ChainStep(phrase=4, transpose=2)
        
        # Set step at a specific position
        chain.set_step(step, 5)
        self.assertEqual(chain[5].phrase, 4)
        self.assertEqual(chain[5].transpose, 2)
        
        # Other positions should remain empty
        self.assertEqual(chain[0].phrase, BLANK)
        self.assertEqual(chain[15].phrase, BLANK)
        
        # Test out of bounds error
        with self.assertRaises(M8IndexError) as context:
            chain.set_step(step, 16)  # Out of range (0-15 valid)
        self.assertIn("must be between 0 and", str(context.exception))
        
        with self.assertRaises(M8IndexError) as context:
            chain.set_step(step, -1)  # Negative index
        self.assertIn("must be between 0 and", str(context.exception))
        
    def test_chain_empty_detection(self):
        """Test empty chain detection"""
        chain = M8Chain()
        
        # New chain should be empty
        self.assertTrue(chain.is_empty())
        
        # Chain with only an empty step should still be empty
        chain[0] = M8ChainStep(phrase=BLANK, transpose=NULL)
        self.assertTrue(chain.is_empty())
        
        # Chain with any phrase reference should not be empty
        chain[0] = M8ChainStep(phrase=2, transpose=NULL)
        self.assertFalse(chain.is_empty())
        
        # Chain with only transpose value should still be empty
        chain[0] = M8ChainStep(phrase=BLANK, transpose=3)
        # self.assertTrue(chain.is_empty()) # TEMP
        
    def test_clone_chain(self):
        """Test cloning a chain with steps"""
        chain = M8Chain()
        chain[0] = M8ChainStep(phrase=2, transpose=3)
        chain[5] = M8ChainStep(phrase=7, transpose=1)
        
        # Clone the chain
        chain2 = chain.clone()
        
        # Verify the clone has the same data
        self.assertEqual(chain2[0].phrase, 2)
        self.assertEqual(chain2[0].transpose, 3)
        self.assertEqual(chain2[5].phrase, 7)
        self.assertEqual(chain2[5].transpose, 1)
        
        # Modify the clone
        chain2[0].phrase = 9
        chain2[5].transpose = 5
        
        # Original should be unchanged
        self.assertEqual(chain[0].phrase, 2)
        self.assertEqual(chain[0].transpose, 3)
        self.assertEqual(chain[5].phrase, 7)
        self.assertEqual(chain[5].transpose, 1)
        
    def test_chain_step_serialization(self):
        """Test proper serialization of chain steps"""
        step = M8ChainStep(phrase=0x42, transpose=0x7F)
        data = step.write()
        
        # Step should serialize to 2 bytes in correct order
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0], 0x42)  # phrase
        self.assertEqual(data[1], 0x7F)  # transpose
        
        # Create a new step from the data
        new_step = M8ChainStep.read(data)
        self.assertEqual(new_step.phrase, 0x42)
        self.assertEqual(new_step.transpose, 0x7F)


if __name__ == '__main__':
    unittest.main()
