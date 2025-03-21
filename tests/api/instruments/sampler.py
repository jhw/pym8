import unittest
from m8.api.instruments.sampler import M8SamplerParams, M8Sampler
from m8.api.modulators import M8LFO

class TestM8SamplerParams(unittest.TestCase):
    def test_constructor_and_defaults(self):
        # Test default constructor
        params = M8SamplerParams()
        
        # Check defaults for key parameters
        self.assertEqual(params.play_mode, 0x0)
        self.assertEqual(params.slice, 0x0)
        self.assertEqual(params.start, 0x0)
        self.assertEqual(params.loop_start, 0x0)
        self.assertEqual(params.length, 0xFF)
        self.assertEqual(params.degrade, 0x0)
        self.assertEqual(params.filter, 0x0)
        self.assertEqual(params.cutoff, 0xFF)
        self.assertEqual(params.res, 0x0)
        self.assertEqual(params.amp, 0x0)
        self.assertEqual(params.limit, 0x0)
        self.assertEqual(params.pan, 0x80)
        self.assertEqual(params.dry, 0xC0)
        self.assertEqual(params.chorus, 0x0)
        self.assertEqual(params.delay, 0x0)
        self.assertEqual(params.reverb, 0x0)
        self.assertEqual(params.sample_path, "")
        
        # Test with kwargs
        params = M8SamplerParams(
            play_mode=0x1,
            slice=0x5,
            start=0x10,
            loop_start=0x20,
            length=0xE0,
            degrade=0x30,
            filter=0x2,
            cutoff=0xD0,
            res=0x40,
            amp=0x50,
            limit=0x60,
            pan=0x70,
            dry=0xB0,
            chorus=0x80,
            delay=0x90,
            reverb=0xA0,
            sample_path="/samples/kick.wav"
        )
        
        # Check values
        self.assertEqual(params.play_mode, 0x1)
        self.assertEqual(params.slice, 0x5)
        self.assertEqual(params.start, 0x10)
        self.assertEqual(params.loop_start, 0x20)
        self.assertEqual(params.length, 0xE0)
        self.assertEqual(params.degrade, 0x30)
        self.assertEqual(params.filter, 0x2)
        self.assertEqual(params.cutoff, 0xD0)
        self.assertEqual(params.res, 0x40)
        self.assertEqual(params.amp, 0x50)
        self.assertEqual(params.limit, 0x60)
        self.assertEqual(params.pan, 0x70)
        self.assertEqual(params.dry, 0xB0)
        self.assertEqual(params.chorus, 0x80)
        self.assertEqual(params.delay, 0x90)
        self.assertEqual(params.reverb, 0xA0)
        self.assertEqual(params.sample_path, "/samples/kick.wav")
    
    def test_read_from_binary(self):
        # Create test binary data
        # Note: The sample_path is at a higher offset (0x57 = 87)
        binary_data = bytearray([0] * 18)  # First 18 bytes are not used by SamplerParams
        
        # Add synth-specific parameters
        binary_data.extend([
            0x01,   # play_mode (offset 18)
            0x05,   # slice (offset 19)
            0x10,   # start (offset 20)
            0x20,   # loop_start (offset 21)
            0xE0,   # length (offset 22)
            0x30,   # degrade (offset 23)
            0x02,   # filter (offset 24)
            0xD0,   # cutoff (offset 25)
            0x40,   # res (offset 26)
            0x50,   # amp (offset 27)
            0x60,   # limit (offset 28)
            0x70,   # pan (offset 29)
            0xB0,   # dry (offset 30)
            0x80,   # chorus (offset 31)
            0x90,   # delay (offset 32)
            0xA0    # reverb (offset 33)
        ])
        
        # Pad up to sample_path offset (0x57 = 87)
        binary_data.extend([0] * (87 - len(binary_data)))
        
        # Add sample path
        test_path = b"/samples/kick.wav"
        binary_data.extend(test_path)
        # Pad to ensure enough space
        binary_data.extend([0] * (128 - len(test_path)))
        
        # Read from binary
        params = M8SamplerParams.read(binary_data)
        
        # Check values
        self.assertEqual(params.play_mode, 0x1)
        self.assertEqual(params.slice, 0x5)
        self.assertEqual(params.start, 0x10)
        self.assertEqual(params.loop_start, 0x20)
        self.assertEqual(params.length, 0xE0)
        self.assertEqual(params.degrade, 0x30)
        self.assertEqual(params.filter, 0x2)
        self.assertEqual(params.cutoff, 0xD0)
        self.assertEqual(params.res, 0x40)
        self.assertEqual(params.amp, 0x50)
        self.assertEqual(params.limit, 0x60)
        self.assertEqual(params.pan, 0x70)
        self.assertEqual(params.dry, 0xB0)
        self.assertEqual(params.chorus, 0x80)
        self.assertEqual(params.delay, 0x90)
        self.assertEqual(params.reverb, 0xA0)
        self.assertEqual(params.sample_path, "/samples/kick.wav")
    
    def test_write_to_binary(self):
        # Create params with specific values
        params = M8SamplerParams(
            play_mode=0x1,
            slice=0x5,
            start=0x10,
            loop_start=0x20,
            length=0xE0,
            degrade=0x30,
            filter=0x2,
            cutoff=0xD0,
            res=0x40,
            amp=0x50,
            limit=0x60,
            pan=0x70,
            dry=0xB0,
            chorus=0x80,
            delay=0x90,
            reverb=0xA0,
            sample_path="/samples/kick.wav"
        )
        
        # Write to binary
        binary = params.write()
        
        # Check binary output
        # The total length should include the sample_path offset (0x57 = 87) + 128 bytes
        self.assertEqual(len(binary), 87 + 128)
        
        # Check specific values
        self.assertEqual(binary[18], 0x1)   # play_mode
        self.assertEqual(binary[19], 0x5)   # slice
        self.assertEqual(binary[20], 0x10)  # start
        self.assertEqual(binary[21], 0x20)  # loop_start
        self.assertEqual(binary[22], 0xE0)  # length
        self.assertEqual(binary[23], 0x30)  # degrade
        self.assertEqual(binary[24], 0x2)   # filter
        self.assertEqual(binary[25], 0xD0)  # cutoff
        self.assertEqual(binary[26], 0x40)  # res
        self.assertEqual(binary[27], 0x50)  # amp
        self.assertEqual(binary[28], 0x60)  # limit
        self.assertEqual(binary[29], 0x70)  # pan
        self.assertEqual(binary[30], 0xB0)  # dry
        self.assertEqual(binary[31], 0x80)  # chorus
        self.assertEqual(binary[32], 0x90)  # delay
        self.assertEqual(binary[33], 0xA0)  # reverb
        
        # Check sample path
        # Sample path starts at offset 0x57 (87)
        sample_path_bytes = binary[87:87+16]  # Just check the first 16 bytes
        self.assertEqual(sample_path_bytes, b"/samples/kick.wa")
    
    def test_read_write_consistency(self):
        # Create original params
        original = M8SamplerParams(
            play_mode=0x1,
            slice=0x5,
            start=0x10,
            loop_start=0x20,
            length=0xE0,
            degrade=0x30,
            filter=0x2,
            cutoff=0xD0,
            res=0x40,
            amp=0x50,
            limit=0x60,
            pan=0x70,
            dry=0xB0,
            chorus=0x80,
            delay=0x90,
            reverb=0xA0,
            sample_path="/samples/kick.wav"
        )
        
        # Write to binary
        binary = original.write()
        
        # Read back from binary
        deserialized = M8SamplerParams.read(binary)
        
        # Check values match
        self.assertEqual(deserialized.play_mode, original.play_mode)
        self.assertEqual(deserialized.slice, original.slice)
        self.assertEqual(deserialized.start, original.start)
        self.assertEqual(deserialized.loop_start, original.loop_start)
        self.assertEqual(deserialized.length, original.length)
        self.assertEqual(deserialized.degrade, original.degrade)
        self.assertEqual(deserialized.filter, original.filter)
        self.assertEqual(deserialized.cutoff, original.cutoff)
        self.assertEqual(deserialized.res, original.res)
        self.assertEqual(deserialized.amp, original.amp)
        self.assertEqual(deserialized.limit, original.limit)
        self.assertEqual(deserialized.pan, original.pan)
        self.assertEqual(deserialized.dry, original.dry)
        self.assertEqual(deserialized.chorus, original.chorus)
        self.assertEqual(deserialized.delay, original.delay)
        self.assertEqual(deserialized.reverb, original.reverb)
        self.assertEqual(deserialized.sample_path, original.sample_path)
    
    def test_as_dict(self):
        # Create params
        params = M8SamplerParams(
            play_mode=0x1,
            slice=0x5,
            start=0x10,
            loop_start=0x20,
            length=0xE0,
            degrade=0x30,
            filter=0x2,
            cutoff=0xD0,
            res=0x40,
            amp=0x50,
            limit=0x60,
            pan=0x70,
            dry=0xB0,
            chorus=0x80,
            delay=0x90,
            reverb=0xA0,
            sample_path="/samples/kick.wav"
        )
        
        # Convert to dict
        result = params.as_dict()
        
        # Check dict
        expected = {
            "play_mode": 0x1,
            "slice": 0x5,
            "start": 0x10,
            "loop_start": 0x20,
            "length": 0xE0,
            "degrade": 0x30,
            "filter": 0x2,
            "cutoff": 0xD0,
            "res": 0x40,
            "amp": 0x50,
            "limit": 0x60,
            "pan": 0x70,
            "dry": 0xB0,
            "chorus": 0x80,
            "delay": 0x90,
            "reverb": 0xA0,
            "sample_path": "/samples/kick.wav"
        }
        
        for key, value in expected.items():
            self.assertEqual(result[key], value)
    
    def test_from_dict(self):
        # Test data
        data = {
            "play_mode": 0x1,
            "slice": 0x5,
            "start": 0x10,
            "loop_start": 0x20,
            "length": 0xE0,
            "degrade": 0x30,
            "filter": 0x2,
            "cutoff": 0xD0,
            "res": 0x40,
            "amp": 0x50,
            "limit": 0x60,
            "pan": 0x70,
            "dry": 0xB0,
            "chorus": 0x80,
            "delay": 0x90,
            "reverb": 0xA0,
            "sample_path": "/samples/kick.wav"
        }
        
        # Create from dict
        params = M8SamplerParams.from_dict(data)
        
        # Check values
        for key, value in data.items():
            self.assertEqual(getattr(params, key), value)


class TestM8Sampler(unittest.TestCase):
    def test_constructor_and_defaults(self):
        # Test default constructor
        sampler = M8Sampler()
        
        # Check type is set correctly
        self.assertEqual(sampler.type, 0x02)
        
        # Check synth object is created
        self.assertIsInstance(sampler.synth, M8SamplerParams)
        
        # Check common parameters
        self.assertNotEqual(sampler.name, "")  # Should auto-generate a name
        self.assertEqual(sampler.transpose, 0x4)
        self.assertEqual(sampler.eq, 0x1)
        self.assertEqual(sampler.table_tick, 0x01)
        self.assertEqual(sampler.volume, 0x0)
        self.assertEqual(sampler.pitch, 0x0)
        self.assertEqual(sampler.finetune, 0x80)
        
        # Test with kwargs for both common and synth-specific parameters
        sampler = M8Sampler(
            # Common instrument parameters
            name="TestSampler",
            transpose=0x5,
            eq=0x2,
            table_tick=0x02,
            volume=0x10,
            pitch=0x20,
            finetune=0x90,
            
            # Sampler-specific parameters
            play_mode=0x1,
            slice=0x5,
            start=0x10,
            length=0xE0,
            filter=0x2,
            cutoff=0xD0,
            pan=0x70,
            sample_path="/samples/kick.wav"
        )
        
        # Check common parameters
        self.assertEqual(sampler.name, "TestSampler")
        self.assertEqual(sampler.transpose, 0x5)
        self.assertEqual(sampler.eq, 0x2)
        self.assertEqual(sampler.table_tick, 0x02)
        self.assertEqual(sampler.volume, 0x10)
        self.assertEqual(sampler.pitch, 0x20)
        self.assertEqual(sampler.finetune, 0x90)
        
        # Check synth-specific parameters
        self.assertEqual(sampler.synth.play_mode, 0x1)
        self.assertEqual(sampler.synth.slice, 0x5)
        self.assertEqual(sampler.synth.start, 0x10)
        self.assertEqual(sampler.synth.length, 0xE0)
        self.assertEqual(sampler.synth.filter, 0x2)
        self.assertEqual(sampler.synth.cutoff, 0xD0)
        self.assertEqual(sampler.synth.pan, 0x70)
        self.assertEqual(sampler.synth.sample_path, "/samples/kick.wav")
    
    def test_read_specific_parameters(self):
        # Create a Sampler
        sampler = M8Sampler()
        
        # Create test binary data for synth parameters
        binary_data = bytearray([0] * 18)  # First 18 bytes (common instrument parameters)
        
        # Add synth-specific parameters
        binary_data.extend([
            0x01,   # play_mode
            0x05,   # slice
            0x10,   # start
            0x20,   # loop_start
            0xE0,   # length
            0x30,   # degrade
            0x02,   # filter
            0xD0,   # cutoff
            0x40,   # res
            0x50,   # amp
            0x60,   # limit
            0x70,   # pan
            0xB0,   # dry
            0x80,   # chorus
            0x90,   # delay
            0xA0    # reverb
        ])
        
        # Pad up to sample_path offset (0x57 = 87)
        binary_data.extend([0] * (87 - len(binary_data)))
        
        # Add sample path
        test_path = b"/samples/kick.wav"
        binary_data.extend(test_path)
        # Pad to ensure enough space
        binary_data.extend([0] * (128 - len(test_path)))
        
        # Call the method to read specific parameters
        # This would normally be called by _read_parameters in the base class
        sampler._read_specific_parameters(binary_data, 18)
        
        # Check synth parameters were read correctly
        self.assertEqual(sampler.synth.play_mode, 0x1)
        self.assertEqual(sampler.synth.slice, 0x5)
        self.assertEqual(sampler.synth.start, 0x10)
        self.assertEqual(sampler.synth.loop_start, 0x20)
        self.assertEqual(sampler.synth.length, 0xE0)
        self.assertEqual(sampler.synth.degrade, 0x30)
        self.assertEqual(sampler.synth.filter, 0x2)
        self.assertEqual(sampler.synth.cutoff, 0xD0)
        self.assertEqual(sampler.synth.res, 0x40)
        self.assertEqual(sampler.synth.amp, 0x50)
        self.assertEqual(sampler.synth.limit, 0x60)
        self.assertEqual(sampler.synth.pan, 0x70)
        self.assertEqual(sampler.synth.dry, 0xB0)
        self.assertEqual(sampler.synth.chorus, 0x80)
        self.assertEqual(sampler.synth.delay, 0x90)
        self.assertEqual(sampler.synth.reverb, 0xA0)
        self.assertEqual(sampler.synth.sample_path, "/samples/kick.wav")
    
    def test_write_specific_parameters(self):
        # Create a Sampler with specific parameters
        sampler = M8Sampler(
            play_mode=0x1,
            slice=0x5,
            start=0x10,
            loop_start=0x20,
            length=0xE0,
            degrade=0x30,
            filter=0x2,
            cutoff=0xD0,
            res=0x40,
            amp=0x50,
            limit=0x60,
            pan=0x70,
            dry=0xB0,
            chorus=0x80,
            delay=0x90,
            reverb=0xA0,
            sample_path="/samples/kick.wav"
        )
        
        # Call the method to write specific parameters
        # This would normally be called by write in the base class
        binary = sampler._write_specific_parameters()
        
        # The total length should include the sample_path offset (0x57 = 87) + 128 bytes
        self.assertEqual(len(binary), 87 + 128)
        
        # Check specific values
        self.assertEqual(binary[18], 0x1)   # play_mode
        self.assertEqual(binary[19], 0x5)   # slice
        self.assertEqual(binary[20], 0x10)  # start
        self.assertEqual(binary[21], 0x20)  # loop_start
        self.assertEqual(binary[22], 0xE0)  # length
        self.assertEqual(binary[23], 0x30)  # degrade
        self.assertEqual(binary[24], 0x2)   # filter
        self.assertEqual(binary[25], 0xD0)  # cutoff
        self.assertEqual(binary[26], 0x40)  # res
        self.assertEqual(binary[27], 0x50)  # amp
        self.assertEqual(binary[28], 0x60)  # limit
        self.assertEqual(binary[29], 0x70)  # pan
        self.assertEqual(binary[30], 0xB0)  # dry
        self.assertEqual(binary[31], 0x80)  # chorus
        self.assertEqual(binary[32], 0x90)  # delay
        self.assertEqual(binary[33], 0xA0)  # reverb
        
        # Check sample path
        # Sample path starts at offset 0x57 (87)
        sample_path_bytes = binary[87:87+16]  # Just check the first 16 bytes
        self.assertEqual(sample_path_bytes, b"/samples/kick.wa")
    
    def test_is_empty(self):
        # Empty Sampler (default values)
        sampler = M8Sampler(name="")
        self.assertTrue(sampler.is_empty())
        
        # Non-empty Sampler (with name)
        sampler = M8Sampler(name="TestSampler")
        self.assertFalse(sampler.is_empty())
        
        # Non-empty Sampler (with volume)
        sampler = M8Sampler(name="", volume=0x10)
        self.assertFalse(sampler.is_empty())
        
        # Non-empty Sampler (with sample_path)
        sampler = M8Sampler(name="", sample_path="/samples/kick.wav")
        self.assertFalse(sampler.is_empty())
    
    def test_add_modulator(self):
        # Create a Sampler
        sampler = M8Sampler()
        
        # Add a modulator
        mod = M8LFO(destination=2, amount=100, frequency=50)
        slot = sampler.add_modulator(mod)
        
        # Should use first slot
        self.assertEqual(slot, 0)
        self.assertEqual(sampler.modulators[0].type, M8LFO.TYPE_VALUE)
        self.assertEqual(sampler.modulators[0].destination, 2)
        self.assertEqual(sampler.modulators[0].amount, 100)
        self.assertEqual(sampler.modulators[0].frequency, 50)
    
    def test_as_dict(self):
        # Create a Sampler with specific parameters
        sampler = M8Sampler(
            # Common parameters
            name="TestSampler",
            transpose=0x5,
            eq=0x2,
            
            # Synth-specific parameters
            play_mode=0x1,
            slice=0x5,
            start=0x10,
            cutoff=0xD0,
            pan=0x70,
            sample_path="/samples/kick.wav"
        )
        
        # Add a modulator
        mod = M8LFO(destination=2, amount=100, frequency=50)
        sampler.modulators[0] = mod
        
        # Convert to dict
        result = sampler.as_dict()
        
        # Check common parameters
        self.assertEqual(result["type"], 0x02)
        self.assertEqual(result["name"], "TestSampler")
        self.assertEqual(result["transpose"], 0x5)
        self.assertEqual(result["eq"], 0x2)
        
        # Check synth-specific parameters
        self.assertEqual(result["play_mode"], 0x1)
        self.assertEqual(result["slice"], 0x5)
        self.assertEqual(result["start"], 0x10)
        self.assertEqual(result["cutoff"], 0xD0)
        self.assertEqual(result["pan"], 0x70)
        self.assertEqual(result["sample_path"], "/samples/kick.wav")
        
        # Check modulators
        self.assertIn("modulators", result)
        self.assertIsInstance(result["modulators"], list)
        self.assertGreater(len(result["modulators"]), 0)
        self.assertEqual(result["modulators"][0]["type"], M8LFO.TYPE_VALUE)
        self.assertEqual(result["modulators"][0]["destination"], 2)
        self.assertEqual(result["modulators"][0]["amount"], 100)
        self.assertEqual(result["modulators"][0]["frequency"], 50)


if __name__ == '__main__':
    unittest.main()