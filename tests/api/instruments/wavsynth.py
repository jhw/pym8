import unittest
from m8.api.instruments.wavsynth import M8WavSynthParams, M8WavSynth
from m8.api.modulators import M8LFO

class TestM8WavSynthParams(unittest.TestCase):
    def test_constructor_and_defaults(self):
        # Test default constructor
        params = M8WavSynthParams()
        
        # Check defaults for some key parameters
        self.assertEqual(params.shape, 0x0)
        self.assertEqual(params.size, 0x80)
        self.assertEqual(params.mult, 0x80)
        self.assertEqual(params.warp, 0x0)
        self.assertEqual(params.scan, 0x0)
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
        
        # Test with kwargs
        params = M8WavSynthParams(
            shape=0x1,
            size=0x70,
            mult=0x90,
            warp=0x10,
            scan=0x20,
            filter=0x2,
            cutoff=0xE0,
            res=0x30,
            amp=0x40,
            limit=0x50,
            pan=0x60,
            dry=0xB0,
            chorus=0x70,
            delay=0x80,
            reverb=0x90
        )
        
        # Check values
        self.assertEqual(params.shape, 0x1)
        self.assertEqual(params.size, 0x70)
        self.assertEqual(params.mult, 0x90)
        self.assertEqual(params.warp, 0x10)
        self.assertEqual(params.scan, 0x20)
        self.assertEqual(params.filter, 0x2)
        self.assertEqual(params.cutoff, 0xE0)
        self.assertEqual(params.res, 0x30)
        self.assertEqual(params.amp, 0x40)
        self.assertEqual(params.limit, 0x50)
        self.assertEqual(params.pan, 0x60)
        self.assertEqual(params.dry, 0xB0)
        self.assertEqual(params.chorus, 0x70)
        self.assertEqual(params.delay, 0x80)
        self.assertEqual(params.reverb, 0x90)
    
    def test_read_from_binary(self):
        # Create test binary data
        # We need at least 33 bytes for the full parameter set
        binary_data = bytearray([0] * 18)  # First 18 bytes are not used by WavSynthParams
        binary_data.extend([
            0x01,   # shape (offset 18)
            0x70,   # size (offset 19)
            0x90,   # mult (offset 20)
            0x10,   # warp (offset 21)
            0x20,   # scan (offset 22)
            0x02,   # filter (offset 23)
            0xE0,   # cutoff (offset 24)
            0x30,   # res (offset 25)
            0x40,   # amp (offset 26)
            0x50,   # limit (offset 27)
            0x60,   # pan (offset 28)
            0xB0,   # dry (offset 29)
            0x70,   # chorus (offset 30)
            0x80,   # delay (offset 31)
            0x90    # reverb (offset 32)
        ])
        
        # Read from binary
        params = M8WavSynthParams.read(binary_data)
        
        # Check values
        self.assertEqual(params.shape, 0x1)
        self.assertEqual(params.size, 0x70)
        self.assertEqual(params.mult, 0x90)
        self.assertEqual(params.warp, 0x10)
        self.assertEqual(params.scan, 0x20)
        self.assertEqual(params.filter, 0x2)
        self.assertEqual(params.cutoff, 0xE0)
        self.assertEqual(params.res, 0x30)
        self.assertEqual(params.amp, 0x40)
        self.assertEqual(params.limit, 0x50)
        self.assertEqual(params.pan, 0x60)
        self.assertEqual(params.dry, 0xB0)
        self.assertEqual(params.chorus, 0x70)
        self.assertEqual(params.delay, 0x80)
        self.assertEqual(params.reverb, 0x90)
    
    def test_write_to_binary(self):
        # Create params with specific values
        params = M8WavSynthParams(
            shape=0x1,
            size=0x70,
            mult=0x90,
            warp=0x10,
            scan=0x20,
            filter=0x2,
            cutoff=0xE0,
            res=0x30,
            amp=0x40,
            limit=0x50,
            pan=0x60,
            dry=0xB0,
            chorus=0x70,
            delay=0x80,
            reverb=0x90
        )
        
        # Write to binary
        binary = params.write()
        
        # Check binary output
        self.assertEqual(len(binary), 33)  # Should be 33 bytes (offsets 0-32)
        
        # Check specific values
        self.assertEqual(binary[18], 0x1)   # shape
        self.assertEqual(binary[19], 0x70)  # size
        self.assertEqual(binary[20], 0x90)  # mult
        self.assertEqual(binary[21], 0x10)  # warp
        self.assertEqual(binary[22], 0x20)  # scan
        self.assertEqual(binary[23], 0x2)   # filter
        self.assertEqual(binary[24], 0xE0)  # cutoff
        self.assertEqual(binary[25], 0x30)  # res
        self.assertEqual(binary[26], 0x40)  # amp
        self.assertEqual(binary[27], 0x50)  # limit
        self.assertEqual(binary[28], 0x60)  # pan
        self.assertEqual(binary[29], 0xB0)  # dry
        self.assertEqual(binary[30], 0x70)  # chorus
        self.assertEqual(binary[31], 0x80)  # delay
        self.assertEqual(binary[32], 0x90)  # reverb
    
    def test_read_write_consistency(self):
        # Create original params
        original = M8WavSynthParams(
            shape=0x1,
            size=0x70,
            mult=0x90,
            warp=0x10,
            scan=0x20,
            filter=0x2,
            cutoff=0xE0,
            res=0x30,
            amp=0x40,
            limit=0x50,
            pan=0x60,
            dry=0xB0,
            chorus=0x70,
            delay=0x80,
            reverb=0x90
        )
        
        # Write to binary
        binary = original.write()
        
        # Read back from binary
        deserialized = M8WavSynthParams.read(binary)
        
        # Check values match
        self.assertEqual(deserialized.shape, original.shape)
        self.assertEqual(deserialized.size, original.size)
        self.assertEqual(deserialized.mult, original.mult)
        self.assertEqual(deserialized.warp, original.warp)
        self.assertEqual(deserialized.scan, original.scan)
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
    
    def test_as_dict(self):
        # Create params
        params = M8WavSynthParams(
            shape=0x1,
            size=0x70,
            mult=0x90,
            warp=0x10,
            scan=0x20,
            filter=0x2,
            cutoff=0xE0,
            res=0x30,
            amp=0x40,
            limit=0x50,
            pan=0x60,
            dry=0xB0,
            chorus=0x70,
            delay=0x80,
            reverb=0x90
        )
        
        # Convert to dict
        result = params.as_dict()
        
        # Check dict
        expected = {
            "shape": 0x1,
            "size": 0x70,
            "mult": 0x90,
            "warp": 0x10,
            "scan": 0x20,
            "filter": 0x2,
            "cutoff": 0xE0,
            "res": 0x30,
            "amp": 0x40,
            "limit": 0x50,
            "pan": 0x60,
            "dry": 0xB0,
            "chorus": 0x70,
            "delay": 0x80,
            "reverb": 0x90
        }
        
        for key, value in expected.items():
            self.assertEqual(result[key], value)
    
    def test_from_dict(self):
        # Test data
        data = {
            "shape": 0x1,
            "size": 0x70,
            "mult": 0x90,
            "warp": 0x10,
            "scan": 0x20,
            "filter": 0x2,
            "cutoff": 0xE0,
            "res": 0x30,
            "amp": 0x40,
            "limit": 0x50,
            "pan": 0x60,
            "dry": 0xB0,
            "chorus": 0x70,
            "delay": 0x80,
            "reverb": 0x90
        }
        
        # Create from dict
        params = M8WavSynthParams.from_dict(data)
        
        # Check values
        for key, value in data.items():
            self.assertEqual(getattr(params, key), value)


class TestM8WavSynth(unittest.TestCase):
    def test_constructor_and_defaults(self):
        # Test default constructor
        synth = M8WavSynth()
        
        # Check type is set correctly
        self.assertEqual(synth.type, 0x00)
        
        # Check synth object is created
        self.assertIsInstance(synth.synth, M8WavSynthParams)
        
        # Check common parameters
        self.assertNotEqual(synth.name, "")  # Should auto-generate a name
        self.assertEqual(synth.transpose, 0x4)
        self.assertEqual(synth.eq, 0x1)
        self.assertEqual(synth.table_tick, 0x01)
        self.assertEqual(synth.volume, 0x0)
        self.assertEqual(synth.pitch, 0x0)
        self.assertEqual(synth.finetune, 0x80)
        
        # Test with kwargs for both common and synth-specific parameters
        synth = M8WavSynth(
            # Common instrument parameters
            name="TestWavSynth",
            transpose=0x5,
            eq=0x2,
            table_tick=0x02,
            volume=0x10,
            pitch=0x20,
            finetune=0x90,
            
            # WavSynth-specific parameters
            shape=0x1,
            size=0x70,
            mult=0x90,
            cutoff=0xE0,
            pan=0x60
        )
        
        # Check common parameters
        self.assertEqual(synth.name, "TestWavSynth")
        self.assertEqual(synth.transpose, 0x5)
        self.assertEqual(synth.eq, 0x2)
        self.assertEqual(synth.table_tick, 0x02)
        self.assertEqual(synth.volume, 0x10)
        self.assertEqual(synth.pitch, 0x20)
        self.assertEqual(synth.finetune, 0x90)
        
        # Check synth-specific parameters
        self.assertEqual(synth.synth.shape, 0x1)
        self.assertEqual(synth.synth.size, 0x70)
        self.assertEqual(synth.synth.mult, 0x90)
        self.assertEqual(synth.synth.cutoff, 0xE0)
        self.assertEqual(synth.synth.pan, 0x60)
    
    def test_read_specific_parameters(self):
        # Create a WavSynth
        synth = M8WavSynth()
        
        # Create test binary data for synth parameters (with offset)
        # We need data for the full instrument including the synth parameters
        binary_data = bytearray([0] * 18)  # First 18 bytes (common instrument parameters)
        
        # Add synth-specific parameters
        binary_data.extend([
            0x01,   # shape
            0x70,   # size
            0x90,   # mult
            0x10,   # warp
            0x20,   # scan
            0x02,   # filter
            0xE0,   # cutoff
            0x30,   # res
            0x40,   # amp
            0x50,   # limit
            0x60,   # pan
            0xB0,   # dry
            0x70,   # chorus
            0x80,   # delay
            0x90    # reverb
        ])
        
        # Call the method to read specific parameters
        # This would normally be called by _read_parameters in the base class
        synth._read_specific_parameters(binary_data, 18)
        
        # Check synth parameters were read correctly
        self.assertEqual(synth.synth.shape, 0x1)
        self.assertEqual(synth.synth.size, 0x70)
        self.assertEqual(synth.synth.mult, 0x90)
        self.assertEqual(synth.synth.warp, 0x10)
        self.assertEqual(synth.synth.scan, 0x20)
        self.assertEqual(synth.synth.filter, 0x2)
        self.assertEqual(synth.synth.cutoff, 0xE0)
        self.assertEqual(synth.synth.res, 0x30)
        self.assertEqual(synth.synth.amp, 0x40)
        self.assertEqual(synth.synth.limit, 0x50)
        self.assertEqual(synth.synth.pan, 0x60)
        self.assertEqual(synth.synth.dry, 0xB0)
        self.assertEqual(synth.synth.chorus, 0x70)
        self.assertEqual(synth.synth.delay, 0x80)
        self.assertEqual(synth.synth.reverb, 0x90)
    
    def test_write_specific_parameters(self):
        # Create a WavSynth with specific parameters
        synth = M8WavSynth(
            shape=0x1,
            size=0x70,
            mult=0x90,
            warp=0x10,
            scan=0x20,
            filter=0x2,
            cutoff=0xE0,
            res=0x30,
            amp=0x40,
            limit=0x50,
            pan=0x60,
            dry=0xB0,
            chorus=0x70,
            delay=0x80,
            reverb=0x90
        )
        
        # Call the method to write specific parameters
        # This would normally be called by write in the base class
        binary = synth._write_specific_parameters()
        
        # Check the binary output
        self.assertEqual(len(binary), 33)  # Should contain 33 bytes
        
        # Check synth-specific parameters
        self.assertEqual(binary[18], 0x1)   # shape
        self.assertEqual(binary[19], 0x70)  # size
        self.assertEqual(binary[20], 0x90)  # mult
        self.assertEqual(binary[21], 0x10)  # warp
        self.assertEqual(binary[22], 0x20)  # scan
        self.assertEqual(binary[23], 0x2)   # filter
        self.assertEqual(binary[24], 0xE0)  # cutoff
        self.assertEqual(binary[25], 0x30)  # res
        self.assertEqual(binary[26], 0x40)  # amp
        self.assertEqual(binary[27], 0x50)  # limit
        self.assertEqual(binary[28], 0x60)  # pan
        self.assertEqual(binary[29], 0xB0)  # dry
        self.assertEqual(binary[30], 0x70)  # chorus
        self.assertEqual(binary[31], 0x80)  # delay
        self.assertEqual(binary[32], 0x90)  # reverb
    
    def test_is_empty(self):
        # Empty WavSynth (default values)
        synth = M8WavSynth(name="")
        self.assertTrue(synth.is_empty())
        
        # Non-empty WavSynth (with name)
        synth = M8WavSynth(name="TestWavSynth")
        self.assertFalse(synth.is_empty())
        
        # Non-empty WavSynth (with volume)
        synth = M8WavSynth(name="", volume=0x10)
        self.assertFalse(synth.is_empty())
        
        # Non-empty WavSynth (with shape)
        synth = M8WavSynth(name="", shape=0x1)
        self.assertFalse(synth.is_empty())
    
    def test_add_modulator(self):
        # Create a WavSynth
        synth = M8WavSynth()
        
        # Add a modulator
        mod = M8LFO(destination=2, amount=100, frequency=50)
        slot = synth.add_modulator(mod)
        
        # Should use first slot
        self.assertEqual(slot, 0)
        self.assertEqual(synth.modulators[0].type, M8LFO.TYPE_VALUE)
        self.assertEqual(synth.modulators[0].destination, 2)
        self.assertEqual(synth.modulators[0].amount, 100)
        self.assertEqual(synth.modulators[0].frequency, 50)
    
    def test_as_dict(self):
        # Create a WavSynth with specific parameters
        synth = M8WavSynth(
            # Common parameters
            name="TestWavSynth",
            transpose=0x5,
            eq=0x2,
            
            # Synth-specific parameters
            shape=0x1,
            size=0x70,
            mult=0x90,
            cutoff=0xE0,
            pan=0x60
        )
        
        # Add a modulator
        mod = M8LFO(destination=2, amount=100, frequency=50)
        synth.modulators[0] = mod
        
        # Convert to dict
        result = synth.as_dict()
        
        # Check common parameters
        self.assertEqual(result["type"], 0x00)
        self.assertEqual(result["name"], "TestWavSynth")
        self.assertEqual(result["transpose"], 0x5)
        self.assertEqual(result["eq"], 0x2)
        
        # Check synth-specific parameters
        self.assertEqual(result["shape"], 0x1)
        self.assertEqual(result["size"], 0x70)
        self.assertEqual(result["mult"], 0x90)
        self.assertEqual(result["cutoff"], 0xE0)
        self.assertEqual(result["pan"], 0x60)
        
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