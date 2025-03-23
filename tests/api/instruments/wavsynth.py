import unittest
from m8.api.instruments import M8Instrument, M8Params
from m8.api.modulators import M8Modulator, M8ModulatorType

class TestM8Params(unittest.TestCase):
    def test_constructor_and_defaults(self):
        # Test default constructor for WavSynth params
        params = M8Params.from_config("wavsynth")
        
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
        params = M8Params.from_config("wavsynth",
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
        
        # Create params and read from binary
        params = M8Params.from_config("wavsynth")
        params.read(binary_data)
        
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
        params = M8Params.from_config("wavsynth",
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
        
        # Check binary output (note: the minimum size may be different)
        min_size = 33  # Should at least include up to reverb at offset 32
        self.assertGreaterEqual(len(binary), min_size)
        
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
        original = M8Params.from_config("wavsynth",
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
        deserialized = M8Params.from_config("wavsynth")
        deserialized.read(binary)
        
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
        params = M8Params.from_config("wavsynth",
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
            "shape": "PULSE25",  # Now using enum name
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


class TestM8WavSynthInstrument(unittest.TestCase):
    def test_constructor_and_defaults(self):
        # Test default constructor
        synth = M8Instrument(instrument_type="wavsynth")
        
        # Check type is set correctly
        self.assertEqual(synth.type, 0x00)
        
        # Check params object is created
        self.assertTrue(hasattr(synth, "params"))
        
        # Check common parameters
        self.assertNotEqual(synth.name, "")  # Should auto-generate a name
        self.assertEqual(synth.transpose, 0x4)
        self.assertEqual(synth.eq, 0x1)
        self.assertEqual(synth.table_tick, 0x01)
        self.assertEqual(synth.volume, 0x0)
        self.assertEqual(synth.pitch, 0x0)
        self.assertEqual(synth.finetune, 0x80)
        
        # Test with kwargs for both common and synth-specific parameters
        synth = M8Instrument(
            instrument_type="wavsynth",
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
        self.assertEqual(synth.params.shape, 0x1)
        self.assertEqual(synth.params.size, 0x70)
        self.assertEqual(synth.params.mult, 0x90)
        self.assertEqual(synth.params.cutoff, 0xE0)
        self.assertEqual(synth.params.pan, 0x60)
    
    def test_read_parameters(self):
        # Create a WavSynth
        synth = M8Instrument(instrument_type="wavsynth")
        
        # Create test binary data
        binary_data = bytearray([
            0x00,   # type (WavSynth)
            0x54, 0x45, 0x53, 0x54, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # name "TEST"
            0x42,   # transpose/eq (4/2)
            0x02,   # table_tick
            0x10,   # volume
            0x20,   # pitch
            0x90,   # finetune
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
        
        # Extend with empty modulator data
        binary_data.extend([0] * (63 - len(binary_data)))  # Fill up to modulator offset
        binary_data.extend([0] * 24)  # Four empty modulators (6 bytes each)
        
        # Call the method to read parameters
        synth._read_parameters(binary_data)
        
        # Check common parameters
        self.assertEqual(synth.type, 0x00)
        self.assertEqual(synth.name, "TEST")
        self.assertEqual(synth.transpose, 0x4)
        self.assertEqual(synth.eq, 0x2)
        self.assertEqual(synth.table_tick, 0x02)
        self.assertEqual(synth.volume, 0x10)
        self.assertEqual(synth.pitch, 0x20)
        self.assertEqual(synth.finetune, 0x90)
        
        # Check synth parameters
        self.assertEqual(synth.params.shape, 0x1)
        self.assertEqual(synth.params.size, 0x70)
        self.assertEqual(synth.params.mult, 0x90)
        self.assertEqual(synth.params.warp, 0x10)
        self.assertEqual(synth.params.scan, 0x20)
        self.assertEqual(synth.params.filter, 0x2)
        self.assertEqual(synth.params.cutoff, 0xE0)
        self.assertEqual(synth.params.res, 0x30)
        self.assertEqual(synth.params.amp, 0x40)
        self.assertEqual(synth.params.limit, 0x50)
        self.assertEqual(synth.params.pan, 0x60)
        self.assertEqual(synth.params.dry, 0xB0)
        self.assertEqual(synth.params.chorus, 0x70)
        self.assertEqual(synth.params.delay, 0x80)
        self.assertEqual(synth.params.reverb, 0x90)
    
    def test_write(self):
        # Create a WavSynth with specific parameters
        synth = M8Instrument(
            instrument_type="wavsynth",
            name="TEST",
            transpose=0x4,
            eq=0x2,
            table_tick=0x02,
            volume=0x10,
            pitch=0x20,
            finetune=0x90,
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
        
        # Call the method to write
        binary = synth.write()
        
        # Check the binary output
        self.assertEqual(len(binary), 215)  # Should be BLOCK_SIZE bytes
        
        # Check common parameters
        self.assertEqual(binary[0], 0x00)  # type
        self.assertEqual(binary[1:5], b"TEST")  # name (first 4 bytes)
        self.assertEqual(binary[13], 0x42)  # transpose/eq
        self.assertEqual(binary[14], 0x02)  # table_tick
        self.assertEqual(binary[15], 0x10)  # volume
        self.assertEqual(binary[16], 0x20)  # pitch
        self.assertEqual(binary[17], 0x90)  # finetune
        
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
        synth = M8Instrument(instrument_type="wavsynth", name="")
        self.assertTrue(synth.is_empty())
        
        # Non-empty WavSynth (with name)
        synth = M8Instrument(instrument_type="wavsynth", name="TestWavSynth")
        self.assertFalse(synth.is_empty())
        
        # Non-empty WavSynth (with volume)
        synth = M8Instrument(instrument_type="wavsynth", name="", volume=0x10)
        self.assertFalse(synth.is_empty())
        
        # Non-empty WavSynth (with shape)
        synth = M8Instrument(instrument_type="wavsynth", name="", shape=0x1)
        self.assertFalse(synth.is_empty())
    
    def test_add_modulator(self):
        # Create a WavSynth
        synth = M8Instrument(instrument_type="wavsynth")
        
        # Add a modulator
        mod = M8Modulator(modulator_type="lfo", destination=2, amount=100, frequency=50)
        slot = synth.add_modulator(mod)
        
        # Should use first slot
        self.assertEqual(slot, 0)
        self.assertEqual(synth.modulators[0].type, 3)  # LFO type value
        self.assertEqual(synth.modulators[0].destination, 2)
        self.assertEqual(synth.modulators[0].amount, 100)
        self.assertEqual(synth.modulators[0].params.frequency, 50)
    
    def test_as_dict(self):
        # Create a WavSynth with specific parameters
        synth = M8Instrument(
            instrument_type="wavsynth",
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
        mod = M8Modulator(modulator_type=M8ModulatorType.LFO, destination=2, amount=100, frequency=50)
        synth.modulators[0] = mod
        
        # Convert to dict
        result = synth.as_dict()
        
        # Check common parameters
        self.assertEqual(result["type"], "WAVSYNTH")
        self.assertEqual(result["name"], "TestWavSynth")
        self.assertEqual(result["transpose"], 0x5)
        self.assertEqual(result["eq"], 0x2)
        
        # Check synth-specific parameters
        self.assertEqual(result["shape"], "PULSE25")  # Now using enum name
        self.assertEqual(result["size"], 0x70)
        self.assertEqual(result["mult"], 0x90)
        self.assertEqual(result["cutoff"], 0xE0)
        self.assertEqual(result["pan"], 0x60)
        
        # Check modulators
        self.assertIn("modulators", result)
        self.assertIsInstance(result["modulators"], list)
        self.assertGreater(len(result["modulators"]), 0)
        self.assertEqual(result["modulators"][0]["type"], "LFO")  # LFO type name
        self.assertEqual(result["modulators"][0]["destination"], 2)
        self.assertEqual(result["modulators"][0]["amount"], 100)
        self.assertEqual(result["modulators"][0]["frequency"], 50)


if __name__ == '__main__':
    unittest.main()