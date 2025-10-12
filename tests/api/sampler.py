import unittest
from m8.api.sampler import M8Sampler


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

    def test_constructor_with_parameters(self):
        # Test with kwargs
        sampler = M8Sampler(
            name=self.test_name,
            sample_path=self.test_sample_path
        )

        # Check parameters
        self.assertEqual(sampler.name, self.test_name)
        self.assertEqual(sampler.sample_path, self.test_sample_path)

    def test_binary_serialization(self):
        # Create sampler with supported parameters
        sampler = M8Sampler(
            name="TEST",
            sample_path="/samples/kick.wav"
        )

        # Write to binary
        binary = sampler.write()

        # Read it back
        read_sampler = M8Sampler.read(binary)

        # Check supported parameters were preserved
        self.assertEqual(read_sampler.name, "TEST")
        self.assertEqual(read_sampler.sample_path, "/samples/kick.wav")

    def test_is_empty(self):
        # Valid SAMPLER instrument should not be empty
        sampler = M8Sampler()
        self.assertFalse(sampler.is_empty())

    def test_clone(self):
        # Create sampler
        original = M8Sampler(
            name=self.test_name,
            sample_path=self.test_sample_path
        )

        # Clone it
        cloned = original.clone()

        # Check they are different objects
        self.assertIsNot(cloned, original)

        # Check values match
        self.assertEqual(cloned.name, original.name)
        self.assertEqual(cloned.sample_path, original.sample_path)


if __name__ == '__main__':
    unittest.main()
