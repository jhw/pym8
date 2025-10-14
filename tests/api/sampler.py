import unittest
from m8.api.sampler import M8Sampler, DEFAULT_PARAMETERS


class TestM8Sampler(unittest.TestCase):
    def setUp(self):
        # Define Sampler-specific parameters
        self.test_name = "TestSampler"
        self.test_sample_path = "/samples/kick.wav"

    def test_constructor_and_defaults(self):
        # Test default constructor
        sampler = M8Sampler()

        # Check type is set correctly
        self.assertEqual(sampler.get(0), 0x02)  # SAMPLER type_id is 2

        # Check default parameters
        self.assertEqual(sampler.name, "")
        self.assertEqual(sampler.sample_path, "")

        # Check non-zero defaults using generic get
        self.assertEqual(sampler.get(17), 0x80)  # FINETUNE
        self.assertEqual(sampler.get(22), 0xFF)  # LENGTH
        self.assertEqual(sampler.get(25), 0xFF)  # CUTOFF
        self.assertEqual(sampler.get(29), 0x80)  # PAN
        self.assertEqual(sampler.get(30), 0xC0)  # DRY

    def test_constructor_with_parameters(self):
        # Test with name and sample_path
        sampler = M8Sampler(
            name=self.test_name,
            sample_path=self.test_sample_path
        )

        # Check parameters
        self.assertEqual(sampler.name, self.test_name)
        self.assertEqual(sampler.sample_path, self.test_sample_path)

        # Set custom values using generic set
        sampler.set(22, 0x80)  # LENGTH
        sampler.set(17, 0x70)  # FINETUNE
        sampler.set(25, 0xE0)  # CUTOFF
        sampler.set(29, 0x60)  # PAN
        sampler.set(30, 0xA0)  # DRY

        # Verify using get
        self.assertEqual(sampler.get(22), 0x80)
        self.assertEqual(sampler.get(17), 0x70)
        self.assertEqual(sampler.get(25), 0xE0)
        self.assertEqual(sampler.get(29), 0x60)
        self.assertEqual(sampler.get(30), 0xA0)

    def test_binary_serialization(self):
        # Create sampler with custom parameters
        sampler = M8Sampler(
            name="TEST",
            sample_path="/samples/kick.wav"
        )
        sampler.set(22, 0x80)  # LENGTH
        sampler.set(17, 0x70)  # FINETUNE
        sampler.set(25, 0xE0)  # CUTOFF
        sampler.set(29, 0x60)  # PAN
        sampler.set(30, 0xA0)  # DRY

        # Write to binary
        binary = sampler.write()

        # Read it back
        read_sampler = M8Sampler.read(binary)

        # Check all parameters were preserved
        self.assertEqual(read_sampler.name, "TEST")
        self.assertEqual(read_sampler.sample_path, "/samples/kick.wav")
        self.assertEqual(read_sampler.get(22), 0x80)
        self.assertEqual(read_sampler.get(17), 0x70)
        self.assertEqual(read_sampler.get(25), 0xE0)
        self.assertEqual(read_sampler.get(29), 0x60)
        self.assertEqual(read_sampler.get(30), 0xA0)

    def test_clone(self):
        # Create sampler with custom parameters
        original = M8Sampler(
            name=self.test_name,
            sample_path=self.test_sample_path
        )
        original.set(22, 0x80)  # LENGTH
        original.set(17, 0x70)  # FINETUNE
        original.set(25, 0xE0)  # CUTOFF
        original.set(29, 0x60)  # PAN
        original.set(30, 0xA0)  # DRY

        # Clone it
        cloned = original.clone()

        # Check they are different objects
        self.assertIsNot(cloned, original)

        # Check all values match
        self.assertEqual(cloned.name, original.name)
        self.assertEqual(cloned.sample_path, original.sample_path)
        self.assertEqual(cloned.get(22), original.get(22))
        self.assertEqual(cloned.get(17), original.get(17))
        self.assertEqual(cloned.get(25), original.get(25))
        self.assertEqual(cloned.get(29), original.get(29))
        self.assertEqual(cloned.get(30), original.get(30))


if __name__ == '__main__':
    unittest.main()
