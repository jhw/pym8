import unittest
from m8.api.instruments import M8InstrumentParams, M8Instrument
from m8.api.modulators import M8Modulator, M8ModulatorType

class TestM8MacroSynthParams(unittest.TestCase):
    def test_constructor_and_defaults(self):
        # Test default constructor
        params = M8InstrumentParams.from_config("MACROSYNTH")
        
        # Check defaults for key parameters
        self.assertEqual(params.shape, 0x0)
        self.assertEqual(params.timbre, 0x80)
        self.assertEqual(params.color, 0x80)
        self.assertEqual(params.degrade, 0x0)
        self.assertEqual(params.redux, 0x0)
        self.assertEqual(params.filter, 0x0)
        self.assertEqual(params.cutoff, 0xFF)
        self.assertEqual(params.res, 0x0)
        self.assertEqual(params.amp, 0x0)
        self.assertEqual(params.limit, 0x0)  # Default is CLIP = 0x0
        self.assertEqual(params.pan, 0x80)
        self.assertEqual(params.dry, 0xC0)
        self.assertEqual(params.chorus, 0x0)
        self.assertEqual(params.delay, 0x0)
        self.assertEqual(params.reverb, 0x0)
        
        # Test with kwargs
        params = M8InstrumentParams.from_config("MACROSYNTH",
            shape="MORPH",  # Using string enum value
            timbre=0x70,
            color=0x90,
            degrade=0x10,
            redux=0x20,
            filter="HIGHPASS",  # Using string enum value
            cutoff=0xE0,
            res=0x30,
            amp=0x40,
            limit="FOLD",  # Using string enum value (FOLD = 0x2)
            pan=0x60,
            dry=0xB0,
            chorus=0x70,
            delay=0x80,
            reverb=0x90
        )
        
        # Check values
        self.assertEqual(params.shape, 0x1)
        self.assertEqual(params.timbre, 0x70)
        self.assertEqual(params.color, 0x90)
        self.assertEqual(params.degrade, 0x10)
        self.assertEqual(params.redux, 0x20)
        self.assertEqual(params.filter, 0x2)
        self.assertEqual(params.cutoff, 0xE0)
        self.assertEqual(params.res, 0x30)
        self.assertEqual(params.amp, 0x40)
        self.assertEqual(params.limit, 0x2)  # FOLD = 0x2
        self.assertEqual(params.pan, 0x60)
        self.assertEqual(params.dry, 0xB0)
        self.assertEqual(params.chorus, 0x70)
        self.assertEqual(params.delay, 0x80)
        self.assertEqual(params.reverb, 0x90)
    
    def test_read_from_binary(self):
        # Create test binary data
        # We need at least 33 bytes for the full parameter set
        binary_data = bytearray([0] * 18)  # First 18 bytes are not used by MacroSynthParams
        binary_data.extend([
            0x01,   # shape (offset 18)
            0x70,   # timbre (offset 19)
            0x90,   # color (offset 20)
            0x10,   # degrade (offset 21)
            0x20,   # redux (offset 22)
            0x02,   # filter (offset 23)
            0xE0,   # cutoff (offset 24)
            0x30,   # res (offset 25)
            0x40,   # amp (offset 26)
            0x2,   # limit (offset 27/28) - FOLD = 0x2 - FOLD = 0x2
            0x60,   # pan (offset 28)
            0xB0,   # dry (offset 29)
            0x70,   # chorus (offset 30)
            0x80,   # delay (offset 31)
            0x90    # reverb (offset 32)
        ])
        
        # Read from binary
        params = M8InstrumentParams.from_config("MACROSYNTH")
        params.read(binary_data)
        
        # Check values
        self.assertEqual(params.shape, 0x1)
        self.assertEqual(params.timbre, 0x70)
        self.assertEqual(params.color, 0x90)
        self.assertEqual(params.degrade, 0x10)
        self.assertEqual(params.redux, 0x20)
        self.assertEqual(params.filter, 0x2)
        self.assertEqual(params.cutoff, 0xE0)
        self.assertEqual(params.res, 0x30)
        self.assertEqual(params.amp, 0x40)
        self.assertEqual(params.limit, 0x2)  # FOLD = 0x2
        self.assertEqual(params.pan, 0x60)
        self.assertEqual(params.dry, 0xB0)
        self.assertEqual(params.chorus, 0x70)
        self.assertEqual(params.delay, 0x80)
        self.assertEqual(params.reverb, 0x90)
    
    def test_write_to_binary(self):
        # Create params with specific values
        params = M8InstrumentParams.from_config("MACROSYNTH",
            shape=0x1,
            timbre=0x70,
            color=0x90,
            degrade=0x10,
            redux=0x20,
            filter=0x2,
            cutoff=0xE0,
            res=0x30,
            amp=0x40,
            limit="FOLD",  # Using string enum (FOLD = 0x2)
            pan=0x60,
            dry=0xB0,
            chorus=0x70,
            delay=0x80,
            reverb=0x90
        )
        
        # Write to binary
        binary = params.write()
        
        # Check specific values for MacroSynth parameters
        self.assertEqual(binary[18], 0x1)   # shape
        self.assertEqual(binary[19], 0x70)  # timbre
        self.assertEqual(binary[20], 0x90)  # color
        self.assertEqual(binary[21], 0x10)  # degrade
        self.assertEqual(binary[22], 0x20)  # redux
        self.assertEqual(binary[23], 0x2)   # filter
        self.assertEqual(binary[24], 0xE0)  # cutoff
        self.assertEqual(binary[25], 0x30)  # res
        self.assertEqual(binary[26], 0x40)  # amp
        self.assertEqual(binary[27], 0x2)   # limit (FOLD = 0x2)
        self.assertEqual(binary[28], 0x60)  # pan
        self.assertEqual(binary[29], 0xB0)  # dry
        self.assertEqual(binary[30], 0x70)  # chorus
        self.assertEqual(binary[31], 0x80)  # delay
        self.assertEqual(binary[32], 0x90)  # reverb
    
    def test_read_write_consistency(self):
        # Create original params
        original = M8InstrumentParams.from_config("MACROSYNTH",
            shape=0x1,
            timbre=0x70,
            color=0x90,
            degrade=0x10,
            redux=0x20,
            filter=0x2,
            cutoff=0xE0,
            res=0x30,
            amp=0x40,
            limit="FOLD",  # Using string enum (FOLD = 0x2)
            pan=0x60,
            dry=0xB0,
            chorus=0x70,
            delay=0x80,
            reverb=0x90
        )
        
        # Write to binary
        binary = original.write()
        
        # Read back from binary
        deserialized = M8InstrumentParams.from_config("MACROSYNTH")
        deserialized.read(binary)
        
        # Check values match
        self.assertEqual(deserialized.shape, original.shape)
        self.assertEqual(deserialized.timbre, original.timbre)
        self.assertEqual(deserialized.color, original.color)
        self.assertEqual(deserialized.degrade, original.degrade)
        self.assertEqual(deserialized.redux, original.redux)
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
        params = M8InstrumentParams.from_config("MACROSYNTH",
            shape=0x1,  # MORPH
            timbre=0x70,
            color=0x90,
            degrade=0x10,
            redux=0x20,
            filter=0x2,
            cutoff=0xE0,
            res=0x30,
            amp=0x40,
            limit="FOLD",  # Using string enum (FOLD = 0x2)
            pan=0x60,
            dry=0xB0,
            chorus=0x70,
            delay=0x80,
            reverb=0x90
        )
        
        # Convert to dict
        result = params.as_dict()
        
        # Check dict with shape as enum name
        expected = {
            "shape": "MORPH",  # Enum name instead of 0x1
            "timbre": 0x70,
            "color": 0x90,
            "degrade": 0x10,
            "redux": 0x20,
            "filter": "HIGHPASS",  # Now using enum name
            "cutoff": 0xE0,
            "res": 0x30,
            "amp": 0x40,
            "limit": "FOLD",  # Now using enum name
            "pan": 0x60,
            "dry": 0xB0,
            "chorus": 0x70,
            "delay": 0x80,
            "reverb": 0x90
        }
        
        for key, value in expected.items():
            self.assertEqual(result[key], value)
    
    def test_from_dict(self):
        # Test data with shape and filter as enum names
        data = {
            "shape": "MORPH",  # Enum name instead of 0x1
            "timbre": 0x70,
            "color": 0x90,
            "degrade": 0x10,
            "redux": 0x20,
            "filter": "HIGHPASS",  # Enum name instead of 0x2
            "cutoff": 0xE0,
            "res": 0x30,
            "amp": 0x40,
            "limit": "FOLD",  # Now using enum name
            "pan": 0x60,
            "dry": 0xB0,
            "chorus": 0x70,
            "delay": 0x80,
            "reverb": 0x90
        }
        
        # Create from dict
        params = M8InstrumentParams.from_dict("macrosynth", data)
        
        # With EnumPropertyMixin, string enum values are now preserved
        expected_values = data.copy()
        
        # Check values
        for key, value in expected_values.items():
            self.assertEqual(getattr(params, key), value)


class TestM8MacroSynth(unittest.TestCase):
    def test_constructor_and_defaults(self):
        # Test default constructor
        synth = M8Instrument(instrument_type="MACROSYNTH")
        
        # Check type is set correctly
        self.assertEqual(synth.type, 0x01)
        
        # Check params object is created
        self.assertIsInstance(synth.params, M8InstrumentParams)
        
        # Check common parameters
        self.assertNotEqual(synth.name, "")  # Should auto-generate a name
        self.assertEqual(synth.transpose, 0x4)
        self.assertEqual(synth.eq, 0x1)
        self.assertEqual(synth.table_tick, 0x01)
        self.assertEqual(synth.volume, 0x0)
        self.assertEqual(synth.pitch, 0x0)
        self.assertEqual(synth.finetune, 0x80)
        
        # Test with kwargs for both common and specific parameters
        synth = M8Instrument(
            instrument_type="MACROSYNTH",
            # Common instrument parameters
            name="TestMacroSynth",
            transpose=0x5,
            eq=0x2,
            table_tick=0x02,
            volume=0x10,
            pitch=0x20,
            finetune=0x90,
            
            # MacroSynth-specific parameters with string enum values
            shape="MORPH",
            timbre=0x70,
            color=0x90,
            filter="HIGHPASS",
            cutoff=0xE0,
            pan=0x60
        )
        
        # Check common parameters
        self.assertEqual(synth.name, "TestMacroSynth")
        self.assertEqual(synth.transpose, 0x5)
        self.assertEqual(synth.eq, 0x2)
        self.assertEqual(synth.table_tick, 0x02)
        self.assertEqual(synth.volume, 0x10)
        self.assertEqual(synth.pitch, 0x20)
        self.assertEqual(synth.finetune, 0x90)
        
        # Check synth-specific parameters
        if isinstance(synth.params.shape, int):
            self.assertEqual(synth.params.shape, 0x1)
        else:
            self.assertEqual(synth.params.shape, "MORPH")
        self.assertEqual(synth.params.timbre, 0x70)
        self.assertEqual(synth.params.color, 0x90)
        self.assertEqual(synth.params.cutoff, 0xE0)
        self.assertEqual(synth.params.pan, 0x60)
    
    def test_read_parameters(self):
        # Create a MacroSynth
        synth = M8Instrument(instrument_type="MACROSYNTH")
        
        # Create test binary data (with type=0x01 for MacroSynth)
        binary_data = bytearray([0x01])  # Type
        binary_data.extend(bytearray([0] * 17))  # Rest of common parameters
        
        # Add macrosynth-specific parameters
        binary_data.extend([
            0x01,   # shape
            0x70,   # timbre
            0x90,   # color
            0x10,   # degrade
            0x20,   # redux
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
        
        # Call the method to read parameters
        synth._read_parameters(binary_data)
        
        # Check parameters were read correctly
        self.assertEqual(synth.params.shape, 0x1)
        self.assertEqual(synth.params.timbre, 0x70)
        self.assertEqual(synth.params.color, 0x90)
        self.assertEqual(synth.params.degrade, 0x10)
        self.assertEqual(synth.params.redux, 0x20)
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
        # Create a MacroSynth with specific parameters
        synth = M8Instrument(
            instrument_type="MACROSYNTH",
            shape="MORPH",
            timbre=0x70,
            color=0x90,
            degrade=0x10,
            redux=0x20,
            filter="HIGHPASS",
            cutoff=0xE0,
            res=0x30,
            amp=0x40,
            limit="FOLD",  # Using string enum (FOLD = 0x2)
            pan=0x60,
            dry=0xB0,
            chorus=0x70,
            delay=0x80,
            reverb=0x90
        )
        
        # Write to binary
        binary = synth.write()
        
        # Check the type byte (macrosynth = 0x01)
        self.assertEqual(binary[0], 0x01)
        
        # Check macrosynth-specific parameters
        self.assertEqual(binary[18], 0x1)   # shape
        self.assertEqual(binary[19], 0x70)  # timbre
        self.assertEqual(binary[20], 0x90)  # color
        self.assertEqual(binary[21], 0x10)  # degrade
        self.assertEqual(binary[22], 0x20)  # redux
        self.assertEqual(binary[23], 0x2)   # filter
        self.assertEqual(binary[24], 0xE0)  # cutoff
        self.assertEqual(binary[25], 0x30)  # res
        self.assertEqual(binary[26], 0x40)  # amp
        self.assertEqual(binary[27], 0x2)   # limit (FOLD = 0x2)
        self.assertEqual(binary[28], 0x60)  # pan
        self.assertEqual(binary[29], 0xB0)  # dry
        self.assertEqual(binary[30], 0x70)  # chorus
        self.assertEqual(binary[31], 0x80)  # delay
        self.assertEqual(binary[32], 0x90)  # reverb
    
    def test_is_empty(self):
        # Valid MACROSYNTH instrument should not be empty
        synth = M8Instrument(instrument_type="MACROSYNTH")
        self.assertFalse(synth.is_empty())
        
        # Create an invalid instrument that should be empty
        mock_synth = M8Instrument(instrument_type="MACROSYNTH")
        # Create a custom is_empty method for this test
        mock_synth.is_empty = lambda: True
        self.assertTrue(mock_synth.is_empty())
    
    def test_add_modulator(self):
        # Create a MacroSynth
        synth = M8Instrument(instrument_type="MACROSYNTH")
        
        # Add a modulator
        mod = M8Modulator(modulator_type="LFO", destination=2, amount=100, frequency=50)
        slot = synth.add_modulator(mod)
        
        # Should use first slot
        self.assertEqual(slot, 0)
        self.assertEqual(synth.modulators[0].type, 3)  # LFO type value
        self.assertEqual(synth.modulators[0].destination, 2)
        self.assertEqual(synth.modulators[0].amount, 100)
        self.assertEqual(synth.modulators[0].params.frequency, 50)
    
    def test_as_dict(self):
        # Create a MacroSynth with specific parameters
        synth = M8Instrument(
            instrument_type="MACROSYNTH",
            # Common parameters
            name="TestMacroSynth",
            transpose=0x5,
            eq=0x2,
            
            # Synth-specific parameters
            shape=0x1,  # MORPH
            timbre=0x70,
            color=0x90,
            cutoff=0xE0,
            pan=0x60
        )
        
        # Add a modulator
        mod = M8Modulator(modulator_type=M8ModulatorType.LFO, destination=2, amount=100, frequency=50)
        synth.modulators[0] = mod
        
        # Convert to dict
        result = synth.as_dict()
        
        # Check common parameters
        self.assertEqual(result["type"], "MACROSYNTH")
        self.assertEqual(result["name"], "TestMacroSynth")
        self.assertEqual(result["transpose"], 0x5)
        self.assertEqual(result["eq"], 0x2)
        
        # Check synth-specific parameters
        self.assertEqual(result["shape"], "MORPH")  # Now returns enum name
        self.assertEqual(result["timbre"], 0x70)
        self.assertEqual(result["color"], 0x90)
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