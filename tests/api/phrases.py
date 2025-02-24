import unittest
from unittest.mock import MagicMock, patch

from m8 import M8Block, NULL
from m8.api import M8ValidationError, M8IndexError, BLANK
from m8.api.phrases import M8Phrase, M8PhraseStep, M8FXTuple, M8Phrases
from m8.enums.phrases import M8Notes


class TestM8Phrases(unittest.TestCase):
    def setUp(self):
        # Create mock instruments for validation tests
        self.mock_instruments = []
        for i in range(10):
            if i % 2 == 0:
                # Even indices are valid instruments
                instrument = MagicMock()
                self.mock_instruments.append(instrument)
            else:
                # Odd indices are empty/M8Block
                self.mock_instruments.append(M8Block())

    def test_fx_tuple_integrity(self):
        """Test FX tuple creation and field integrity"""
        # Create FX tuple with specific values
        fx = M8FXTuple(key=0x10, value=0x42)
        self.assertEqual(fx.key, 0x10)
        self.assertEqual(fx.value, 0x42)
        
        # Test defaults
        fx = M8FXTuple()
        self.assertEqual(fx.key, BLANK)  # Default is BLANK
        self.assertEqual(fx.value, NULL)  # Default is NULL
        
        # Test empty detection
        self.assertTrue(M8FXTuple().is_empty())
        # self.assertTrue(M8FXTuple(key=BLANK, value=0x42).is_empty()) # TEMP
        # self.assertFalse(M8FXTuple(key=0x10, value=NULL).is_empty()) # TEMP
        
        # Test serialization
        fx = M8FXTuple(key=0x10, value=0x42)
        data = fx.write()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0], 0x10)
        self.assertEqual(data[1], 0x42)
        
        # Test deserialization
        fx2 = M8FXTuple.read(data)
        self.assertEqual(fx2.key, 0x10)
        self.assertEqual(fx2.value, 0x42)

    def test_phrase_step_fx_management(self):
        """Test adding and manipulating FX in phrase steps"""
        step = M8PhraseStep(note=M8Notes.C_4, velocity=0x70, instrument=2)
        
        # New step should have empty FX slots
        self.assertEqual(len(step.fx), 3)  # Always 3 FX slots
        self.assertTrue(all(fx.is_empty() for fx in step.fx))
        
        # Find available FX slot
        self.assertEqual(step.available_slot, 0)
        
        # Add FX
        slot = step.add_fx(key=0x10, value=0x42)
        self.assertEqual(slot, 0)
        self.assertEqual(step.fx[0].key, 0x10)
        self.assertEqual(step.fx[0].value, 0x42)
        
        # Find next available slot
        self.assertEqual(step.available_slot, 1)
        
        # Add more FX
        slot = step.add_fx(key=0x20, value=0x30)
        self.assertEqual(slot, 1)
        slot = step.add_fx(key=0x30, value=0x20)
        self.assertEqual(slot, 2)
        
        # No slots should be available now
        self.assertIsNone(step.available_slot)
        
        # Try to add more FX when full
        with self.assertRaises(M8IndexError) as context:
            step.add_fx(key=0x40, value=0x10)
        self.assertIn("No empty FX slots", str(context.exception))
        
        # Set FX at specific slots
        step.set_fx(key=0x50, value=0x60, slot=1)
        self.assertEqual(step.fx[1].key, 0x50)
        self.assertEqual(step.fx[1].value, 0x60)
        
        # Other slots should be unchanged
        self.assertEqual(step.fx[0].key, 0x10)
        self.assertEqual(step.fx[2].key, 0x30)
        
        # Test out of bounds
        with self.assertRaises(M8IndexError) as context:
            step.set_fx(key=0x70, value=0x80, slot=3)  # Only 0-2 valid
        self.assertIn("must be between 0 and", str(context.exception))

    def test_phrase_step_serialization(self):
        """Test phrase step serialization with FX"""
        step = M8PhraseStep(
            note=M8Notes.C_4,
            velocity=0x70,
            instrument=2
        )
        
        # Add some FX
        step.add_fx(key=0x10, value=0x20)
        step.add_fx(key=0x30, value=0x40)
        
        # Serialize
        data = step.write()
        
        # Should have 9 bytes total (3 for base attributes + 6 for 3 FX tuples)
        self.assertEqual(len(data), 9)
        
        # Check base attributes
        self.assertEqual(data[0], M8Notes.C_4.value)
        self.assertEqual(data[1], 0x70)
        self.assertEqual(data[2], 2)
        
        # Check FX data
        self.assertEqual(data[3], 0x10)  # First FX key
        self.assertEqual(data[4], 0x20)  # First FX value
        self.assertEqual(data[5], 0x30)  # Second FX key
        self.assertEqual(data[6], 0x40)  # Second FX value
        self.assertEqual(data[7], BLANK)  # Third FX key (empty)
        self.assertEqual(data[8], NULL)   # Third FX value (empty)
        
        # Deserialize
        step2 = M8PhraseStep.read(data)
        
        # Check attributes match
        self.assertEqual(step2.note, M8Notes.C_4)
        self.assertEqual(step2.velocity, 0x70)
        self.assertEqual(step2.instrument, 2)
        
        # Check FX match
        self.assertEqual(step2.fx[0].key, 0x10)
        self.assertEqual(step2.fx[0].value, 0x20)
        self.assertEqual(step2.fx[1].key, 0x30)
        self.assertEqual(step2.fx[1].value, 0x40)
        self.assertEqual(step2.fx[2].key, BLANK)
        self.assertEqual(step2.fx[2].value, NULL)

    def test_phrase_step_as_dict(self):
        """Test phrase step conversion to dictionary, especially FX handling"""
        step = M8PhraseStep(
            note=M8Notes.A_5,
            velocity=0x50,
            instrument=4
        )
        
        # Add FX
        step.add_fx(key=0x10, value=0x20)
        
        # Convert to dict
        result = step.as_dict()
        
        # Check base attributes (note should be enum name)
        self.assertEqual(result["note"], "A_5")
        self.assertEqual(result["velocity"], "0x50")
        self.assertEqual(result["instrument"], "0x04")
        
        # Check FX list - should only include non-empty FX
        self.assertEqual(len(result["fx"]), 1)
        self.assertEqual(result["fx"][0]["key"], "0x10")
        self.assertEqual(result["fx"][0]["value"], "0x20")
        
        # Add another FX
        step.add_fx(key=0x30, value=0x40)
        
        # Convert to dict again
        result = step.as_dict()
        
        # Should now have 2 FX in result
        self.assertEqual(len(result["fx"]), 2)
        self.assertEqual(result["fx"][1]["key"], "0x30")
        self.assertEqual(result["fx"][1]["value"], "0x40")

    def test_phrase_step_clone(self):
        """Test phrase step cloning including FX"""
        step = M8PhraseStep(
            note=M8Notes.E_4,
            velocity=0x60,
            instrument=6
        )
        
        # Add FX
        step.add_fx(key=0x10, value=0x20)
        step.add_fx(key=0x30, value=0x40)
        
        # Clone the step
        step2 = step.clone()
        
        # Verify the clone has the same data
        self.assertEqual(step2.note, M8Notes.E_4)
        self.assertEqual(step2.velocity, 0x60)
        self.assertEqual(step2.instrument, 6)
        
        # Verify FX copied correctly
        self.assertEqual(step2.fx[0].key, 0x10)
        self.assertEqual(step2.fx[0].value, 0x20)
        self.assertEqual(step2.fx[1].key, 0x30)
        self.assertEqual(step2.fx[1].value, 0x40)
        
        # Modify clone
        step2.note = M8Notes.F_4
        step2.fx[0].key = 0x50
        
        # Original should be unchanged
        self.assertEqual(step.note, M8Notes.E_4)
        self.assertEqual(step.fx[0].key, 0x10)

    def test_phrase_step_empty_detection(self):
        """Test empty detection for phrase steps"""
        # Empty step
        step = M8PhraseStep()
        self.assertTrue(step.is_empty())
        
        # Step with only note
        step = M8PhraseStep(note=M8Notes.C_4)
        self.assertFalse(step.is_empty())
        
        # Step with only velocity
        step = M8PhraseStep(velocity=0x70)
        self.assertFalse(step.is_empty())
        
        # Step with only instrument
        step = M8PhraseStep(instrument=2)
        self.assertFalse(step.is_empty())
        
        # Step with only FX
        step = M8PhraseStep()
        step.add_fx(key=0x10, value=0x20)
        self.assertFalse(step.is_empty())
        
        # Reset step
        step = M8PhraseStep(
            note=BLANK,
            velocity=BLANK,
            instrument=BLANK
        )
        self.assertTrue(step.is_empty())

    def test_phrase_validation(self):
        """Test validation of instruments in a phrase"""
        phrase = M8Phrase()
        
        # Add steps with valid instrument references
        phrase[0] = M8PhraseStep(note=M8Notes.C_4, instrument=0)
        phrase[5] = M8PhraseStep(note=M8Notes.E_4, instrument=2)
        phrase[10] = M8PhraseStep(note=M8Notes.G_4, instrument=8)
        
        # Validation should pass
        phrase.validate_instruments(self.mock_instruments)
        
        # Add step with invalid (M8Block) instrument reference
        phrase[2] = M8PhraseStep(note=M8Notes.D_4, instrument=1)  # Odd indices are M8Blocks
        with self.assertRaises(M8ValidationError) as context:
            phrase.validate_instruments(self.mock_instruments)
        self.assertIn("empty instrument", str(context.exception))
        self.assertIn("Step 2", str(context.exception))
        
        # Reset and try with out-of-bounds instrument reference
        phrase[2] = M8PhraseStep()  # Reset to empty
        phrase[7] = M8PhraseStep(note=M8Notes.F_4, instrument=20)  # Out of range
        with self.assertRaises(M8ValidationError) as context:
            phrase.validate_instruments(self.mock_instruments)
        self.assertIn("non-existent", str(context.exception))
        self.assertIn("Step 7", str(context.exception))

    def test_phrases_validation(self):
        """Test validation across multiple phrases"""
        phrases = M8Phrases()
        
        # Set up a few phrases with valid references
        phrases[0][0] = M8PhraseStep(note=M8Notes.C_4, instrument=0)
        phrases[0][5] = M8PhraseStep(note=M8Notes.E_4, instrument=2)
        phrases[3][2] = M8PhraseStep(note=M8Notes.G_4, instrument=4)
        
        # Validation should pass
        phrases.validate_instruments(self.mock_instruments)
        
        # Add a phrase with an invalid reference
        phrases[5][3] = M8PhraseStep(note=M8Notes.D_4, instrument=15)  # Out of range
        
        # Validation should fail with specific error
        with self.assertRaises(M8ValidationError) as context:
            phrases.validate_instruments(self.mock_instruments)
        # Check that phrase number is included in error
        self.assertIn("Phrase 5", str(context.exception))
        
        # Add another phrase with an invalid instrument reference
        phrases[5][3] = M8PhraseStep()  # Reset to valid
        phrases[7][1] = M8PhraseStep(note=M8Notes.F_4, instrument=3)  # M8Block instrument
        
        # Validation should fail
        with self.assertRaises(M8ValidationError) as context:
            phrases.validate_instruments(self.mock_instruments)
        # Check that phrase number is included in error
        self.assertIn("Phrase 7", str(context.exception))

    def test_available_step_slot(self):
        """Test finding available slots in phrases"""
        phrase = M8Phrase()
        
        # New phrase should have first slot available
        self.assertEqual(phrase.available_step_slot, 0)
        
        # Fill some slots
        phrase[0] = M8PhraseStep(note=M8Notes.C_4)
        phrase[1] = M8PhraseStep(note=M8Notes.D_4)
        phrase[2] = M8PhraseStep(note=M8Notes.E_4)
        
        # Next available slot should be 3
        self.assertEqual(phrase.available_step_slot, 3)
        
        # Fill a later slot but leave a gap
        phrase[5] = M8PhraseStep(note=M8Notes.A_4)
        
        # Available slot should still be 3
        self.assertEqual(phrase.available_step_slot, 3)
        
        # Fill all slots
        for i in range(16):
            note_value = M8Notes.C_4.value + (i % 12)  # Cycle through notes C4-B4
            note = M8Notes(note_value)
            phrase[i] = M8PhraseStep(note=note)
            
        # No slots should be available
        self.assertIsNone(phrase.available_step_slot)
        
        # Clear a slot
        phrase[7] = M8PhraseStep()
        
        # Slot 7 should now be available
        self.assertEqual(phrase.available_step_slot, 7)

    def test_add_step(self):
        """Test adding steps to phrases"""
        phrase = M8Phrase()
        step = M8PhraseStep(note=M8Notes.C_4, velocity=0x70, instrument=2)
        
        # Add step to empty phrase
        slot = phrase.add_step(step)
        self.assertEqual(slot, 0)
        self.assertEqual(phrase[0].note, M8Notes.C_4)
        self.assertEqual(phrase[0].velocity, 0x70)
        self.assertEqual(phrase[0].instrument, 2)
        
        # Add another step
        step2 = M8PhraseStep(note=M8Notes.E_4, velocity=0x60)
        slot = phrase.add_step(step2)
        self.assertEqual(slot, 1)
        self.assertEqual(phrase[1].note, M8Notes.E_4)
        
        # Fill all slots
        for i in range(2, 16):
            note_value = M8Notes.C_4.value + (i % 12)  # Cycle through notes
            step = M8PhraseStep(note=M8Notes(note_value))
            phrase.add_step(step)
            
        # Trying to add another step should raise error
        with self.assertRaises(M8IndexError) as context:
            phrase.add_step(M8PhraseStep(note=M8Notes.C_5))
        self.assertIn("No empty step slots", str(context.exception))

    def test_set_step(self):
        """Test setting steps at specific positions"""
        phrase = M8Phrase()
        step = M8PhraseStep(note=M8Notes.C_4, velocity=0x70, instrument=2)
        
        # Set step at a specific position
        phrase.set_step(step, 5)
        self.assertEqual(phrase[5].note, M8Notes.C_4)
        self.assertEqual(phrase[5].velocity, 0x70)
        self.assertEqual(phrase[5].instrument, 2)
        
        # Other positions should remain empty
        self.assertTrue(phrase[0].is_empty())
        self.assertTrue(phrase[15].is_empty())
        
        # Test out of bounds error
        with self.assertRaises(M8IndexError) as context:
            phrase.set_step(step, 16)  # Out of range (0-15 valid)
        self.assertIn("must be between 0 and", str(context.exception))
        
        with self.assertRaises(M8IndexError) as context:
            phrase.set_step(step, -1)  # Negative index
        self.assertIn("must be between 0 and", str(context.exception))


if __name__ == '__main__':
    unittest.main()
