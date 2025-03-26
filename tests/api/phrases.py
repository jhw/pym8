import unittest
from m8.api.phrases import (
    M8PhraseStep, M8Phrase, M8Phrases,
    STEP_BLOCK_SIZE, STEP_COUNT, PHRASE_BLOCK_SIZE, PHRASE_COUNT, FX_BLOCK_COUNT
)
from m8.api.fx import M8FXTuple, M8FXTuples
from m8.api import M8ValidationError, M8Block
from m8.enums import M8Notes

class TestM8PhraseStep(unittest.TestCase):
    def test_read_from_binary(self):
        # Create test binary data for a step with note, velocity, instrument, and 3 FX tuples
        test_data = bytearray()
        
        # Basic step data (note, velocity, instrument)
        test_data.extend([60, 100, 5])  # note=60 (C_6), velocity=100, instrument=5
        
        # FX tuples
        test_data.extend([10, 20])  # FX1: key=10, value=20
        test_data.extend([30, 40])  # FX2: key=30, value=40
        test_data.extend([M8FXTuple.EMPTY_KEY, 0])  # FX3: empty
        
        # Read from binary
        step = M8PhraseStep.read(test_data)
        
        # Verify basic fields - note should now be a string enum name
        self.assertEqual(step.note, "C_6")
        self.assertEqual(step.velocity, 100)
        self.assertEqual(step.instrument, 5)
        
        # Verify FX tuples
        self.assertEqual(step.fx[0].key, 10)
        self.assertEqual(step.fx[0].value, 20)
        self.assertEqual(step.fx[1].key, 30)
        self.assertEqual(step.fx[1].value, 40)
        self.assertTrue(step.fx[2].is_empty())
        
        # Test empty step
        test_data = bytearray([
            M8PhraseStep.EMPTY_NOTE, M8PhraseStep.EMPTY_VELOCITY, M8PhraseStep.EMPTY_INSTRUMENT,
            M8FXTuple.EMPTY_KEY, 0, M8FXTuple.EMPTY_KEY, 0, M8FXTuple.EMPTY_KEY, 0
        ])
        step = M8PhraseStep.read(test_data)
        self.assertTrue(step.is_empty())
    
    def test_write_to_binary(self):
        # Create a step with some data using string note
        step = M8PhraseStep(note="C_6", velocity=100, instrument=5)
        
        # Set up FX tuples
        step.fx[0] = M8FXTuple(key=10, value=20)
        step.fx[1] = M8FXTuple(key=30, value=40)
        
        # Write to binary
        binary = step.write()
        
        # Verify size and contents
        self.assertEqual(len(binary), M8PhraseStep.BASE_DATA_SIZE + FX_BLOCK_COUNT * 2)
        
        # Check basic fields - note should be converted to binary value 60 (C_6)
        self.assertEqual(binary[0], 60)  # note C_6 = 60
        self.assertEqual(binary[1], 100)  # velocity
        self.assertEqual(binary[2], 5)    # instrument
        
        # Check FX tuples
        self.assertEqual(binary[3], 10)  # FX1 key
        self.assertEqual(binary[4], 20)  # FX1 value
        self.assertEqual(binary[5], 30)  # FX2 key
        self.assertEqual(binary[6], 40)  # FX2 value
        self.assertEqual(binary[7], M8FXTuple.EMPTY_KEY)  # FX3 key (empty)
        self.assertEqual(binary[8], 0)                    # FX3 value
    
    def test_read_write_consistency(self):
        # Create a step with some data using string note
        original = M8PhraseStep(note="C_6", velocity=100, instrument=5)
        original.fx[0] = M8FXTuple(key=10, value=20)
        original.fx[1] = M8FXTuple(key=30, value=40)
        
        # Write to binary
        binary = original.write()
        
        # Read back from binary
        deserialized = M8PhraseStep.read(binary)
        
        # Verify all fields match
        self.assertEqual(deserialized.note, original.note)  # Both should be string "C_5"
        self.assertEqual(deserialized.velocity, original.velocity)
        self.assertEqual(deserialized.instrument, original.instrument)
        
        for i in range(FX_BLOCK_COUNT):
            self.assertEqual(deserialized.fx[i].key, original.fx[i].key)
            self.assertEqual(deserialized.fx[i].value, original.fx[i].value)
    
    def test_constructor_and_defaults(self):
        # Test default constructor
        step = M8PhraseStep()
        self.assertEqual(step.note, M8PhraseStep.EMPTY_NOTE)
        self.assertEqual(step.velocity, M8PhraseStep.EMPTY_VELOCITY)
        self.assertEqual(step.instrument, M8PhraseStep.EMPTY_INSTRUMENT)
        self.assertEqual(len(step.fx), FX_BLOCK_COUNT)
        
        # Test with string note parameter
        step = M8PhraseStep(note="C_6", velocity=100, instrument=5)
        self.assertEqual(step.note, "C_6")
        self.assertEqual(step.velocity, 100)
        self.assertEqual(step.instrument, 5)
        
        # Test with numeric note parameter (should still return string from getter)
        step = M8PhraseStep(note=60, velocity=100, instrument=5)
        self.assertEqual(step.note, "C_6")
        self.assertEqual(step.velocity, 100)
        self.assertEqual(step.instrument, 5)
        
        # Test with partial parameters
        step = M8PhraseStep(note="C_6")
        self.assertEqual(step.note, "C_6")
        self.assertEqual(step.velocity, M8PhraseStep.EMPTY_VELOCITY)
        self.assertEqual(step.instrument, M8PhraseStep.EMPTY_INSTRUMENT)
    
    def test_property_accessors(self):
        # Test property getters and setters
        step = M8PhraseStep()
        
        # Test setters with string enum
        step.note = "C_6"
        step.velocity = 100
        step.instrument = 5
        
        # Test getters
        self.assertEqual(step.note, "C_6")
        self.assertEqual(step.velocity, 100)
        self.assertEqual(step.instrument, 5)
        
        # Test with numeric note value
        step.note = 62  # D_6
        self.assertEqual(step.note, "D_6")
    
    def test_is_empty(self):
        # Test is_empty method
        step = M8PhraseStep()
        self.assertTrue(step.is_empty())
        
        # Modify note
        step.note = "C_6"
        self.assertFalse(step.is_empty())
        step.note = M8PhraseStep.EMPTY_NOTE
        self.assertTrue(step.is_empty())
        
        # Modify velocity
        step.velocity = 100
        self.assertFalse(step.is_empty())
        step.velocity = M8PhraseStep.EMPTY_VELOCITY
        self.assertTrue(step.is_empty())
        
        # Modify instrument
        step.instrument = 5
        self.assertFalse(step.is_empty())
        step.instrument = M8PhraseStep.EMPTY_INSTRUMENT
        self.assertTrue(step.is_empty())
        
        # Modify FX
        step.fx[0] = M8FXTuple(key=10, value=20)
        self.assertFalse(step.is_empty())
        
    def test_is_complete(self):
        # Test is_complete method
        step = M8PhraseStep()
        # Empty step is complete
        self.assertTrue(step.is_complete())
        
        # Step with just a note is incomplete (missing velocity and instrument)
        step.note = "C_6"
        self.assertFalse(step.is_complete())
        
        # Step with note and velocity is incomplete (missing instrument)
        step.velocity = 100
        self.assertFalse(step.is_complete())
        
        # Step with note, velocity, and instrument is complete
        step.instrument = 5
        self.assertTrue(step.is_complete())
        
        # Reset to empty
        step = M8PhraseStep()
        
        # Step with just FX is complete (FX-only step)
        step.fx[0] = M8FXTuple(key=10, value=20)
        self.assertTrue(step.is_complete())
        
        # Step with note and FX but no velocity/instrument is incomplete
        step.note = "C_6"
        self.assertFalse(step.is_complete())
    
    def test_clone(self):
        # Test clone method
        original = M8PhraseStep(note="C_6", velocity=100, instrument=5)
        original.fx[0] = M8FXTuple(key=10, value=20)
        original.fx[1] = M8FXTuple(key=30, value=40)
        
        clone = original.clone()
        
        # Verify clone has the same values
        self.assertEqual(clone.note, original.note)
        self.assertEqual(clone.velocity, original.velocity)
        self.assertEqual(clone.instrument, original.instrument)
        
        for i in range(FX_BLOCK_COUNT):
            self.assertEqual(clone.fx[i].key, original.fx[i].key)
            self.assertEqual(clone.fx[i].value, original.fx[i].value)
        
        # Verify clone is a different object
        self.assertIsNot(clone, original)
        
        # Modify clone and verify original remains unchanged
        clone.note = "D_6"
        clone.fx[0].key = 50
        self.assertEqual(original.note, "C_6")
        self.assertEqual(original.fx[0].key, 10)
    
    def test_available_slot(self):
        # Test available_slot property
        step = M8PhraseStep()  # All FX slots empty
        self.assertEqual(step.available_slot, 0)
        
        # Fill first slot
        step.fx[0] = M8FXTuple(key=10, value=20)
        self.assertEqual(step.available_slot, 1)
        
        # Fill all slots
        for i in range(FX_BLOCK_COUNT):
            step.fx[i] = M8FXTuple(key=i+10, value=i+20)
        self.assertIsNone(step.available_slot)
    
    def test_find_fx_slot(self):
        # Test find_fx_slot method
        step = M8PhraseStep()
        step.fx[0] = M8FXTuple(key=10, value=20)
        step.fx[2] = M8FXTuple(key=30, value=40)
        
        # Find existing slots
        self.assertEqual(step.find_fx_slot(10), 0)
        self.assertEqual(step.find_fx_slot(30), 2)
        
        # Find non-existent slot
        self.assertIsNone(step.find_fx_slot(20))
    
    def test_add_fx(self):
        # Test add_fx method
        step = M8PhraseStep()
        
        # Add new FX
        slot = step.add_fx(10, 20)
        self.assertEqual(slot, 0)
        self.assertEqual(step.fx[0].key, 10)
        self.assertEqual(step.fx[0].value, 20)
        
        # Add another FX
        slot = step.add_fx(30, 40)
        self.assertEqual(slot, 1)
        self.assertEqual(step.fx[1].key, 30)
        self.assertEqual(step.fx[1].value, 40)
        
        # Update existing FX
        slot = step.add_fx(10, 25)  # Same key, different value
        self.assertEqual(slot, 0)  # Should reuse the same slot
        self.assertEqual(step.fx[0].key, 10)
        self.assertEqual(step.fx[0].value, 25)  # Updated value
        
        # Fill all slots and test error
        step.fx[2] = M8FXTuple(key=50, value=60)
        with self.assertRaises(IndexError):
            step.add_fx(70, 80)  # No slots available
    
    def test_set_fx(self):
        # Test set_fx method
        step = M8PhraseStep()
        
        # Set FX at specific slot
        step.set_fx(10, 20, 1)
        self.assertEqual(step.fx[1].key, 10)
        self.assertEqual(step.fx[1].value, 20)
        
        # Test invalid slot
        with self.assertRaises(IndexError):
            step.set_fx(30, 40, FX_BLOCK_COUNT)
        
        with self.assertRaises(IndexError):
            step.set_fx(30, 40, -1)
    
    def test_get_fx(self):
        # Test get_fx method
        step = M8PhraseStep()
        step.fx[0] = M8FXTuple(key=10, value=20)
        step.fx[2] = M8FXTuple(key=30, value=40)
        
        # Get existing FX
        self.assertEqual(step.get_fx(10), 20)
        self.assertEqual(step.get_fx(30), 40)
        
        # Get non-existent FX
        self.assertIsNone(step.get_fx(20))
    
    def test_delete_fx(self):
        # Test delete_fx method
        step = M8PhraseStep()
        step.fx[0] = M8FXTuple(key=10, value=20)
        step.fx[2] = M8FXTuple(key=30, value=40)
        
        # Delete existing FX
        result = step.delete_fx(10)
        self.assertTrue(result)
        self.assertTrue(step.fx[0].is_empty())
        self.assertEqual(step.fx[2].key, 30)  # Other FX should be unchanged
        
        # Delete non-existent FX
        result = step.delete_fx(20)
        self.assertFalse(result)
    
    def test_as_dict(self):
        # For proper enum value serialization, we need context with instrument types
        # This test uses explicit context to ensure consistent behavior
        from m8.core.enums import M8InstrumentContext
        from m8.enums import M8InstrumentType
        
        # Set up direct instrument context
        context = M8InstrumentContext.get_instance()
        context.current_instrument_type_id = M8InstrumentType.WAVSYNTH.value
        
        # Create a step with FX and a valid instrument reference
        step = M8PhraseStep(note="C_6", velocity=100, instrument=5)
        step.fx[0] = M8FXTuple(key=10, value=20)
        step.fx[2] = M8FXTuple(key=30, value=40)
        
        # Get serialized dict
        result = step.as_dict()
        
        # Verify basic fields - note should be string
        self.assertEqual(result["note"], "C_6")
        self.assertEqual(result["velocity"], 100)
        self.assertEqual(result["instrument"], 5)
        
        # Verify FX list
        self.assertEqual(len(result["fx"]), 2)  # Only non-empty FX tuples
        
        # Find specific FX tuples
        # Since we have set the context properly, both FX keys should be serialized as strings
        fx0 = next(fx for fx in result["fx"] if fx["index"] == 0)
        # The specific string depends on which enum the value maps to in the current context
        self.assertTrue(isinstance(fx0["key"], str), f"Expected string FX key, got {type(fx0['key']).__name__}")
        self.assertEqual(fx0["value"], 20)
        
        fx2 = next(fx for fx in result["fx"] if fx["index"] == 2)
        self.assertTrue(isinstance(fx2["key"], str), f"Expected string FX key, got {type(fx2['key']).__name__}")
        self.assertEqual(fx2["value"], 40)
        
        # Clean up context
        context.clear()
        
    def test_as_dict_with_instrument_context(self):
        """Test that FX keys are serialized to string enum values when instrument context is available."""
        from m8.core.enums import M8InstrumentContext
        from m8.enums import M8SequencerFX, M8MixerFX, M8InstrumentType
        
        # Set up a direct instrument context
        context = M8InstrumentContext.get_instance()
        context.current_instrument_type_id = M8InstrumentType.WAVSYNTH.value
        
        # Create a step with FX
        step = M8PhraseStep(note="C_6", velocity=100, instrument=0)
        step.fx[0] = M8FXTuple(key=M8SequencerFX.RNL.value, value=96)   # RNL = 7
        step.fx[1] = M8FXTuple(key=M8MixerFX.VMV.value, value=80)       # VMV = 27
        
        # Get the dict representation
        result = step.as_dict()
        
        # Verify that FX keys are serialized as string enum values
        self.assertEqual(len(result["fx"]), 2)
        
        # Find specific FX tuples and verify their keys are string enum values
        fx0 = next(fx for fx in result["fx"] if fx["index"] == 0)
        self.assertEqual(fx0["key"], "RNL")  # Should be string enum name, not 7
        
        fx1 = next(fx for fx in result["fx"] if fx["index"] == 1)
        self.assertEqual(fx1["key"], "VMV")  # Should be string enum name, not 27
        
        # Clean up context
        context.clear()
    
    def test_from_dict(self):
        # Test from_dict method with string note
        data = {
            "note": "C_6",
            "velocity": 100,
            "instrument": 5,
            "fx": [
                {"index": 0, "key": 10, "value": 20},
                {"index": 2, "key": 30, "value": 40}
            ]
        }
        
        step = M8PhraseStep.from_dict(data)
        
        # Verify basic fields
        self.assertEqual(step.note, "C_6")
        self.assertEqual(step.velocity, 100)
        self.assertEqual(step.instrument, 5)
        
        # Verify FX tuples
        self.assertEqual(step.fx[0].key, 10)
        self.assertEqual(step.fx[0].value, 20)
        self.assertTrue(step.fx[1].is_empty())
        self.assertEqual(step.fx[2].key, 30)
        self.assertEqual(step.fx[2].value, 40)


class TestM8Phrase(unittest.TestCase):
    def test_read_from_binary(self):
        # Create minimal test data for a phrase (full data would be quite large)
        # Just test with 2 steps for simplicity
        test_data = bytearray()
        
        # Step 0: note=60, velocity=100, instrument=5, one FX tuple
        step0_data = bytearray([60, 100, 5])
        step0_data.extend([10, 20])  # FX1: key=10, value=20
        step0_data.extend([M8FXTuple.EMPTY_KEY, 0, M8FXTuple.EMPTY_KEY, 0])  # FX2, FX3: empty
        test_data.extend(step0_data)
        
        # Step 1: empty
        step1_data = bytearray([
            M8PhraseStep.EMPTY_NOTE, M8PhraseStep.EMPTY_VELOCITY, M8PhraseStep.EMPTY_INSTRUMENT,
            M8FXTuple.EMPTY_KEY, 0, M8FXTuple.EMPTY_KEY, 0, M8FXTuple.EMPTY_KEY, 0
        ])
        test_data.extend(step1_data)
        
        # Fill remaining steps with empty data
        for _ in range(STEP_COUNT - 2):
            test_data.extend([
                M8PhraseStep.EMPTY_NOTE, M8PhraseStep.EMPTY_VELOCITY, M8PhraseStep.EMPTY_INSTRUMENT,
                M8FXTuple.EMPTY_KEY, 0, M8FXTuple.EMPTY_KEY, 0, M8FXTuple.EMPTY_KEY, 0
            ])
        
        # Read from binary
        phrase = M8Phrase.read(test_data)
        
        # Verify number of steps
        self.assertEqual(len(phrase), STEP_COUNT)
        
        # Verify step 0
        self.assertEqual(phrase[0].note, "C_6")
        self.assertEqual(phrase[0].velocity, 100)
        self.assertEqual(phrase[0].instrument, 5)
        self.assertEqual(phrase[0].fx[0].key, 10)
        self.assertEqual(phrase[0].fx[0].value, 20)
        
        # Verify step 1 and remaining steps are empty
        self.assertTrue(phrase[1].is_empty())
        for i in range(2, STEP_COUNT):
            self.assertTrue(phrase[i].is_empty())
    
    def test_write_to_binary(self):
        # Create a phrase with some data
        phrase = M8Phrase()
        
        # Set up step 0
        phrase[0] = M8PhraseStep(note=60, velocity=100, instrument=5)
        phrase[0].fx[0] = M8FXTuple(key=10, value=20)
        
        # Set up step 2 (skipping step 1)
        phrase[2] = M8PhraseStep(note=72, velocity=80, instrument=3)
        phrase[2].fx[1] = M8FXTuple(key=30, value=40)
        
        # Write to binary
        binary = phrase.write()
        
        # Verify size
        self.assertEqual(len(binary), STEP_COUNT * STEP_BLOCK_SIZE)
        
        # Verify step 0
        self.assertEqual(binary[0], 60)  # note
        self.assertEqual(binary[1], 100)  # velocity
        self.assertEqual(binary[2], 5)  # instrument
        self.assertEqual(binary[3], 10)  # FX1 key
        self.assertEqual(binary[4], 20)  # FX1 value
        
        # Verify step 1 is empty (should be all default values)
        step1_offset = STEP_BLOCK_SIZE
        self.assertEqual(binary[step1_offset], M8PhraseStep.EMPTY_NOTE)
        
        # Verify step 2
        step2_offset = 2 * STEP_BLOCK_SIZE
        self.assertEqual(binary[step2_offset], 72)  # note
        self.assertEqual(binary[step2_offset + 1], 80)  # velocity
        self.assertEqual(binary[step2_offset + 2], 3)  # instrument
        self.assertEqual(binary[step2_offset + 5], 30)  # FX2 key (at offset 5)
        self.assertEqual(binary[step2_offset + 6], 40)  # FX2 value
    
    def test_read_write_consistency(self):
        # Create a phrase with some data
        phrase = M8Phrase()
        
        # Set up steps
        phrase[0] = M8PhraseStep(note=60, velocity=100, instrument=5)
        phrase[0].fx[0] = M8FXTuple(key=10, value=20)
        
        phrase[3] = M8PhraseStep(note=72, velocity=80, instrument=3)
        phrase[3].fx[1] = M8FXTuple(key=30, value=40)
        
        # Write to binary
        binary = phrase.write()
        
        # Read back from binary
        deserialized = M8Phrase.read(binary)
        
        # Verify steps are consistent
        self.assertEqual(deserialized[0].note, "C_6")
        self.assertEqual(deserialized[0].velocity, 100)
        self.assertEqual(deserialized[0].instrument, 5)
        self.assertEqual(deserialized[0].fx[0].key, 10)
        self.assertEqual(deserialized[0].fx[0].value, 20)
        
        self.assertTrue(deserialized[1].is_empty())
        self.assertTrue(deserialized[2].is_empty())
        
        self.assertEqual(deserialized[3].note, "C_7")
        self.assertEqual(deserialized[3].velocity, 80)
        self.assertEqual(deserialized[3].instrument, 3)
        self.assertEqual(deserialized[3].fx[1].key, 30)
        self.assertEqual(deserialized[3].fx[1].value, 40)
        
        # Verify all other steps are empty
        for i in [1, 2] + list(range(4, STEP_COUNT)):
            self.assertTrue(deserialized[i].is_empty())
    
    def test_constructor(self):
        # Test default constructor
        phrase = M8Phrase()
        
        # Should have STEP_COUNT steps
        self.assertEqual(len(phrase), STEP_COUNT)
        
        # All steps should be empty
        for step in phrase:
            self.assertTrue(step.is_empty())
    
    def test_is_empty(self):
        # Test is_empty method
        phrase = M8Phrase()
        self.assertTrue(phrase.is_empty())
        
        # Modify one step
        phrase[0] = M8PhraseStep(note=60, velocity=100, instrument=5)
        self.assertFalse(phrase.is_empty())
        
        # Reset to empty
        phrase[0] = M8PhraseStep()
        self.assertTrue(phrase.is_empty())
        
    def test_is_complete(self):
        # Test is_complete method
        phrase = M8Phrase()
        # Empty phrase is complete
        self.assertTrue(phrase.is_complete())
        
        # Phrase with complete step is complete
        phrase[0] = M8PhraseStep(note="C_6", velocity=100, instrument=5)
        self.assertTrue(phrase.is_complete())
        
        # Phrase with incomplete step is incomplete
        phrase[1] = M8PhraseStep(note="C_6")  # Missing velocity and instrument
        self.assertFalse(phrase.is_complete())
        
        # Fix the incomplete step
        phrase[1].velocity = 100
        phrase[1].instrument = 3
        self.assertTrue(phrase.is_complete())
    
    def test_clone(self):
        # Test clone method
        original = M8Phrase()
        original[0] = M8PhraseStep(note="C_6", velocity=100, instrument=5)
        original[0].fx[0] = M8FXTuple(key=10, value=20)
        
        original[3] = M8PhraseStep(note="C_7", velocity=80, instrument=3)
        original[3].fx[1] = M8FXTuple(key=30, value=40)
        
        clone = original.clone()
        
        # Verify clone has the same values
        self.assertEqual(clone[0].note, "C_6")
        self.assertEqual(clone[0].velocity, 100)
        self.assertEqual(clone[0].instrument, 5)
        self.assertEqual(clone[0].fx[0].key, 10)
        self.assertEqual(clone[0].fx[0].value, 20)
        
        self.assertEqual(clone[3].note, "C_7")
        self.assertEqual(clone[3].velocity, 80)
        self.assertEqual(clone[3].instrument, 3)
        self.assertEqual(clone[3].fx[1].key, 30)
        self.assertEqual(clone[3].fx[1].value, 40)
        
        # Verify clone is a different object
        self.assertIsNot(clone, original)
        
        # Modify clone and verify original remains unchanged
        clone[0].note = "C_5"
        self.assertEqual(original[0].note, "C_6")
    
    def test_validate_references_instruments(self):
        # Create mock instruments list
        mock_instruments = [type('MockInstrument', (), {'is_empty': lambda: False})] * 10
        # Add an M8Block instance which should be treated as empty
        mock_instruments.append(M8Block())
        
        # Test case 1: Valid phrase
        phrase = M8Phrase()
        phrase[0] = M8PhraseStep(note=60, velocity=100, instrument=5)
        phrase[3] = M8PhraseStep(note=72, velocity=80, instrument=3)
        phrase.validate_references_instruments(mock_instruments)  # Should not raise
        
        # Test case 2: Reference to non-existent instrument
        phrase = M8Phrase()
        phrase[0] = M8PhraseStep(note="C_6", velocity=100, instrument=20)  # Instrument 20 doesn't exist
        with self.assertRaises(M8ValidationError):
            phrase.validate_references_instruments(mock_instruments)
        
        # Test case 3: Reference to empty instrument (M8Block)
        phrase = M8Phrase()
        phrase[0] = M8PhraseStep(note="C_6", velocity=100, instrument=10)  # Instrument 10 is an M8Block
        with self.assertRaises(M8ValidationError):
            phrase.validate_references_instruments(mock_instruments)
        
        # Test case 4: Empty phrase should be valid
        phrase = M8Phrase()
        phrase.validate_references_instruments([])  # Should not raise
    
    def test_available_step_slot(self):
        # Test available_step_slot property
        phrase = M8Phrase()  # All slots empty
        self.assertEqual(phrase.available_step_slot, 0)
        
        # Fill first slot
        phrase[0] = M8PhraseStep(note=60, velocity=100, instrument=5)
        self.assertEqual(phrase.available_step_slot, 1)
        
        # Fill all slots
        for i in range(STEP_COUNT):
            phrase[i] = M8PhraseStep(note=60+i, velocity=100, instrument=5)
        self.assertIsNone(phrase.available_step_slot)
    
    def test_add_step(self):
        # Test add_step method
        phrase = M8Phrase()
        step = M8PhraseStep(note="C_6", velocity=100, instrument=5)
        
        # Add step to empty phrase
        slot = phrase.add_step(step)
        self.assertEqual(slot, 0)
        self.assertEqual(phrase[0].note, "C_6")
        
        # Add another step
        step2 = M8PhraseStep(note="C_7", velocity=80, instrument=3)
        slot = phrase.add_step(step2)
        self.assertEqual(slot, 1)
        self.assertEqual(phrase[1].note, "C_7")
        
        # Fill all slots and test error
        for i in range(2, STEP_COUNT):
            phrase[i] = M8PhraseStep(note=60+i, velocity=100, instrument=5)
        
        with self.assertRaises(IndexError):
            phrase.add_step(step)
    
    def test_set_step(self):
        # Test set_step method
        phrase = M8Phrase()
        step = M8PhraseStep(note="C_6", velocity=100, instrument=5)
        
        # Set step at specific slot
        phrase.set_step(step, 3)
        self.assertEqual(phrase[3].note, "C_6")
        
        # Test invalid slot
        with self.assertRaises(IndexError):
            phrase.set_step(step, STEP_COUNT)
        
        with self.assertRaises(IndexError):
            phrase.set_step(step, -1)
    
    def test_as_dict(self):
        # Test as_dict method
        phrase = M8Phrase()
        
        # Add some steps
        phrase[0] = M8PhraseStep(note="C_6", velocity=100, instrument=5)
        phrase[0].fx[0] = M8FXTuple(key=10, value=20)
        
        phrase[3] = M8PhraseStep(note="C_7", velocity=80, instrument=3)
        phrase[3].fx[1] = M8FXTuple(key=30, value=40)
        
        result = phrase.as_dict()
        
        # Should only contain non-empty steps
        self.assertEqual(len(result["steps"]), 2)
        
        # Find specific steps
        step0 = next(s for s in result["steps"] if s["index"] == 0)
        self.assertEqual(step0["note"], "C_6")
        self.assertEqual(step0["velocity"], 100)
        self.assertEqual(step0["instrument"], 5)
        self.assertEqual(len(step0["fx"]), 1)
        self.assertEqual(step0["fx"][0]["key"], 10)
        
        step3 = next(s for s in result["steps"] if s["index"] == 3)
        self.assertEqual(step3["note"], "C_7")
        self.assertEqual(step3["velocity"], 80)
        self.assertEqual(step3["instrument"], 3)
        self.assertEqual(len(step3["fx"]), 1)
        self.assertEqual(step3["fx"][0]["key"], 30)
        
        # Test empty phrase
        phrase = M8Phrase()
        result = phrase.as_dict()
        self.assertEqual(result, {"steps": []})
    
    def test_from_dict(self):
        # Test from_dict method
        data = {
            "steps": [
                {
                    "index": 0,
                    "note": "C_6",
                    "velocity": 100,
                    "instrument": 5,
                    "fx": [
                        {"index": 0, "key": 10, "value": 20}
                    ]
                },
                {
                    "index": 3,
                    "note": "C_7",
                    "velocity": 80,
                    "instrument": 3,
                    "fx": [
                        {"index": 1, "key": 30, "value": 40}
                    ]
                }
            ]
        }
        
        phrase = M8Phrase.from_dict(data)
        
        # Verify steps
        self.assertEqual(phrase[0].note, "C_6")
        self.assertEqual(phrase[0].velocity, 100)
        self.assertEqual(phrase[0].instrument, 5)
        self.assertEqual(phrase[0].fx[0].key, 10)
        self.assertEqual(phrase[0].fx[0].value, 20)
        
        self.assertTrue(phrase[1].is_empty())
        self.assertTrue(phrase[2].is_empty())
        
        self.assertEqual(phrase[3].note, "C_7")
        self.assertEqual(phrase[3].velocity, 80)
        self.assertEqual(phrase[3].instrument, 3)
        self.assertEqual(phrase[3].fx[1].key, 30)
        self.assertEqual(phrase[3].fx[1].value, 40)
        
        # Test with invalid step index
        data = {
            "steps": [
                {
                    "index": STEP_COUNT + 5,  # Out of range
                    "note": 60,
                    "velocity": 100,
                    "instrument": 5
                }
            ]
        }
        
        phrase = M8Phrase.from_dict(data)
        self.assertTrue(phrase.is_empty())


class TestM8Phrases(unittest.TestCase):
    def test_read_from_binary(self):
        # Create minimal test data for simplicity
        # We'll use a very simplified approach since the full data would be enormous
        # Just test with 2 phrases, each with 1 non-empty step
        
        # Create a phrase with one step
        phrase0 = M8Phrase()
        phrase0[0] = M8PhraseStep(note=60, velocity=100, instrument=5)
        phrase0[0].fx[0] = M8FXTuple(key=10, value=20)
        
        # Create another phrase with one step
        phrase1 = M8Phrase()
        phrase1[3] = M8PhraseStep(note=72, velocity=80, instrument=3)
        phrase1[3].fx[1] = M8FXTuple(key=30, value=40)
        
        # Write the phrases to binary
        phrase0_binary = phrase0.write()
        phrase1_binary = phrase1.write()
        
        # Create test data with these two phrases
        test_data = bytearray()
        test_data.extend(phrase0_binary)
        test_data.extend(phrase1_binary)
        
        # Fill the rest with empty phrases
        empty_phrase = M8Phrase()
        empty_phrase_binary = empty_phrase.write()
        for _ in range(PHRASE_COUNT - 2):
            test_data.extend(empty_phrase_binary)
        
        # Read from binary
        phrases = M8Phrases.read(test_data)
        
        # Verify number of phrases
        self.assertEqual(len(phrases), PHRASE_COUNT)
        
        # Verify phrase 0
        self.assertEqual(phrases[0][0].note, "C_6")
        self.assertEqual(phrases[0][0].velocity, 100)
        self.assertEqual(phrases[0][0].instrument, 5)
        self.assertEqual(phrases[0][0].fx[0].key, 10)
        self.assertEqual(phrases[0][0].fx[0].value, 20)
        
        # Verify phrase 1
        self.assertEqual(phrases[1][3].note, "C_7")
        self.assertEqual(phrases[1][3].velocity, 80)
        self.assertEqual(phrases[1][3].instrument, 3)
        self.assertEqual(phrases[1][3].fx[1].key, 30)
        self.assertEqual(phrases[1][3].fx[1].value, 40)
        
        # Verify remaining phrases are empty
        for i in range(2, PHRASE_COUNT):
            self.assertTrue(phrases[i].is_empty())
    
    def test_write_to_binary(self):
        # Test with a simplified set of phrases
        phrases = M8Phrases()
        
        # Set up phrase 0
        phrases[0][0] = M8PhraseStep(note=60, velocity=100, instrument=5)
        phrases[0][0].fx[0] = M8FXTuple(key=10, value=20)
        
        # Set up phrase 2 (skipping phrase 1)
        phrases[2][3] = M8PhraseStep(note=72, velocity=80, instrument=3)
        phrases[2][3].fx[1] = M8FXTuple(key=30, value=40)
        
        # Write to binary
        binary = phrases.write()
        
        # Verify size
        self.assertEqual(len(binary), PHRASE_COUNT * PHRASE_BLOCK_SIZE)
        
        # Full validation of the binary would be complex, so we'll just check
        # that we can read it back properly in the next test
    
    def test_read_write_consistency(self):
        # Create phrases with some data
        phrases = M8Phrases()
        
        # Set up phrase 0
        phrases[0][0] = M8PhraseStep(note=60, velocity=100, instrument=5)
        phrases[0][0].fx[0] = M8FXTuple(key=10, value=20)
        
        # Set up phrase 2
        phrases[2][3] = M8PhraseStep(note=72, velocity=80, instrument=3)
        phrases[2][3].fx[1] = M8FXTuple(key=30, value=40)
        
        # Write to binary
        binary = phrases.write()
        
        # Read back from binary
        deserialized = M8Phrases.read(binary)
        
        # Verify phrase 0
        self.assertEqual(deserialized[0][0].note, "C_6")
        self.assertEqual(deserialized[0][0].velocity, 100)
        self.assertEqual(deserialized[0][0].instrument, 5)
        self.assertEqual(deserialized[0][0].fx[0].key, 10)
        self.assertEqual(deserialized[0][0].fx[0].value, 20)
        
        # Verify phrase 1 is empty
        self.assertTrue(deserialized[1].is_empty())
        
        # Verify phrase 2
        self.assertEqual(deserialized[2][3].note, "C_7")
        self.assertEqual(deserialized[2][3].velocity, 80)
        self.assertEqual(deserialized[2][3].instrument, 3)
        self.assertEqual(deserialized[2][3].fx[1].key, 30)
        self.assertEqual(deserialized[2][3].fx[1].value, 40)
    
    def test_constructor(self):
        # Test default constructor
        phrases = M8Phrases()
        
        # Should have PHRASE_COUNT phrases
        self.assertEqual(len(phrases), PHRASE_COUNT)
        
        # All phrases should be empty
        for phrase in phrases:
            self.assertTrue(phrase.is_empty())
    
    def test_is_empty(self):
        # Test is_empty method
        phrases = M8Phrases()
        self.assertTrue(phrases.is_empty())
        
        # Modify one phrase
        phrases[0][0] = M8PhraseStep(note=60, velocity=100, instrument=5)
        self.assertFalse(phrases.is_empty())
        
        # Reset to empty
        phrases[0][0] = M8PhraseStep()
        self.assertTrue(phrases.is_empty())
        
    def test_is_complete(self):
        # Test is_complete method
        phrases = M8Phrases()
        # Empty phrases collection is complete
        self.assertTrue(phrases.is_complete())
        
        # Phrases with complete steps are complete
        phrases[0][0] = M8PhraseStep(note="C_6", velocity=100, instrument=5)
        phrases[1][3] = M8PhraseStep(note="C_7", velocity=80, instrument=3)
        self.assertTrue(phrases.is_complete())
        
        # Phrases with incomplete step is incomplete
        phrases[2][0] = M8PhraseStep(note="C_6")  # Missing velocity and instrument
        self.assertFalse(phrases.is_complete())
        
        # Fix the incomplete step
        phrases[2][0].velocity = 100
        phrases[2][0].instrument = 3
        self.assertTrue(phrases.is_complete())
    
    def test_clone(self):
        # Test clone method
        original = M8Phrases()
        original[0][0] = M8PhraseStep(note=60, velocity=100, instrument=5)
        original[2][3] = M8PhraseStep(note=72, velocity=80, instrument=3)
        
        clone = original.clone()
        
        # Verify clone has the same values
        self.assertEqual(clone[0][0].note, "C_6")
        self.assertEqual(clone[2][3].note, "C_7")
        
        # Verify clone is a different object
        self.assertIsNot(clone, original)
        
        # Modify clone and verify original remains unchanged
        clone[0][0].note = "C_5"
        self.assertEqual(original[0][0].note, "C_6")
    
    def test_validate_references_instruments(self):
        # Create mock instruments list
        mock_instruments = [type('MockInstrument', (), {'is_empty': lambda: False})] * 10
        
        # Test case 1: Valid phrases
        phrases = M8Phrases()
        phrases[0][0] = M8PhraseStep(note=60, velocity=100, instrument=5)
        phrases[2][3] = M8PhraseStep(note=72, velocity=80, instrument=3)
        phrases.validate_references_instruments(mock_instruments)  # Should not raise
        
        # Test case 2: Reference to non-existent instrument
        phrases = M8Phrases()
        phrases[0][0] = M8PhraseStep(note=60, velocity=100, instrument=20)  # Instrument 20 doesn't exist
        with self.assertRaises(M8ValidationError):
            phrases.validate_references_instruments(mock_instruments)
    
    def test_as_list(self):
        # Test as_list method
        phrases = M8Phrases()
        
        # Add some data
        phrases[0][0] = M8PhraseStep(note=60, velocity=100, instrument=5)
        phrases[0][0].fx[0] = M8FXTuple(key=10, value=20)
        
        phrases[2][3] = M8PhraseStep(note=72, velocity=80, instrument=3)
        phrases[2][3].fx[1] = M8FXTuple(key=30, value=40)
        
        result = phrases.as_list()
        
        # Should only contain non-empty phrases
        self.assertEqual(len(result), 2)
        
        # Find specific phrases
        phrase0 = next(p for p in result if p["index"] == 0)
        self.assertEqual(len(phrase0["steps"]), 1)
        self.assertEqual(phrase0["steps"][0]["note"], "C_6")
        
        phrase2 = next(p for p in result if p["index"] == 2)
        self.assertEqual(len(phrase2["steps"]), 1)
        self.assertEqual(phrase2["steps"][0]["note"], "C_7")
        
        # Test empty phrases
        phrases = M8Phrases()
        result = phrases.as_list()
        self.assertEqual(result, [])
    
    def test_from_list(self):
        # Test from_list method
        data = [
            {
                "index": 0,
                "steps": [
                    {
                        "index": 0,
                        "note": 60,
                        "velocity": 100,
                        "instrument": 5,
                        "fx": [
                            {"index": 0, "key": 10, "value": 20}
                        ]
                    }
                ]
            },
            {
                "index": 2,
                "steps": [
                    {
                        "index": 3,
                        "note": 72,
                        "velocity": 80,
                        "instrument": 3,
                        "fx": [
                            {"index": 1, "key": 30, "value": 40}
                        ]
                    }
                ]
            }
        ]
        
        phrases = M8Phrases.from_list(data)
        
        # Verify phrase 0
        self.assertEqual(phrases[0][0].note, "C_6")
        self.assertEqual(phrases[0][0].velocity, 100)
        self.assertEqual(phrases[0][0].instrument, 5)
        self.assertEqual(phrases[0][0].fx[0].key, 10)
        self.assertEqual(phrases[0][0].fx[0].value, 20)
        
        # Verify phrase 1 is empty
        self.assertTrue(phrases[1].is_empty())
        
        # Verify phrase 2
        self.assertEqual(phrases[2][3].note, "C_7")
        self.assertEqual(phrases[2][3].velocity, 80)
        self.assertEqual(phrases[2][3].instrument, 3)
        self.assertEqual(phrases[2][3].fx[1].key, 30)
        self.assertEqual(phrases[2][3].fx[1].value, 40)
        
        # Test with invalid phrase index
        data = [
            {
                "index": PHRASE_COUNT + 5,  # Out of range
                "steps": [
                    {
                        "index": 0,
                        "note": 60,
                        "velocity": 100,
                        "instrument": 5
                    }
                ]
            }
        ]
        
        phrases = M8Phrases.from_list(data)
        self.assertTrue(phrases.is_empty())

if __name__ == '__main__':
    unittest.main()