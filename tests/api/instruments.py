# tests/api/instruments.py
import unittest
import os
import tempfile
from m8.api.instruments.sampler import M8Sampler, BLOCK_SIZE, BLOCK_COUNT
from m8.api.instruments.wavsynth import M8Wavsynth
from m8.api.instruments.macrosynth import M8Macrosynth
from m8.api.instruments.fmsynth import M8FMSynth
from m8.api.instruments.external import M8External
from m8.api.instrument import M8Instrument, M8Instruments, M8InstrumentType, M8FilterType, M8LimiterType
from m8.api import M8Block


class TestInstrumentBase(unittest.TestCase):
    """Tests for base M8Instrument functionality."""

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


class TestInstrumentTypeEnum(unittest.TestCase):
    """Tests for M8InstrumentType enum."""

    def test_instrument_type_values(self):
        """Test instrument type enum has correct values."""
        self.assertEqual(M8InstrumentType.WAVSYNTH, 0)
        self.assertEqual(M8InstrumentType.MACROSYNTH, 1)
        self.assertEqual(M8InstrumentType.SAMPLER, 2)
        self.assertEqual(M8InstrumentType.MIDIOUT, 3)
        self.assertEqual(M8InstrumentType.FMSYNTH, 4)
        self.assertEqual(M8InstrumentType.HYPERSYNTH, 5)
        self.assertEqual(M8InstrumentType.EXTERNAL, 6)

    def test_instrument_type_lookup(self):
        """Test looking up instrument types by value."""
        self.assertEqual(M8InstrumentType(0), M8InstrumentType.WAVSYNTH)
        self.assertEqual(M8InstrumentType(2), M8InstrumentType.SAMPLER)
        self.assertEqual(M8InstrumentType(4), M8InstrumentType.FMSYNTH)


class TestFilterTypeEnum(unittest.TestCase):
    """Tests for M8FilterType enum."""

    def test_filter_type_values(self):
        """Test filter type enum has correct values."""
        self.assertEqual(M8FilterType.OFF, 0x00)
        self.assertEqual(M8FilterType.LOWPASS, 0x01)
        self.assertEqual(M8FilterType.HIGHPASS, 0x02)
        self.assertEqual(M8FilterType.BANDPASS, 0x03)
        self.assertEqual(M8FilterType.BANDSTOP, 0x04)
        self.assertEqual(M8FilterType.LP_HP, 0x05)
        self.assertEqual(M8FilterType.ZDF_LP, 0x06)
        self.assertEqual(M8FilterType.ZDF_HP, 0x07)


class TestLimiterTypeEnum(unittest.TestCase):
    """Tests for M8LimiterType enum."""

    def test_limiter_type_values(self):
        """Test limiter type enum has correct values."""
        self.assertEqual(M8LimiterType.CLIP, 0x00)
        self.assertEqual(M8LimiterType.SIN, 0x01)
        self.assertEqual(M8LimiterType.FOLD, 0x02)
        self.assertEqual(M8LimiterType.WRAP, 0x03)
        self.assertEqual(M8LimiterType.POST, 0x04)


class TestInstrumentFactoryPattern(unittest.TestCase):
    """Tests for M8Instrument factory pattern via from_dict."""

    def test_factory_creates_sampler(self):
        """Test factory creates Sampler from type field."""
        params = {
            'type': 'SAMPLER',
            'name': 'TestSampler',
            'params': {},
            'modulators': []
        }
        instrument = M8Instrument.from_dict(params)
        self.assertIsInstance(instrument, M8Sampler)
        self.assertEqual(instrument.name, 'TestSampler')

    def test_factory_creates_wavsynth(self):
        """Test factory creates Wavsynth from type field."""
        params = {
            'type': 'WAVSYNTH',
            'name': 'TestWavsynth',
            'params': {},
            'modulators': []
        }
        instrument = M8Instrument.from_dict(params)
        self.assertIsInstance(instrument, M8Wavsynth)
        self.assertEqual(instrument.name, 'TestWavsynth')

    def test_factory_creates_macrosynth(self):
        """Test factory creates Macrosynth from type field."""
        params = {
            'type': 'MACROSYNTH',
            'name': 'TestMacro',
            'params': {},
            'modulators': []
        }
        instrument = M8Instrument.from_dict(params)
        self.assertIsInstance(instrument, M8Macrosynth)
        self.assertEqual(instrument.name, 'TestMacro')

    def test_factory_creates_fmsynth(self):
        """Test factory creates FMSynth from type field."""
        params = {
            'type': 'FMSYNTH',
            'name': 'TestFM',
            'params': {},
            'modulators': []
        }
        instrument = M8Instrument.from_dict(params)
        self.assertIsInstance(instrument, M8FMSynth)
        self.assertEqual(instrument.name, 'TestFM')

    def test_factory_creates_external(self):
        """Test factory creates External from type field."""
        params = {
            'type': 'EXTERNAL',
            'name': 'TestExt',
            'params': {},
            'modulators': []
        }
        instrument = M8Instrument.from_dict(params)
        self.assertIsInstance(instrument, M8External)
        self.assertEqual(instrument.name, 'TestExt')

    def test_factory_with_integer_type(self):
        """Test factory works with integer type values."""
        params = {
            'type': M8InstrumentType.SAMPLER,
            'name': 'IntTypeSampler',
            'params': {},
            'modulators': []
        }
        instrument = M8Instrument.from_dict(params)
        self.assertIsInstance(instrument, M8Sampler)

    def test_factory_unknown_type_raises(self):
        """Test factory raises error for unknown type."""
        params = {
            'type': 'UNKNOWN_TYPE',
            'name': 'Test',
            'params': {},
            'modulators': []
        }
        with self.assertRaises(ValueError):
            M8Instrument.from_dict(params)


class TestInstrumentDictSerialization(unittest.TestCase):
    """Tests for to_dict/from_dict serialization."""

    def test_sampler_to_dict_value_mode(self):
        """Test sampler to_dict with value mode."""
        sampler = M8Sampler(name="TestSampler")
        d = sampler.to_dict(enum_mode='value')

        self.assertEqual(d['type'], M8InstrumentType.SAMPLER)
        self.assertEqual(d['name'], 'TestSampler')
        self.assertIn('params', d)
        self.assertIn('modulators', d)

    def test_sampler_to_dict_name_mode(self):
        """Test sampler to_dict with name mode."""
        sampler = M8Sampler(name="TestSampler")
        d = sampler.to_dict(enum_mode='name')

        self.assertEqual(d['type'], 'SAMPLER')
        self.assertEqual(d['name'], 'TestSampler')

    def test_roundtrip_sampler(self):
        """Test sampler dict roundtrip preserves values."""
        original = M8Sampler(name="RoundtripTest", sample_path="/test/path.wav")
        d = original.to_dict(enum_mode='name')

        restored = M8Sampler.from_dict(d)

        self.assertEqual(restored.name, original.name)
        self.assertEqual(restored.sample_path, original.sample_path)

    def test_roundtrip_wavsynth(self):
        """Test wavsynth dict roundtrip preserves values."""
        original = M8Wavsynth(name="WavRoundtrip")
        d = original.to_dict(enum_mode='name')

        restored = M8Wavsynth.from_dict(d)
        self.assertEqual(restored.name, original.name)

    def test_roundtrip_via_factory(self):
        """Test dict roundtrip via factory preserves type and values."""
        original = M8FMSynth(name="FMFactory")
        d = original.to_dict(enum_mode='name')

        # Use factory pattern
        restored = M8Instrument.from_dict(d)

        self.assertIsInstance(restored, M8FMSynth)
        self.assertEqual(restored.name, original.name)


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
