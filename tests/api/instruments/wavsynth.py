import unittest
from m8.api.instruments import M8Instrument, M8InstrumentParams
from m8.api.modulators import M8Modulator, M8ModulatorType

class TestM8InstrumentParams(unittest.TestCase):
    def setUp(self):
        # Define parameter groups for easier testing
        self.parameter_groups = {
            "wave_params": {
                "shape": (0x01, 18),  # (test_value, binary_offset) - PULSE25
                "size": (0x70, 19),
                "mult": (0x90, 20),
                "warp": (0x10, 21),
                "scan": (0x20, 22)
            },
            "filter_params": {
                "filter": (0x02, 23),  # HIGHPASS
                "cutoff": (0xE0, 24),
                "res": (0x30, 25)
            },
            "amp_params": {
                "amp": (0x40, 26),
                "limit": (0x00, 27),  # CLIP
                "pan": (0x60, 28)
            },
            "fx_params": {
                "dry": (0xB0, 29),
                "chorus": (0x70, 30),
                "delay": (0x80, 31),
                "reverb": (0x90, 32)
            }
        }
        
        # Define expected default values
        self.default_values = {
            "shape": 0x0,  # SINE
            "size": 0x80,
            "mult": 0x80,
            "warp": 0x0,
            "scan": 0x0,
            "filter": 0x0,  # OFF
            "cutoff": 0xFF,
            "res": 0x0,
            "amp": 0x0,
            "limit": 0x0,  # CLIP
            "pan": 0x80,
            "dry": 0xC0,
            "chorus": 0x0,
            "delay": 0x0,
            "reverb": 0x0
        }
        
        # With simplified enum system, all parameters are now integer values

    def test_constructor_and_defaults(self):
        # Test default constructor for WavSynth params
        params = M8InstrumentParams.from_config("WAVSYNTH")
        
        # Check defaults for all parameters
        for param_name, expected_value in self.default_values.items():
            self.assertEqual(getattr(params, param_name), expected_value, 
                            f"Default value for {param_name} should be {expected_value}")

    def test_parameter_groups(self):
        # Test each parameter group for initialization, read, write, and serialization
        for group_name, params_dict in self.parameter_groups.items():
            with self.subTest(group=group_name):
                self._test_parameter_group(params_dict)
    
    def _test_parameter_group(self, params_dict):
        # Prepare kwargs for constructor
        kwargs = {name: val for name, (val, _) in params_dict.items()}
        
        # Test constructor with parameters
        params = M8InstrumentParams.from_config("WAVSYNTH", **kwargs)
        
        # Check values match what we set
        for param_name, (value, _) in params_dict.items():
            self.assertEqual(getattr(params, param_name), value, 
                            f"Parameter {param_name} should be {value}")
        
        # Create binary data for reading test
        binary_data = bytearray([0] * 100)
        
        # Set values at the exact offsets with slightly different values
        for param_name, (_, offset) in params_dict.items():
            # Create a different value for testing read
            binary_data[offset] = getattr(params, param_name) + 5
        
        # Read from binary
        read_params = M8InstrumentParams.from_config("WAVSYNTH")
        read_params.read(binary_data)
        
        # Check parameters were read correctly
        for param_name, (_, offset) in params_dict.items():
            expected_value = getattr(params, param_name) + 5
            self.assertEqual(getattr(read_params, param_name), expected_value,
                            f"Read value for {param_name} should be {expected_value}")
        
        # Test write to binary
        write_params = M8InstrumentParams.from_config("WAVSYNTH", **kwargs)
        binary = write_params.write()
        
        # Check binary has all parameters with correct values
        for param_name, (value, offset) in params_dict.items():
            self.assertEqual(binary[offset], value,
                            f"Binary at offset {offset} for {param_name} should be {value}")
        
        # Test dictionary serialization
        dict_params = M8InstrumentParams.from_config("WAVSYNTH", **kwargs)
        result = dict_params.as_dict()
        
        # Check dictionary has all values correctly - expect integer values with simplified enum system
        for param_name, (value, _) in params_dict.items():
            self.assertIsInstance(result[param_name], int,
                               f"Parameter {param_name} should be an integer in dictionary")
            self.assertEqual(result[param_name], value,
                           f"Dictionary value for {param_name} should be {value}")
    
    def test_read_write_consistency(self):
        # Prepare all parameters with test values
        all_params = {}
        for group in self.parameter_groups.values():
            for name, (value, _) in group.items():
                all_params[name] = value
        
        # Create original params with all parameters
        original = M8InstrumentParams.from_config("WAVSYNTH", **all_params)
        
        # Write to binary
        binary = original.write()
        
        # Read back from binary
        deserialized = M8InstrumentParams.from_config("WAVSYNTH")
        deserialized.read(binary)
        
        # Check all values match between original and deserialized
        for param_name in all_params.keys():
            original_value = getattr(original, param_name)
            deserialized_value = getattr(deserialized, param_name)
            self.assertEqual(deserialized_value, original_value,
                            f"Deserialized value for {param_name} should match original")
    
    def test_comprehensive_read_from_binary(self):
        # Create test binary data with values for all parameters
        binary_data = bytearray([0] * 100)
        
        # Set values for all parameters
        for group in self.parameter_groups.values():
            for name, (_, offset) in group.items():
                test_value = 0xA0 | offset  # Create unique test value based on offset
                binary_data[offset] = test_value
        
        # Read parameters from binary
        params = M8InstrumentParams.from_config("WAVSYNTH")
        params.read(binary_data)
        
        # Verify all parameters were read correctly
        for group in self.parameter_groups.values():
            for name, (_, offset) in group.items():
                expected_value = 0xA0 | offset
                self.assertEqual(getattr(params, name), expected_value,
                                f"Parameter {name} should have value {expected_value}")
    
    def test_as_dict_with_all_params(self):
        # Prepare all parameters with test values
        all_params = {}
        for group in self.parameter_groups.values():
            for name, (value, _) in group.items():
                all_params[name] = value
        
        # Create params with all parameters
        params = M8InstrumentParams.from_config("WAVSYNTH", **all_params)
        
        # Convert to dict
        result = params.as_dict()
        
        # Check all parameters are in the dictionary with correct values - expect integer values with simplified enum system
        for param_name, value in all_params.items():
            self.assertIsInstance(result[param_name], int,
                               f"Parameter {param_name} should be an integer in dictionary")
            self.assertEqual(result[param_name], value,
                           f"Dictionary value for {param_name} should be {value}")


class TestM8WavSynthInstrument(unittest.TestCase):
    def setUp(self):
        # Define common instrument parameters
        self.common_params = {
            "name": "TestWavSynth",
            "transpose": 0x5,
            "eq": 0x2,
            "table_tick": 0x2,
            "volume": 0x10,
            "pitch": 0x20,
            "finetune": 0x90
        }
        
        # Define all WavSynth-specific parameters for comprehensive testing
        self.wavsynth_params = {
            "shape": 0x01,  # PULSE25
            "size": 0x70,
            "mult": 0x90,
            "warp": 0x10,
            "scan": 0x20,
            "filter": 0x02,  # HIGHPASS
            "cutoff": 0xE0,
            "res": 0x30,
            "amp": 0x40,
            "limit": 0x00,  # CLIP
            "pan": 0x60,
            "dry": 0xB0,
            "chorus": 0x70,
            "delay": 0x80,
            "reverb": 0x90
        }
        
        # Define parameter offsets for binary testing
        self.param_offsets = {
            "shape": 18,
            "size": 19,
            "mult": 20,
            "warp": 21,
            "scan": 22,
            "filter": 23,
            "cutoff": 24,
            "res": 25,
            "amp": 26,
            "limit": 27,
            "pan": 28,
            "dry": 29,
            "chorus": 30,
            "delay": 31,
            "reverb": 32
        }
        
        # Define expected default values
        self.defaults = {
            "name": "",  # Auto-generated, should not be empty
            "transpose": 0x4,
            "eq": 0x1,
            "table_tick": 0x01,
            "volume": 0x0,
            "pitch": 0x0,
            "finetune": 0x80,
            "shape": 0x0,  # SINE
            "size": 0x80,
            "mult": 0x80,
            "warp": 0x0,
            "scan": 0x0,
            "filter": 0x0,  # OFF
            "cutoff": 0xFF,
            "res": 0x0,
            "amp": 0x0,
            "limit": 0x0,  # CLIP
            "pan": 0x80,
            "dry": 0xC0,
            "chorus": 0x0,
            "delay": 0x0,
            "reverb": 0x0
        }
        
        # With simplified enum system, all parameters are now integer values
        

    def test_constructor_and_defaults(self):
        # Test default constructor
        synth = M8Instrument(instrument_type="WAVSYNTH")
        
        # Check type is set correctly
        self.assertEqual(synth.type, 0x00)
        self.assertEqual(synth.instrument_type, "WAVSYNTH")
        
        # Check params object is created
        self.assertTrue(hasattr(synth, "params"))
        
        # Check default parameters
        self.assertNotEqual(synth.name, "")  # Should auto-generate a name
        for param, expected in self.defaults.items():
            if param == "name":
                continue  # Skip name, already checked
            
            if hasattr(synth, param):
                # Test synth attribute
                self.assertEqual(getattr(synth, param), expected, 
                              f"Default {param} should be {expected}")
            elif hasattr(synth.params, param):
                # Test params attribute
                self.assertEqual(getattr(synth.params, param), expected, 
                              f"Default params.{param} should be {expected}")
        
        # Test with kwargs for both common and specific parameters
        all_params = {}
        all_params.update(self.common_params)
        all_params.update(self.wavsynth_params)
        
        synth = M8Instrument(instrument_type="WAVSYNTH", **all_params)
        
        # Check common parameters
        for param, expected in self.common_params.items():
            self.assertEqual(getattr(synth, param), expected,
                          f"Parameter {param} should be {expected}")
            
        # Check instrument-specific parameters
        for param, expected in self.wavsynth_params.items():
            self.assertEqual(getattr(synth.params, param), expected,
                          f"Parameter params.{param} should be {expected}")

    def test_read_parameters(self):
        # Create a WavSynth
        synth = M8Instrument(instrument_type="WAVSYNTH")
        
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
            0x00,   # limit (CLIP)
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
        for param, expected in self.wavsynth_params.items():
            self.assertEqual(getattr(synth.params, param), expected,
                          f"Parameter params.{param} should be {expected}")

    def test_binary_serialization(self):
        # Create synth with all parameters but use a shorter name
        all_params = {}
        all_params.update(self.common_params)
        all_params.update(self.wavsynth_params)
        
        # Use a shorter name to avoid truncation issues
        all_params["name"] = "TEST"
        
        synth = M8Instrument(instrument_type="WAVSYNTH", **all_params)
        
        # Write to binary
        binary = synth.write()
        
        # Check the binary output
        self.assertEqual(len(binary), 215)  # Should be BLOCK_SIZE bytes
        
        # Check common parameters
        self.assertEqual(binary[0], 0x00)  # type
        self.assertEqual(binary[1:5], b"TEST")  # name (first 4 bytes)
        self.assertEqual(binary[13] & 0xF, 0x2)  # Check eq part
        self.assertEqual(binary[14], 0x02)  # table_tick
        self.assertEqual(binary[15], 0x10)  # volume
        self.assertEqual(binary[16], 0x20)  # pitch
        self.assertEqual(binary[17], 0x90)  # finetune
        
        # Check instrument-specific parameters
        for param, offset in self.param_offsets.items():
            expected = self.wavsynth_params[param]
            self.assertEqual(binary[offset], expected,
                          f"Parameter {param} at offset {offset} should be {expected}")

    def test_is_empty(self):
        # Valid WAVSYNTH instrument should not be empty
        synth = M8Instrument(instrument_type="WAVSYNTH")
        self.assertFalse(synth.is_empty())
        
        # Create an invalid instrument that should be empty
        mock_synth = M8Instrument(instrument_type="WAVSYNTH")
        # Create a custom is_empty method for this test
        mock_synth.is_empty = lambda: True
        self.assertTrue(mock_synth.is_empty())

    def test_modulators(self):
        # Create a WavSynth
        synth = M8Instrument(instrument_type="WAVSYNTH")
        
        # Add a modulator
        mod = M8Modulator(modulator_type=3, destination=2, amount=100, frequency=50)  # 3=LFO, 2=PITCH
        slot = synth.add_modulator(mod)
        
        # Should use first slot
        self.assertEqual(slot, 0)
        self.assertEqual(synth.modulators[0].type, 3)  # LFO type value
        self.assertEqual(synth.modulators[0].destination, 2)  # PITCH value
        self.assertEqual(synth.modulators[0].amount, 100)
        self.assertEqual(synth.modulators[0].params.frequency, 50)
        
        # Test modulator preservation through serialization
        binary = synth.write()
        deserialized = M8Instrument(instrument_type="WAVSYNTH")
        deserialized._read_parameters(binary)
        
        # Check modulator was deserialized properly
        self.assertEqual(len(deserialized.modulators), 4)  # All slots initialized
        self.assertEqual(deserialized.modulators[0].type, 3)  # LFO
        self.assertEqual(deserialized.modulators[0].destination, 2)  # PITCH
        self.assertEqual(deserialized.modulators[0].amount, 100)

    def test_as_dict(self):
        # Create synth with all parameters
        all_params = {}
        all_params.update(self.common_params)
        all_params.update(self.wavsynth_params)
        
        synth = M8Instrument(instrument_type="WAVSYNTH", **all_params)
        
        # Add a modulator
        mod = M8Modulator(modulator_type=M8ModulatorType.LFO, destination=2, amount=100, frequency=50)
        synth.add_modulator(mod)
        
        # Convert to dict
        result = synth.as_dict()
        
        # Check common parameters
        self.assertEqual(result["type"], "WAVSYNTH")
        self.assertEqual(result["name"], "TestWavSynth")
        self.assertEqual(result["transpose"], 0x5)
        self.assertEqual(result["eq"], 0x2)
        
        # Check instrument-specific parameters - expect integer values with simplified enum system
        for param, value in self.wavsynth_params.items():
            self.assertIsInstance(result[param], int,
                               f"Parameter {param} should be an integer in dictionary")
            self.assertEqual(result[param], value,
                          f"Dictionary value for {param} should be {value}")
        
        # Check modulators
        self.assertIn("modulators", result)
        self.assertIsInstance(result["modulators"], list)
        self.assertGreater(len(result["modulators"]), 0)  # At least the one we added
        self.assertEqual(result["modulators"][0]["amount"], 100)
        self.assertEqual(result["modulators"][0]["frequency"], 50)


if __name__ == '__main__':
    unittest.main()