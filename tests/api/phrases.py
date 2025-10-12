import unittest
from m8.api.phrases import (
    M8PhraseStep, M8Phrase, M8Phrases,
    STEP_BLOCK_SIZE, STEP_COUNT, PHRASE_BLOCK_SIZE, PHRASE_COUNT, FX_BLOCK_COUNT
)
from m8.api.fx import M8FXTuple, M8FXTuples
from m8.api import M8Block
# Test constants - using hardcoded values since we removed enums
TEST_NOTE_C6 = 72  # C_6 note value
TEST_NOTE_C7 = 84  # C_7 note value
TEST_FX_RMX = 0x08
TEST_FX_DEL = 0x06

class TestM8PhraseStepEssential(unittest.TestCase):
    """Essential phrase step tests focusing on core functionality."""
    
    def test_constructor_and_defaults(self):
        # Test default constructor
        step = M8PhraseStep()
        self.assertEqual(step.note, M8PhraseStep.EMPTY_NOTE)
        self.assertEqual(step.velocity, M8PhraseStep.EMPTY_VELOCITY)
        self.assertEqual(step.instrument, M8PhraseStep.EMPTY_INSTRUMENT)
        self.assertEqual(len(step.fx), FX_BLOCK_COUNT)
        
        # Test with numeric note parameter (simplified enum system)
        step = M8PhraseStep(note=TEST_NOTE_C6, velocity=100, instrument=5)
        self.assertEqual(step.note, TEST_NOTE_C6)
        self.assertEqual(step.velocity, 100)
        self.assertEqual(step.instrument, 5)
    
    def test_read_write_consistency(self):
        # Create a step with some data
        original = M8PhraseStep(note=TEST_NOTE_C6, velocity=100, instrument=5)
        original.fx[0] = M8FXTuple(key=TEST_FX_RMX, value=20)
        original.fx[1] = M8FXTuple(key=TEST_FX_DEL, value=40)
        
        # Write to binary
        binary = original.write()
        
        # Read back from binary
        deserialized = M8PhraseStep.read(binary)
        
        # Verify all fields match
        self.assertEqual(deserialized.note, original.note)
        self.assertEqual(deserialized.velocity, original.velocity)
        self.assertEqual(deserialized.instrument, original.instrument)
        self.assertEqual(deserialized.fx[0].key, original.fx[0].key)
        self.assertEqual(deserialized.fx[0].value, original.fx[0].value)
        self.assertEqual(deserialized.fx[1].key, original.fx[1].key)
        self.assertEqual(deserialized.fx[1].value, original.fx[1].value)
    


class TestM8PhraseEssential(unittest.TestCase):
    """Essential phrase tests focusing on core functionality."""
    
    def test_constructor(self):
        # Test default constructor
        phrase = M8Phrase()
        self.assertEqual(len(phrase), STEP_COUNT)
        for step in phrase:
            self.assertEqual(step.note, M8PhraseStep.EMPTY_NOTE)
    
    def test_read_write_consistency(self):
        # Create a phrase with some steps
        original = M8Phrase()
        original[0] = M8PhraseStep(note=TEST_NOTE_C6, velocity=100, instrument=5)
        original[0].fx[0] = M8FXTuple(key=TEST_FX_RMX, value=20)
        original[3] = M8PhraseStep(note=TEST_NOTE_C7, velocity=80, instrument=3)
        original[3].fx[1] = M8FXTuple(key=TEST_FX_DEL, value=40)
        
        # Write to binary
        binary = original.write()
        
        # Read back from binary
        deserialized = M8Phrase.read(binary)
        
        # Verify steps are consistent
        self.assertEqual(deserialized[0].note, original[0].note)
        self.assertEqual(deserialized[0].velocity, original[0].velocity)
        self.assertEqual(deserialized[0].instrument, original[0].instrument)
        self.assertEqual(deserialized[0].fx[0].key, original[0].fx[0].key)
        self.assertEqual(deserialized[0].fx[0].value, original[0].fx[0].value)
        
        self.assertEqual(deserialized[3].note, original[3].note)
        self.assertEqual(deserialized[3].velocity, original[3].velocity)
        self.assertEqual(deserialized[3].instrument, original[3].instrument)
    

class TestM8PhrasesEssential(unittest.TestCase):
    """Essential phrases collection tests focusing on core functionality."""
    
    def test_constructor(self):
        # Test default constructor
        phrases = M8Phrases()
        self.assertEqual(len(phrases), PHRASE_COUNT)
        # All phrases are empty by default

    def test_read_write_consistency(self):
        # Create phrases with some data
        original = M8Phrases()
        original[0][0] = M8PhraseStep(note=TEST_NOTE_C6, velocity=100, instrument=5)
        original[0][0].fx[0] = M8FXTuple(key=TEST_FX_RMX, value=20)
        original[2][3] = M8PhraseStep(note=TEST_NOTE_C7, velocity=80, instrument=3)
        original[2][3].fx[1] = M8FXTuple(key=TEST_FX_DEL, value=40)
        
        # Write to binary
        binary = original.write()
        
        # Read back from binary
        deserialized = M8Phrases.read(binary)
        
        # Verify phrase 0
        self.assertEqual(deserialized[0][0].note, original[0][0].note)
        self.assertEqual(deserialized[0][0].velocity, original[0][0].velocity)
        self.assertEqual(deserialized[0][0].instrument, original[0][0].instrument)
        
        # Verify phrase 2
        self.assertEqual(deserialized[2][3].note, original[2][3].note)
        self.assertEqual(deserialized[2][3].velocity, original[2][3].velocity)
        self.assertEqual(deserialized[2][3].instrument, original[2][3].instrument)
    
