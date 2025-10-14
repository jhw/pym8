import unittest
from m8.api.sampler import (
    M8Sampler,
    DEFAULT_LENGTH, DEFAULT_FINETUNE, DEFAULT_CUTOFF, DEFAULT_PAN, DEFAULT_DRY
)


class TestM8Sampler(unittest.TestCase):
    def setUp(self):
        # Define Sampler-specific parameters
        self.test_name = "TestSampler"
        self.test_sample_path = "/samples/kick.wav"

    def test_constructor_and_defaults(self):
        # Test default constructor
        sampler = M8Sampler()

        # Check type is set correctly
        self.assertEqual(sampler.type, 0x02)  # SAMPLER type_id is 2

        # Check default parameters
        self.assertEqual(sampler.name, "")
        self.assertEqual(sampler.sample_path, "")
        self.assertEqual(sampler.length, DEFAULT_LENGTH)
        self.assertEqual(sampler.finetune, DEFAULT_FINETUNE)
        self.assertEqual(sampler.cutoff, DEFAULT_CUTOFF)
        self.assertEqual(sampler.pan, DEFAULT_PAN)
        self.assertEqual(sampler.dry, DEFAULT_DRY)

    def test_constructor_with_parameters(self):
        # Test with kwargs including non-default values
        sampler = M8Sampler(
            name=self.test_name,
            sample_path=self.test_sample_path,
            length=0x80,
            finetune=0x70,
            cutoff=0xE0,
            pan=0x60,
            dry=0xA0
        )

        # Check parameters
        self.assertEqual(sampler.name, self.test_name)
        self.assertEqual(sampler.sample_path, self.test_sample_path)
        self.assertEqual(sampler.length, 0x80)
        self.assertEqual(sampler.finetune, 0x70)
        self.assertEqual(sampler.cutoff, 0xE0)
        self.assertEqual(sampler.pan, 0x60)
        self.assertEqual(sampler.dry, 0xA0)

    def test_binary_serialization(self):
        # Create sampler with custom parameters
        sampler = M8Sampler(
            name="TEST",
            sample_path="/samples/kick.wav",
            length=0x80,
            finetune=0x70,
            cutoff=0xE0,
            pan=0x60,
            dry=0xA0
        )

        # Write to binary
        binary = sampler.write()

        # Read it back
        read_sampler = M8Sampler.read(binary)

        # Check all parameters were preserved
        self.assertEqual(read_sampler.name, "TEST")
        self.assertEqual(read_sampler.sample_path, "/samples/kick.wav")
        self.assertEqual(read_sampler.length, 0x80)
        self.assertEqual(read_sampler.finetune, 0x70)
        self.assertEqual(read_sampler.cutoff, 0xE0)
        self.assertEqual(read_sampler.pan, 0x60)
        self.assertEqual(read_sampler.dry, 0xA0)

    def test_clone(self):
        # Create sampler with custom parameters
        original = M8Sampler(
            name=self.test_name,
            sample_path=self.test_sample_path,
            length=0x80,
            finetune=0x70,
            cutoff=0xE0,
            pan=0x60,
            dry=0xA0
        )

        # Clone it
        cloned = original.clone()

        # Check they are different objects
        self.assertIsNot(cloned, original)

        # Check all values match
        self.assertEqual(cloned.name, original.name)
        self.assertEqual(cloned.sample_path, original.sample_path)
        self.assertEqual(cloned.length, original.length)
        self.assertEqual(cloned.finetune, original.finetune)
        self.assertEqual(cloned.cutoff, original.cutoff)
        self.assertEqual(cloned.pan, original.pan)
        self.assertEqual(cloned.dry, original.dry)


if __name__ == '__main__':
    unittest.main()
