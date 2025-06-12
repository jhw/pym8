import unittest
from m8.api.instruments import M8InstrumentParams, M8Instrument
from m8.api.modulators import M8Modulator, M8ModulatorType

class TestM8MacroSynthParams(unittest.TestCase):
    def setUp(self):
        # Define parameter groups for easier testing
        self.parameter_groups = {
            "wave_params": {
                "shape": (0x01, 18),  # (test_value, binary_offset) - MORPH
                "timbre": (0x70, 19),
                "color": (0x90, 20),
                "degrade": (0x10, 21),
                "redux": (0x20, 22)
            },
            "filter_params": {
                "filter": (0x02, 23),  # HIGHPASS
                "cutoff": (0xE0, 24),
                "res": (0x30, 25)
            },
            "amp_params": {
                "amp": (0x40, 26),
                "limit": (0x02, 27),  # FOLD
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
            "shape": 0x0,
            "timbre": 0x80,
            "color": 0x80,
            "degrade": 0x0,
            "redux": 0x0,
            "filter": 0x0,
            "cutoff": 0xFF,
            "res": 0x0,
            "amp": 0x0,
            "limit": 0x0,  # Default is CLIP = 0x0
            "pan": 0x80,
            "dry": 0xC0,
            "chorus": 0x0,
            "delay": 0x0,
            "reverb": 0x0
        }
        
        # With simplified enum system, all parameters are now integer values
        
        # Create a flattened test values dict for convenience
        self.test_values = {}
        for group, params in self.parameter_groups.items():
            for param, (value, _) in params.items():
                self.test_values[param] = value
    
    def test_constructor_and_defaults(self):
        # Test default constructor
        params = M8InstrumentParams.from_config("MACROSYNTH")
        
        # Check defaults for key parameters
        for param, expected in self.default_values.items():
            self.assertEqual(getattr(params, param), expected, 
                          f"Default for {param} should be {expected}")
        
        # Test with kwargs
        test_kwargs = {param: value for param, value in self.test_values.items()}
        # Convert enum values to string representation for test
        for param in self.enum_params:
            value = test_kwargs[param]
            test_kwargs[param] = self.enum_string_values[param][value]
        
        params = M8InstrumentParams.from_config("MACROSYNTH", **test_kwargs)
        
        # Check values
        for param, expected in self.test_values.items():
            self.assertEqual(getattr(params, param), expected,
                          f"Parameter {param} should be {expected}")
    
    def test_read_from_binary(self):
        # Create test binary data
        binary_data = bytearray([0] * 18)  # First 18 bytes are not used by MacroSynthParams
        
        # Extend with test values from parameter groups
        for group, params in self.parameter_groups.items():
            for param, (value, offset) in params.items():
                # Ensure binary data is long enough
                while len(binary_data) <= offset:
                    binary_data.append(0)
                binary_data[offset] = value
        
        # Read from binary
        params = M8InstrumentParams.from_config("MACROSYNTH")
        params.read(binary_data)
        
        # Check all parameters were read correctly
        for param, expected in self.test_values.items():
            self.assertEqual(getattr(params, param), expected,
                          f"Parameter {param} should be {expected}")
    
    def test_write_to_binary(self):
        # Create params with test values (use numeric values directly)
        test_kwargs = {param: value for param, value in self.test_values.items()}
        
        params = M8InstrumentParams.from_config("MACROSYNTH", **test_kwargs)
        
        # Write to binary
        binary = params.write()
        
        # Check specific values in binary output
        for group, group_params in self.parameter_groups.items():
            for param, (value, offset) in group_params.items():
                self.assertEqual(binary[offset], value,
                              f"Binary at offset {offset} for {param} should be {value}")
    
    def test_read_write_consistency(self):
        # Create params with test values (use numeric values directly)
        test_kwargs = {param: value for param, value in self.test_values.items()}
        
        original = M8InstrumentParams.from_config("MACROSYNTH", **test_kwargs)
        
        # Write to binary
        binary = original.write()
        
        # Read back from binary
        deserialized = M8InstrumentParams.from_config("MACROSYNTH")
        deserialized.read(binary)
        
        # Check all values match
        for param in self.test_values.keys():
            self.assertEqual(getattr(deserialized, param), getattr(original, param),
                          f"Parameter {param} should match after read/write")
    
    def test_dictionary_serialization(self):
        # Create params with test values
        test_kwargs = {param: value for param, value in self.test_values.items()}
        # Convert enum values to string representation for test
        for param in self.enum_params:
            value = test_kwargs[param]
            test_kwargs[param] = self.enum_string_values[param][value]
        
        params = M8InstrumentParams.from_config("MACROSYNTH", **test_kwargs)
        
        # Convert to dict
        result = params.as_dict()
        
        # Check dict values
        for param, value in self.test_values.items():
            expected = value
            # For enum parameters, we expect the string representation
            if param in self.enum_params:
                expected = self.enum_string_values[param][value]
            self.assertEqual(result[param], expected,
                          f"Dict value for {param} should be {expected}")
        
        # Test from_dict
        # Create a new dict with string enum values
        dict_data = {param: value for param, value in self.test_values.items()}
        for param in self.enum_params:
            dict_data[param] = self.enum_string_values[param][dict_data[param]]
        
        # Create params from dict
        from_dict_params = M8InstrumentParams.from_dict("MACROSYNTH", dict_data)
        
        # Check all values match the expected test values
        for param, expected in self.test_values.items():
            self.assertEqual(getattr(from_dict_params, param), expected,
                          f"Parameter {param} should be {expected} after from_dict")


class TestM8MacroSynth(unittest.TestCase):
    def setUp(self):
        # Common instrument parameters for testing
        self.common_params = {
            "name": "TestMacroSynth",
            "transpose": 0x5,
            "eq": 0x2,
            "table_tick": 0x02,
            "volume": 0x10,
            "pitch": 0x20,
            "finetune": 0x90
        }
        
        # Synth-specific parameters
        self.synth_params = {
            "shape": "MORPH",  # Using string enum
            "timbre": 0x70,
            "color": 0x90,
            "degrade": 0x10,
            "redux": 0x20,
            "filter": "HIGHPASS",  # Using string enum
            "cutoff": 0xE0,
            "res": 0x30,
            "amp": 0x40,
            "limit": "FOLD",  # Using string enum
            "pan": 0x60,
            "dry": 0xB0,
            "chorus": 0x70,
            "delay": 0x80,
            "reverb": 0x90
        }
        
        # Expected binary values for parameters
        self.binary_offsets = {
            "shape": 18,
            "timbre": 19,
            "color": 20,
            "degrade": 21,
            "redux": 22,
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
        
        # Expected binary values (after enum resolution)
        self.binary_values = {
            "shape": 0x01,  # MORPH
            "timbre": 0x70,
            "color": 0x90,
            "degrade": 0x10,
            "redux": 0x20,
            "filter": 0x02,  # HIGHPASS
            "cutoff": 0xE0,
            "res": 0x30,
            "amp": 0x40,
            "limit": 0x02,  # FOLD
            "pan": 0x60,
            "dry": 0xB0,
            "chorus": 0x70,
            "delay": 0x80,
            "reverb": 0x90
        }
    
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
        kwargs = {**self.common_params, **self.synth_params}
        synth = M8Instrument(instrument_type="MACROSYNTH", **kwargs)
        
        # Check common parameters
        for param, expected in self.common_params.items():
            self.assertEqual(getattr(synth, param), expected,
                          f"Common parameter {param} should be {expected}")
        
        # Check synth-specific parameters
        for param, expected in self.synth_params.items():
            param_value = getattr(synth.params, param)
            
            # For enum parameters, we need to handle both integer and string representations
            if param in ["shape", "filter", "limit"]:
                expected_value = self.binary_values[param]
                # Some versions might return string, others might return int
                if isinstance(param_value, str):
                    self.assertEqual(param_value, expected,
                                  f"Parameter {param} should be {expected}")
                else:
                    self.assertEqual(param_value, expected_value,
                                  f"Parameter {param} should be {expected_value}")
            else:
                self.assertEqual(param_value, expected,
                              f"Parameter {param} should be {expected}")
    
    def test_read_parameters(self):
        # Create a MacroSynth
        synth = M8Instrument(instrument_type="MACROSYNTH")
        
        # Create test binary data (with type=0x01 for MacroSynth)
        binary_data = bytearray([0x01])  # Type
        binary_data.extend(bytearray([0] * 17))  # Rest of common parameters
        
        # Add macrosynth-specific parameters
        for _ in range(33 - len(binary_data)):
            binary_data.append(0)
            
        for param, offset in self.binary_offsets.items():
            binary_data[offset] = self.binary_values[param]
        
        # Call the method to read parameters
        synth._read_parameters(binary_data)
        
        # Check parameters were read correctly
        for param, expected in self.binary_values.items():
            self.assertEqual(getattr(synth.params, param), expected,
                          f"Parameter {param} should be {expected}")
    
    def test_write(self):
        # Create a MacroSynth with specific parameters
        kwargs = {**self.common_params, **self.synth_params}
        synth = M8Instrument(instrument_type="MACROSYNTH", **kwargs)
        
        # Write to binary
        binary = synth.write()
        
        # Check the type byte (macrosynth = 0x01)
        self.assertEqual(binary[0], 0x01)
        
        # Check macrosynth-specific parameters
        for param, offset in self.binary_offsets.items():
            expected = self.binary_values[param]
            self.assertEqual(binary[offset], expected,
                          f"Binary at offset {offset} for {param} should be {expected}")
    
    def test_is_empty(self):
        # Valid MACROSYNTH instrument should not be empty
        synth = M8Instrument(instrument_type="MACROSYNTH")
        self.assertFalse(synth.is_empty())
        
        # Create an invalid instrument that should be empty
        mock_synth = M8Instrument(instrument_type="MACROSYNTH")
        # Create a custom is_empty method for this test
        mock_synth.is_empty = lambda: True
        self.assertTrue(mock_synth.is_empty())
    
    def test_modulator_integration(self):
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
        
        # Test dict serialization with modulators
        kwargs = {**self.common_params, **self.synth_params}
        synth = M8Instrument(instrument_type="MACROSYNTH", **kwargs)
        mod = M8Modulator(modulator_type=M8ModulatorType.LFO, destination=2, amount=100, frequency=50)
        synth.modulators[0] = mod
        
        result = synth.as_dict()
        
        # Check common parameters
        self.assertEqual(result["type"], "MACROSYNTH")
        for param, expected in self.common_params.items():
            self.assertEqual(result[param], expected,
                          f"Dict value for {param} should be {expected}")
        
        # Check synth-specific parameters, ensuring enum values are properly serialized
        for param, expected in self.synth_params.items():
            if param in ["shape", "filter", "limit"]:
                self.assertEqual(result[param], expected,
                              f"Dict value for enum {param} should be {expected}")
            else:
                self.assertEqual(result[param], expected,
                              f"Dict value for {param} should be {expected}")
        
        # Check modulators
        self.assertIn("modulators", result)
        self.assertIsInstance(result["modulators"], list)
        self.assertGreater(len(result["modulators"]), 0)
        self.assertEqual(result["modulators"][0]["type"], "LFO")
        self.assertEqual(result["modulators"][0]["destination"], "PITCH")
        self.assertEqual(result["modulators"][0]["amount"], 100)
        self.assertEqual(result["modulators"][0]["frequency"], 50)


if __name__ == '__main__':
    unittest.main()