# tests/api/instruments/__init__.py
import unittest
import os
import tempfile
from m8.api.sampler import M8SamplerParams, M8Sampler, BLOCK_SIZE, BLOCK_COUNT
from m8.api.instruments import M8Instruments

# Legacy aliases
M8InstrumentParams = M8SamplerParams
M8Instrument = M8Sampler
from m8.api import M8Block

class TestM8InstrumentParams(unittest.TestCase):
    def test_constructor_and_defaults(self):
        # Test default constructor
        params = M8InstrumentParams()
        self.assertEqual(params.play_mode, 0)
        self.assertEqual(params.slice, 0)
        self.assertEqual(params.sample_path, "")

        # Test with kwargs
        params = M8InstrumentParams(play_mode=1, slice=5, sample_path="/path/to/sample.wav")
        self.assertEqual(params.play_mode, 1)
        self.assertEqual(params.slice, 5)
        self.assertEqual(params.sample_path, "/path/to/sample.wav")

    def test_read_write_consistency(self):
        # Create original params
        original = M8InstrumentParams(play_mode=2, slice=10, sample_path="/test.wav")

        # Write to binary
        binary = original.write()

        # Read back from binary
        params = M8InstrumentParams()
        params.read(binary)

        # Check values match
        self.assertEqual(params.play_mode, original.play_mode)
        self.assertEqual(params.slice, original.slice)
        self.assertEqual(params.sample_path, original.sample_path)

    def test_clone(self):
        # Create params
        original = M8InstrumentParams(play_mode=3, slice=7, sample_path="/sample.wav")

        # Clone it
        clone = original.clone()

        # Check values match
        self.assertEqual(clone.play_mode, original.play_mode)
        self.assertEqual(clone.slice, original.slice)
        self.assertEqual(clone.sample_path, original.sample_path)

        # Verify they're separate instances
        self.assertIsNot(clone, original)

        # Modify clone and verify original unchanged
        clone.play_mode = 5
        self.assertEqual(original.play_mode, 3)


class TestInstrumentBase(unittest.TestCase):
    def test_constructor_and_defaults(self):
        # Test default constructor
        instrument = M8Instrument()
        self.assertEqual(instrument.name, "")
        # volume, pitch, transpose, eq, table_tick, finetune use config defaults

        # Test with kwargs
        instrument = M8Instrument(name="TestSynth", sample_path="/test.wav")
        self.assertEqual(instrument.name, "TestSynth")
        self.assertEqual(instrument.params.sample_path, "/test.wav")

    def test_write(self):
        # Create instrument
        instrument = M8Instrument(name="Test")

        # Write to binary
        binary = instrument.write()

        # Should be exactly BLOCK_SIZE bytes
        self.assertEqual(len(binary), BLOCK_SIZE)

    def test_read_common_parameters(self):
        # Create an instrument
        instrument = M8Instrument(name="TestInstr")

        # Write to binary
        binary = instrument.write()

        # Read it back
        read_instrument = M8Instrument.read(binary)

        # Check common parameters
        self.assertEqual(read_instrument.name, "TestInstr")

    def test_clone(self):
        # Create instrument
        original = M8Instrument(name="Original", sample_path="/test.wav", slice=5)

        # Clone it
        clone = original.clone()

        # Check values match
        self.assertEqual(clone.name, original.name)
        self.assertEqual(clone.params.sample_path, original.params.sample_path)
        self.assertEqual(clone.params.slice, original.params.slice)

        # Verify they're separate instances
        self.assertIsNot(clone, original)
        self.assertIsNot(clone.params, original.params)

        # Modify clone and verify original unchanged
        clone.name = "Modified"
        self.assertEqual(original.name, "Original")

    def test_is_empty(self):
        # New sampler instrument should not be empty
        instrument = M8Instrument(name="Test")
        self.assertFalse(instrument.is_empty())


class TestInstrumentFileIO(unittest.TestCase):
    def test_write_to_file(self):
        # Create instrument
        instrument = M8Instrument(name="FileTest", sample_path="/test.wav")

        # Write to temporary file
        with tempfile.NamedTemporaryFile(suffix='.m8i', delete=False) as tmp:
            try:
                tmp_path = tmp.name
                instrument.write_to_file(tmp_path)

                # Verify file exists
                self.assertTrue(os.path.exists(tmp_path))

                # Verify file has content
                with open(tmp_path, 'rb') as f:
                    data = f.read()
                self.assertGreater(len(data), 0)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    def test_read_from_file(self):
        # Skip if template not available
        try:
            from m8.api.project import M8Project
            project = M8Project.initialise()
        except FileNotFoundError:
            self.skipTest("Template file not found")
            return

        # Create and write instrument
        instrument = M8Instrument(name="ReadTest", sample_path="/sample.wav", slice=7)

        with tempfile.NamedTemporaryFile(suffix='.m8i', delete=False) as tmp:
            try:
                tmp_path = tmp.name
                instrument.write_to_file(tmp_path)

                # Read it back
                read_instrument = M8Instrument.read_from_file(tmp_path)

                # Check values
                self.assertEqual(read_instrument.name, "ReadTest")
                self.assertEqual(read_instrument.params.sample_path, "/sample.wav")
                self.assertEqual(read_instrument.params.slice, 7)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    def test_round_trip(self):
        # Create instrument
        original = M8Instrument(
            name="RoundTrip",
            sample_path="/path/to/file.wav",
            play_mode=1,
            slice=12
        )

        with tempfile.NamedTemporaryFile(suffix='.m8i', delete=False) as tmp:
            try:
                tmp_path = tmp.name

                # Write
                original.write_to_file(tmp_path)

                # Read
                read_instrument = M8Instrument.read_from_file(tmp_path)

                # Compare
                self.assertEqual(read_instrument.name, original.name)
                self.assertEqual(read_instrument.params.sample_path, original.params.sample_path)
                self.assertEqual(read_instrument.params.play_mode, original.params.play_mode)
                self.assertEqual(read_instrument.params.slice, original.params.slice)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)


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
        # Create instruments collection with one instrument
        instruments = M8Instruments()
        instruments[0] = M8Instrument(name="Test1", sample_path="/test1.wav")
        instruments[5] = M8Instrument(name="Test2", slice=3)

        # Write to binary
        binary = instruments.write()

        # Read back
        read_instruments = M8Instruments.read(binary)

        # Check count
        self.assertEqual(len(read_instruments), BLOCK_COUNT)

        # Check specific instruments
        self.assertIsInstance(read_instruments[0], M8Instrument)
        self.assertEqual(read_instruments[0].name, "Test1")

        self.assertIsInstance(read_instruments[5], M8Instrument)
        self.assertEqual(read_instruments[5].name, "Test2")

        # Check empty slots
        self.assertIsInstance(read_instruments[1], M8Block)

    def test_write_to_binary(self):
        instruments = M8Instruments()
        instruments[0] = M8Instrument(name="Test")

        binary = instruments.write()

        # Should be BLOCK_COUNT * BLOCK_SIZE bytes
        self.assertEqual(len(binary), BLOCK_COUNT * BLOCK_SIZE)

    def test_read_write_consistency(self):
        # Create collection
        original = M8Instruments()
        original[0] = M8Instrument(name="Instr1", sample_path="/path1.wav")
        original[10] = M8Instrument(name="Instr2", slice=5)

        # Write and read
        binary = original.write()
        read_instruments = M8Instruments.read(binary)

        # Check instruments match
        self.assertEqual(read_instruments[0].name, "Instr1")
        self.assertEqual(read_instruments[0].params.sample_path, "/path1.wav")
        self.assertEqual(read_instruments[10].name, "Instr2")
        self.assertEqual(read_instruments[10].params.slice, 5)

    def test_clone(self):
        original = M8Instruments()
        original[0] = M8Instrument(name="Original")

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

    def test_is_empty(self):
        instruments = M8Instruments()
        self.assertTrue(instruments.is_empty())

        instruments[0] = M8Instrument(name="Test")
        self.assertFalse(instruments.is_empty())


if __name__ == '__main__':
    unittest.main()
