import unittest
from m8.api.instruments.wavsynth import M8Wavsynth, DEFAULT_PARAMETERS, M8WavsynthParam, M8WavShape
from m8.api.instrument import MODULATORS_OFFSET
from m8.api.modulator import M8Modulators


class TestM8Wavsynth(unittest.TestCase):
    def setUp(self):
        # Define Wavsynth-specific parameters
        self.test_name = "TestWavsynth"

    def test_constructor_and_defaults(self):
        # Test default constructor
        wavsynth = M8Wavsynth()

        # Check type is set correctly
        self.assertEqual(wavsynth.get(M8WavsynthParam.TYPE), 0x00)  # WAVSYNTH type_id is 0

        # Check default parameters
        self.assertEqual(wavsynth.name, "")

        # Check non-zero defaults using generic get
        self.assertEqual(wavsynth.get(M8WavsynthParam.FINE_TUNE), 0x80)  # FINETUNE
        self.assertEqual(wavsynth.get(M8WavsynthParam.CUTOFF), 0xFF)    # CUTOFF
        self.assertEqual(wavsynth.get(M8WavsynthParam.PAN), 0x80)       # PAN
        self.assertEqual(wavsynth.get(M8WavsynthParam.DRY), 0xC0)       # DRY

    def test_constructor_with_parameters(self):
        # Test with name
        wavsynth = M8Wavsynth(name=self.test_name)

        # Check parameters
        self.assertEqual(wavsynth.name, self.test_name)

        # Set custom values using generic set
        wavsynth.set(M8WavsynthParam.CUTOFF, 0x20)
        wavsynth.set(M8WavsynthParam.RESONANCE, 0xC0)
        wavsynth.set(M8WavsynthParam.SHAPE, M8WavShape.SAW)
        wavsynth.set(M8WavsynthParam.SIZE, 0x40)

        # Verify using get
        self.assertEqual(wavsynth.get(M8WavsynthParam.CUTOFF), 0x20)
        self.assertEqual(wavsynth.get(M8WavsynthParam.RESONANCE), 0xC0)
        self.assertEqual(wavsynth.get(M8WavsynthParam.SHAPE), M8WavShape.SAW)
        self.assertEqual(wavsynth.get(M8WavsynthParam.SIZE), 0x40)

    def test_binary_serialization(self):
        # Create wavsynth with custom parameters
        wavsynth = M8Wavsynth(name="TEST")
        wavsynth.set(M8WavsynthParam.CUTOFF, 0x20)
        wavsynth.set(M8WavsynthParam.RESONANCE, 0xC0)
        wavsynth.set(M8WavsynthParam.SHAPE, M8WavShape.SINE)
        wavsynth.set(M8WavsynthParam.SIZE, 0x80)

        # Write to binary
        binary = wavsynth.write()

        # Read it back
        read_wavsynth = M8Wavsynth.read(binary)

        # Check all parameters were preserved
        self.assertEqual(read_wavsynth.name, "TEST")
        self.assertEqual(read_wavsynth.get(M8WavsynthParam.CUTOFF), 0x20)
        self.assertEqual(read_wavsynth.get(M8WavsynthParam.RESONANCE), 0xC0)
        self.assertEqual(read_wavsynth.get(M8WavsynthParam.SHAPE), M8WavShape.SINE)
        self.assertEqual(read_wavsynth.get(M8WavsynthParam.SIZE), 0x80)

    def test_clone(self):
        # Create wavsynth with custom parameters
        original = M8Wavsynth(name=self.test_name)
        original.set(M8WavsynthParam.CUTOFF, 0x20)
        original.set(M8WavsynthParam.RESONANCE, 0xC0)
        original.set(M8WavsynthParam.SHAPE, M8WavShape.TRIANGLE)
        original.set(M8WavsynthParam.WARP, 0x60)

        # Clone it
        cloned = original.clone()

        # Check they are different objects
        self.assertIsNot(cloned, original)

        # Check all values match
        self.assertEqual(cloned.name, original.name)
        self.assertEqual(cloned.get(M8WavsynthParam.CUTOFF), original.get(M8WavsynthParam.CUTOFF))
        self.assertEqual(cloned.get(M8WavsynthParam.RESONANCE), original.get(M8WavsynthParam.RESONANCE))
        self.assertEqual(cloned.get(M8WavsynthParam.SHAPE), original.get(M8WavsynthParam.SHAPE))
        self.assertEqual(cloned.get(M8WavsynthParam.WARP), original.get(M8WavsynthParam.WARP))

    def test_modulators_initialized(self):
        """Test that modulators are initialized with defaults."""
        wavsynth = M8Wavsynth()

        # Check modulators exist
        self.assertIsInstance(wavsynth.modulators, M8Modulators)

        # Check 4 modulators
        self.assertEqual(len(wavsynth.modulators), 4)

        # Check default types (2 ADSR, 2 LFO based on rust docs)
        # Note: Default might be different from sampler, but let's verify with 0 (AHD) for now
        self.assertEqual(wavsynth.modulators[0].mod_type, 0)  # AHD/ADSR
        self.assertEqual(wavsynth.modulators[1].mod_type, 0)  # AHD/ADSR

    def test_modulators_read_write(self):
        """Test that modulators are read and written correctly."""
        # Create wavsynth with custom modulator
        original = M8Wavsynth(name="TEST")
        original.modulators[0].destination = 1
        original.modulators[0].set(2, 0x20)  # Attack

        # Write to binary
        binary = original.write()

        # Check length (should be same as sampler block size)
        self.assertEqual(len(binary), 215)  # Full instrument block

        # Read back
        deserialized = M8Wavsynth.read(binary)

        # Verify modulator preserved
        self.assertEqual(deserialized.modulators[0].destination, 1)
        self.assertEqual(deserialized.modulators[0].get(2), 0x20)

    def test_modulators_clone(self):
        """Test that modulators are cloned correctly."""
        original = M8Wavsynth(name="TEST")
        original.modulators[1].destination = 5
        original.modulators[1].set(4, 0x40)  # Decay

        # Clone
        cloned = original.clone()

        # Check modulator values match
        self.assertEqual(cloned.modulators[1].destination, original.modulators[1].destination)
        self.assertEqual(cloned.modulators[1].get(4), original.modulators[1].get(4))

        # Modify clone
        cloned.modulators[1].destination = 2

        # Check original unchanged
        self.assertEqual(original.modulators[1].destination, 5)

    def test_wavshape_enum(self):
        """Test that WavShape enum values work correctly."""
        wavsynth = M8Wavsynth()

        # Test basic shapes
        wavsynth.set(M8WavsynthParam.SHAPE, M8WavShape.SINE)
        self.assertEqual(wavsynth.get(M8WavsynthParam.SHAPE), M8WavShape.SINE)

        wavsynth.set(M8WavsynthParam.SHAPE, M8WavShape.SAW)
        self.assertEqual(wavsynth.get(M8WavsynthParam.SHAPE), M8WavShape.SAW)

        # Test wavetable shapes
        wavsynth.set(M8WavsynthParam.SHAPE, M8WavShape.WT_CRUSH)
        self.assertEqual(wavsynth.get(M8WavsynthParam.SHAPE), M8WavShape.WT_CRUSH)


if __name__ == '__main__':
    unittest.main()
