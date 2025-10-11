import unittest
from m8.api.sampler import M8Sampler, M8SamplerParams

class TestM8SamplerParams(unittest.TestCase):
    def setUp(self):
        # Test values for sampler parameters
        self.test_sample_path = "/samples/kick.wav"
        self.test_play_mode = 0x01  # REV
        self.test_slice = 0x05

    def test_constructor_and_defaults(self):
        # Test default constructor
        params = M8SamplerParams()

        # Check defaults
        self.assertEqual(params.play_mode, 0)
        self.assertEqual(params.slice, 0)
        self.assertEqual(params.sample_path, "")

    def test_constructor_with_values(self):
        # Test constructor with parameters
        params = M8SamplerParams(
            play_mode=self.test_play_mode,
            slice=self.test_slice,
            sample_path=self.test_sample_path
        )

        # Check values match
        self.assertEqual(params.play_mode, self.test_play_mode)
        self.assertEqual(params.slice, self.test_slice)
        self.assertEqual(params.sample_path, self.test_sample_path)

    def test_read_write_consistency(self):
        # Create params with test values
        original = M8SamplerParams(
            play_mode=self.test_play_mode,
            slice=self.test_slice,
            sample_path=self.test_sample_path
        )

        # Write to binary
        binary = original.write()

        # Read back from binary
        deserialized = M8SamplerParams()
        deserialized.read(binary)

        # Check all values match
        self.assertEqual(deserialized.play_mode, original.play_mode)
        self.assertEqual(deserialized.slice, original.slice)
        self.assertEqual(deserialized.sample_path, original.sample_path)

    def test_as_dict(self):
        # Create params with test values
        params = M8SamplerParams(
            play_mode=self.test_play_mode,
            slice=self.test_slice,
            sample_path=self.test_sample_path
        )

        # Convert to dict
        result = params.as_dict()

        # Check all parameters are in the dictionary
        self.assertEqual(result["play_mode"], self.test_play_mode)
        self.assertEqual(result["slice"], self.test_slice)
        self.assertEqual(result["sample_path"], self.test_sample_path)

    def test_from_dict(self):
        # Test data
        data = {
            "play_mode": self.test_play_mode,
            "slice": self.test_slice,
            "sample_path": self.test_sample_path
        }

        # Create from dict
        params = M8SamplerParams.from_dict(data)

        # Check values
        self.assertEqual(params.play_mode, self.test_play_mode)
        self.assertEqual(params.slice, self.test_slice)
        self.assertEqual(params.sample_path, self.test_sample_path)

    def test_clone(self):
        # Create params with test values
        original = M8SamplerParams(
            play_mode=self.test_play_mode,
            slice=self.test_slice,
            sample_path=self.test_sample_path
        )

        # Clone
        cloned = original.clone()

        # Check they are different objects
        self.assertIsNot(cloned, original)

        # Check values match
        self.assertEqual(cloned.play_mode, original.play_mode)
        self.assertEqual(cloned.slice, original.slice)
        self.assertEqual(cloned.sample_path, original.sample_path)


class TestM8Sampler(unittest.TestCase):
    def setUp(self):
        # Define common instrument parameters
        self.common_params = {
            "name": "TestSampler",
            "transpose": 0x5,
            "eq": 0x2,
            "table_tick": 0x2,
            "volume": 0x10,
            "pitch": 0x20,
            "finetune": 0x90
        }

        # Define Sampler-specific parameters
        self.sampler_params = {
            "play_mode": 0x01,  # REV
            "slice": 0x05,
            "sample_path": "/samples/kick.wav"
        }

    def test_constructor_and_defaults(self):
        # Test default constructor
        sampler = M8Sampler()

        # Check type is set correctly
        self.assertEqual(sampler.type, 0x02)  # SAMPLER type_id is 2

        # Check params object is created
        self.assertTrue(hasattr(sampler, "params"))
        self.assertIsInstance(sampler.params, M8SamplerParams)

        # Check default parameters
        self.assertEqual(sampler.name, "")
        self.assertEqual(sampler.volume, 255)
        self.assertEqual(sampler.pitch, 64)
        self.assertEqual(sampler.transpose, 4)
        self.assertEqual(sampler.eq, 1)
        self.assertEqual(sampler.table_tick, 1)
        self.assertEqual(sampler.finetune, 128)

        # Check sampler-specific defaults
        self.assertEqual(sampler.params.play_mode, 0)
        self.assertEqual(sampler.params.slice, 0)
        self.assertEqual(sampler.params.sample_path, "")

    def test_constructor_with_parameters(self):
        # Test with kwargs for both common and specific parameters
        sampler = M8Sampler(
            name="TestSampler",
            sample_path="/samples/kick.wav",
            play_mode=0x01,
            slice=0x05,
            volume=0x10,
            pitch=0x20,
            transpose=0x5,
            eq=0x2,
            table_tick=0x2,
            finetune=0x90
        )

        # Check common parameters
        self.assertEqual(sampler.name, "TestSampler")
        self.assertEqual(sampler.volume, 0x10)
        self.assertEqual(sampler.pitch, 0x20)
        self.assertEqual(sampler.transpose, 0x5)
        self.assertEqual(sampler.eq, 0x2)
        self.assertEqual(sampler.table_tick, 0x2)
        self.assertEqual(sampler.finetune, 0x90)

        # Check instrument-specific parameters
        self.assertEqual(sampler.params.play_mode, 0x01)
        self.assertEqual(sampler.params.slice, 0x05)
        self.assertEqual(sampler.params.sample_path, "/samples/kick.wav")

    def test_binary_serialization(self):
        # Create sampler with all parameters
        sampler = M8Sampler(
            name="TEST",
            sample_path="/samples/kick.wav",
            play_mode=0x01,
            slice=0x05,
            volume=0x10,
            pitch=0x20,
            transpose=0x5,
            eq=0x2,
            table_tick=0x2,
            finetune=0x90
        )

        # Write to binary
        binary = sampler.write()

        # Read it back
        read_sampler = M8Sampler.read(binary)

        # Check all parameters were preserved
        self.assertEqual(read_sampler.name, "TEST")
        self.assertEqual(read_sampler.volume, 0x10)
        self.assertEqual(read_sampler.pitch, 0x20)
        self.assertEqual(read_sampler.transpose, 0x5)
        self.assertEqual(read_sampler.eq, 0x2)
        self.assertEqual(read_sampler.table_tick, 0x2)
        self.assertEqual(read_sampler.finetune, 0x90)

        # Check sampler-specific parameters
        self.assertEqual(read_sampler.params.play_mode, 0x01)
        self.assertEqual(read_sampler.params.slice, 0x05)
        self.assertEqual(read_sampler.params.sample_path, "/samples/kick.wav")

    def test_is_empty(self):
        # Valid SAMPLER instrument should not be empty
        sampler = M8Sampler()
        self.assertFalse(sampler.is_empty())

    def test_as_dict(self):
        # Create sampler with all parameters
        sampler = M8Sampler(
            name="TestSampler",
            sample_path="/samples/kick.wav",
            play_mode=0x01,
            slice=0x05,
            volume=0x10,
            pitch=0x20,
            transpose=0x5,
            eq=0x2,
            table_tick=0x2,
            finetune=0x90
        )

        # Convert to dict
        result = sampler.as_dict()

        # Check common parameters
        self.assertEqual(result["type"], 0x02)
        self.assertEqual(result["name"], "TestSampler")
        self.assertEqual(result["volume"], 0x10)
        self.assertEqual(result["pitch"], 0x20)
        self.assertEqual(result["transpose"], 0x5)
        self.assertEqual(result["eq"], 0x2)
        self.assertEqual(result["table_tick"], 0x2)
        self.assertEqual(result["finetune"], 0x90)

        # Check sampler-specific parameters
        self.assertEqual(result["play_mode"], 0x01)
        self.assertEqual(result["slice"], 0x05)
        self.assertEqual(result["sample_path"], "/samples/kick.wav")

    def test_from_dict(self):
        # Test data
        data = {
            "name": "TestSampler",
            "sample_path": "/samples/kick.wav",
            "play_mode": 0x01,
            "slice": 0x05,
            "volume": 0x10,
            "pitch": 0x20,
            "transpose": 0x5,
            "eq": 0x2,
            "table_tick": 0x2,
            "finetune": 0x90
        }

        # Create from dict
        sampler = M8Sampler.from_dict(data)

        # Check all parameters
        self.assertEqual(sampler.name, "TestSampler")
        self.assertEqual(sampler.volume, 0x10)
        self.assertEqual(sampler.pitch, 0x20)
        self.assertEqual(sampler.transpose, 0x5)
        self.assertEqual(sampler.eq, 0x2)
        self.assertEqual(sampler.table_tick, 0x2)
        self.assertEqual(sampler.finetune, 0x90)
        self.assertEqual(sampler.params.play_mode, 0x01)
        self.assertEqual(sampler.params.slice, 0x05)
        self.assertEqual(sampler.params.sample_path, "/samples/kick.wav")

    def test_clone(self):
        # Create sampler
        original = M8Sampler(
            name="TestSampler",
            sample_path="/samples/kick.wav",
            play_mode=0x01,
            slice=0x05
        )

        # Clone it
        cloned = original.clone()

        # Check they are different objects
        self.assertIsNot(cloned, original)
        self.assertIsNot(cloned.params, original.params)

        # Check values match
        self.assertEqual(cloned.name, original.name)
        self.assertEqual(cloned.params.sample_path, original.params.sample_path)
        self.assertEqual(cloned.params.play_mode, original.params.play_mode)
        self.assertEqual(cloned.params.slice, original.params.slice)


if __name__ == '__main__':
    unittest.main()
