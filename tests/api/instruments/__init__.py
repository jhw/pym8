# tests/api/instruments/__init__.py
import unittest
import os
import tempfile
from m8.api.instruments import M8InstrumentParams, M8Instrument, M8Instruments, BLOCK_SIZE, BLOCK_COUNT
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

    def test_as_dict(self):
        params = M8InstrumentParams(play_mode=1, slice=3, sample_path="/test.wav")
        result = params.as_dict()

        expected = {
            "play_mode": 1,
            "slice": 3,
            "sample_path": "/test.wav"
        }
        self.assertEqual(result, expected)

    def test_from_dict(self):
        data = {
            "play_mode": 2,
            "slice": 8,
            "sample_path": "/path/sample.wav"
        }

        params = M8InstrumentParams.from_dict(data)

        self.assertEqual(params.play_mode, 2)
        self.assertEqual(params.slice, 8)
        self.assertEqual(params.sample_path, "/path/sample.wav")


class TestInstrumentBase(unittest.TestCase):
    def test_constructor_and_defaults(self):
        # Test default constructor
        instrument = M8Instrument()
        self.assertEqual(instrument.name, "")
        self.assertEqual(instrument.volume, 255)
        self.assertEqual(instrument.pitch, 64)
        self.assertEqual(instrument.transpose, 4)
        self.assertEqual(instrument.eq, 1)
        self.assertEqual(instrument.table_tick, 1)
        self.assertEqual(instrument.finetune, 128)

        # Test with kwargs
        instrument = M8Instrument(name="TestSynth", volume=200, sample_path="/test.wav")
        self.assertEqual(instrument.name, "TestSynth")
        self.assertEqual(instrument.volume, 200)
        self.assertEqual(instrument.params.sample_path, "/test.wav")

    def test_write(self):
        # Create instrument
        instrument = M8Instrument(name="Test", volume=200)

        # Write to binary
        binary = instrument.write()

        # Should be exactly BLOCK_SIZE bytes
        self.assertEqual(len(binary), BLOCK_SIZE)

    def test_read_common_parameters(self):
        # Create an instrument
        instrument = M8Instrument(name="TestInstr", volume=180, pitch=70)

        # Write to binary
        binary = instrument.write()

        # Read it back
        read_instrument = M8Instrument.read(binary)

        # Check common parameters
        self.assertEqual(read_instrument.name, "TestInstr")
        self.assertEqual(read_instrument.volume, 180)
        self.assertEqual(read_instrument.pitch, 70)

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

    def test_as_dict(self):
        instrument = M8Instrument(name="Test", volume=200, sample_path="/test.wav", slice=3)
        result = instrument.as_dict()

        self.assertEqual(result["name"], "Test")
        self.assertEqual(result["volume"], 200)
        self.assertEqual(result["sample_path"], "/test.wav")
        self.assertEqual(result["slice"], 3)

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
            slice=12,
            volume=220,
            pitch=72
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
                self.assertEqual(read_instrument.volume, original.volume)
                self.assertEqual(read_instrument.pitch, original.pitch)
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

    def test_as_list(self):
        instruments = M8Instruments()
        instruments[0] = M8Instrument(name="First", sample_path="/first.wav")
        instruments[5] = M8Instrument(name="Second", slice=3)

        result = instruments.as_list()

        # Should only include non-empty instruments
        self.assertEqual(len(result), 2)

        # Check first instrument
        first = next(item for item in result if item["index"] == 0)
        self.assertEqual(first["name"], "First")
        self.assertEqual(first["sample_path"], "/first.wav")

        # Check second instrument
        second = next(item for item in result if item["index"] == 5)
        self.assertEqual(second["name"], "Second")
        self.assertEqual(second["slice"], 3)

    def test_from_list(self):
        data = [
            {"index": 0, "name": "First", "sample_path": "/first.wav", "volume": 200},
            {"index": 7, "name": "Second", "slice": 5}
        ]

        instruments = M8Instruments.from_list(data)

        # Check length
        self.assertEqual(len(instruments), BLOCK_COUNT)

        # Check instruments
        self.assertEqual(instruments[0].name, "First")
        self.assertEqual(instruments[0].params.sample_path, "/first.wav")
        self.assertEqual(instruments[0].volume, 200)

        self.assertEqual(instruments[7].name, "Second")
        self.assertEqual(instruments[7].params.slice, 5)

        # Check empty slots
        self.assertIsInstance(instruments[1], M8Block)


if __name__ == '__main__':
    unittest.main()
