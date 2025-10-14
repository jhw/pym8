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

    def test_read_with_zero_defaults(self):
        # Simulate loading from a template with zeros for default parameters
        # Create binary data with type=2 (sampler) but zeros for default params
        from m8.api.sampler import BLOCK_SIZE
        binary_data = bytearray([0] * BLOCK_SIZE)
        binary_data[0] = 0x02  # Set type to SAMPLER

        # Read it back
        sampler = M8Sampler.read(binary_data)

        # Check that non-zero defaults were applied despite zeros in template
        self.assertEqual(sampler.get(0), 0x02)   # Type should be preserved
        self.assertEqual(sampler.get(17), 0x80)  # FINETUNE should default to 128
        self.assertEqual(sampler.get(22), 0xFF)  # LENGTH should default to 255
        self.assertEqual(sampler.get(25), 0xFF)  # CUTOFF should default to 255
        self.assertEqual(sampler.get(29), 0x80)  # PAN should default to 128
        self.assertEqual(sampler.get(30), 0xC0)  # DRY should default to 192

    def test_read_with_non_zero_values_preserved(self):
        # Test that non-zero values from file are preserved (not overwritten)
        from m8.api.sampler import BLOCK_SIZE
        binary_data = bytearray([0] * BLOCK_SIZE)
        binary_data[0] = 0x02   # Type
        binary_data[17] = 0x70  # FINETUNE (non-default)
        binary_data[22] = 0x80  # LENGTH (non-default)
        binary_data[25] = 0xE0  # CUTOFF (non-default)
        binary_data[29] = 0x60  # PAN (non-default)
        binary_data[30] = 0xA0  # DRY (non-default)

        # Read it back
        sampler = M8Sampler.read(binary_data)

        # Check that existing non-zero values were preserved
        self.assertEqual(sampler.get(17), 0x70)  # Should preserve 0x70
        self.assertEqual(sampler.get(22), 0x80)  # Should preserve 0x80
        self.assertEqual(sampler.get(25), 0xE0)  # Should preserve 0xE0
        self.assertEqual(sampler.get(29), 0x60)  # Should preserve 0x60
        self.assertEqual(sampler.get(30), 0xA0)  # Should preserve 0xA0


if __name__ == '__main__':
    unittest.main()
