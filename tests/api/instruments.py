# tests/api/instruments/__init__.py
import unittest
import os
import tempfile
from m8.api.sampler import M8Sampler, BLOCK_SIZE, BLOCK_COUNT
from m8.api.instrument import M8Instruments
from m8.api import M8Block


class TestInstrumentBase(unittest.TestCase):
    def test_constructor_and_defaults(self):
        # Test default constructor
        instrument = M8Sampler()
        self.assertEqual(instrument.name, "")
        # volume, pitch, transpose, eq, table_tick, finetune use config defaults

        # Test with kwargs
        instrument = M8Sampler(name="TestSynth", sample_path="/test.wav")
        self.assertEqual(instrument.name, "TestSynth")
        self.assertEqual(instrument.sample_path, "/test.wav")

    def test_write(self):
        # Create instrument
        instrument = M8Sampler(name="Test")

        # Write to binary
        binary = instrument.write()

        # Should be exactly BLOCK_SIZE bytes
        self.assertEqual(len(binary), BLOCK_SIZE)

    def test_read_common_parameters(self):
        # Create an instrument
        instrument = M8Sampler(name="TestInstr")

        # Write to binary
        binary = instrument.write()

        # Read it back
        read_instrument = M8Sampler.read(binary)

        # Check common parameters
        self.assertEqual(read_instrument.name, "TestInstr")

    def test_clone(self):
        # Create instrument
        original = M8Sampler(name="Original", sample_path="/test.wav")

        # Clone it
        clone = original.clone()

        # Check values match
        self.assertEqual(clone.name, original.name)
        self.assertEqual(clone.sample_path, original.sample_path)

        # Verify they're separate instances
        self.assertIsNot(clone, original)

        # Modify clone and verify original unchanged
        clone.name = "Modified"
        self.assertEqual(original.name, "Original")


class TestM8Instruments(unittest.TestCase):
    def test_constructor(self):
        # Test default constructor
        instruments = M8Instruments()

        # Should have BLOCK_COUNT slots
        self.assertEqual(len(instruments), BLOCK_COUNT)

        # All should be empty blocks
        for instr in instruments:
            self.assertIsInstance(instr, M8Block)

    def test_read_from_binary(self):
        # Create instruments collection with samplers
        instruments = M8Instruments()
        instruments[0] = M8Sampler(name="Test1", sample_path="/test1.wav")
        instruments[5] = M8Sampler(name="Test2", sample_path="/test2.wav")

        # Write to binary
        binary = instruments.write()

        # Read back
        read_instruments = M8Instruments.read(binary)

        # Check count
        self.assertEqual(len(read_instruments), BLOCK_COUNT)

        # Check specific instruments
        self.assertIsInstance(read_instruments[0], M8Sampler)
        self.assertEqual(read_instruments[0].name, "Test1")

        self.assertIsInstance(read_instruments[5], M8Sampler)
        self.assertEqual(read_instruments[5].name, "Test2")

        # Check empty slots
        self.assertIsInstance(read_instruments[1], M8Block)

    def test_write_to_binary(self):
        instruments = M8Instruments()
        instruments[0] = M8Sampler(name="Test")

        binary = instruments.write()

        # Should be BLOCK_COUNT * BLOCK_SIZE bytes
        self.assertEqual(len(binary), BLOCK_COUNT * BLOCK_SIZE)

    def test_read_write_consistency(self):
        # Create collection
        original = M8Instruments()
        original[0] = M8Sampler(name="Instr1", sample_path="/path1.wav")
        original[10] = M8Sampler(name="Instr2", sample_path="/path2.wav")

        # Write and read
        binary = original.write()
        read_instruments = M8Instruments.read(binary)

        # Check instruments match
        self.assertEqual(read_instruments[0].name, "Instr1")
        self.assertEqual(read_instruments[0].sample_path, "/path1.wav")
        self.assertEqual(read_instruments[10].name, "Instr2")
        self.assertEqual(read_instruments[10].sample_path, "/path2.wav")

    def test_clone(self):
        original = M8Instruments()
        original[0] = M8Sampler(name="Original")

        clone = original.clone()

        # Check length
        self.assertEqual(len(clone), len(original))

        # Check value
        self.assertEqual(clone[0].name, "Original")

        # Verify separate instances
        self.assertIsNot(clone, original)
        self.assertIsNot(clone[0], original[0])

        # Modify clone
        clone[0].name = "Modified"
        self.assertEqual(original[0].name, "Original")


if __name__ == '__main__':
    unittest.main()
