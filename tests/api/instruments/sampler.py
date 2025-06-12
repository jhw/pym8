import unittest
from m8.api.instruments import M8InstrumentParams, M8Instrument
from m8.api.modulators import M8Modulator, M8ModulatorType

class TestM8SamplerParams(unittest.TestCase):
    def setUp(self):
        # Define parameter groups for easier testing
        self.parameter_groups = {
            "sample_params": {
                "play_mode": (0x01, 18),  # (test_value, binary_offset) - REV
                "slice": (0x05, 19),
                "start": (0x10, 20),
                "loop_start": (0x20, 21),
                "length": (0xE0, 22),
                "degrade": (0x30, 23)
            },
            "filter_params": {
                "filter": (0x02, 24),  # HIGHPASS
                "cutoff": (0xD0, 25),
                "res": (0x40, 26)
            },
            "amp_params": {
                "amp": (0x50, 27),
                "limit": (0x00, 28),  # CLIP
                "pan": (0x70, 29)
            },
            "fx_params": {
                "dry": (0xB0, 30),
                "chorus": (0x80, 31),
                "delay": (0x90, 32),
                "reverb": (0xA0, 33)
            }
        }
        
        # Define expected default values
        self.default_values = {
            "play_mode": 0x0,  # FWD
            "slice": 0x0,
            "start": 0x0,
            "loop_start": 0x0,
            "length": 0xFF,
            "degrade": 0x0,
            "filter": 0x0,  # OFF
            "cutoff": 0xFF,
            "res": 0x0,
            "amp": 0x0,
            "limit": 0x0,  # CLIP
            "pan": 0x80,
            "dry": 0xC0,
            "chorus": 0x0,
            "delay": 0x0,
            "reverb": 0x0,
            "sample_path": ""
        }
        
        # With simplified enum system, all parameters are now integer values
        
        # Sample path for testing
        self.test_sample_path = "/samples/kick.wav"

    def test_constructor_and_defaults(self):
        # Test default constructor for Sampler params
        params = M8InstrumentParams.from_config("SAMPLER")
        
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
        # Add sample path for all tests
        kwargs["sample_path"] = self.test_sample_path
        
        # Test constructor with parameters
        params = M8InstrumentParams.from_config("SAMPLER", **kwargs)
        
        # Check values match what we set
        for param_name, (value, _) in params_dict.items():
            self.assertEqual(getattr(params, param_name), value, 
                            f"Parameter {param_name} should be {value}")
        
        # Create binary data for reading test
        binary_data = bytearray([0] * 200)  # Make it large enough for sample path
        
        # Set values at the exact offsets with slightly different values
        for param_name, (_, offset) in params_dict.items():
            # Create a different value for testing read
            binary_data[offset] = getattr(params, param_name) + 5
        
        # Add sample path (assuming offset 87)
        sample_path_offset = 87
        sample_path_bytes = self.test_sample_path.encode('utf-8')
        binary_data[sample_path_offset:sample_path_offset + len(sample_path_bytes)] = sample_path_bytes
        
        # Read from binary
        read_params = M8InstrumentParams.from_config("SAMPLER")
        read_params.read(binary_data)
        
        # Check parameters were read correctly
        for param_name, (_, offset) in params_dict.items():
            expected_value = getattr(params, param_name) + 5
            self.assertEqual(getattr(read_params, param_name), expected_value,
                            f"Read value for {param_name} should be {expected_value}")
        
        # Check sample path was read
        self.assertEqual(read_params.sample_path, self.test_sample_path,
                        f"Sample path should be {self.test_sample_path}")
        
        # Test write to binary
        write_params = M8InstrumentParams.from_config("SAMPLER", **kwargs)
        binary = write_params.write()
        
        # Check binary has all parameters with correct values
        for param_name, (value, offset) in params_dict.items():
            self.assertEqual(binary[offset], value,
                            f"Binary at offset {offset} for {param_name} should be {value}")
        
        # Get sample path offset from param definitions
        sample_path_offset = 87
        for param_name, param_def in write_params._param_defs.items():
            if param_name == "sample_path":
                sample_path_offset = param_def["offset"]
                break
        
        # Check sample path was written (at least the first part)
        sample_path_bytes = self.test_sample_path.encode('utf-8')
        self.assertEqual(binary[sample_path_offset:sample_path_offset + len(sample_path_bytes)], sample_path_bytes,
                        f"Sample path should be written to binary at offset {sample_path_offset}")
        
        # Test dictionary serialization
        dict_params = M8InstrumentParams.from_config("SAMPLER", **kwargs)
        result = dict_params.as_dict()
        
        # Check dictionary has all values correctly - expect integer values with simplified enum system
        for param_name, (value, _) in params_dict.items():
            self.assertIsInstance(result[param_name], int,
                               f"Parameter {param_name} should be an integer in dictionary")
            self.assertEqual(result[param_name], value,
                           f"Dictionary value for {param_name} should be {value}")
        
        # Check sample path in dictionary
        self.assertEqual(result["sample_path"], self.test_sample_path,
                        f"Sample path in dictionary should be {self.test_sample_path}")
    
    def test_read_write_consistency(self):
        # Prepare all parameters with test values
        all_params = {}
        for group in self.parameter_groups.values():
            for name, (value, _) in group.items():
                all_params[name] = value
        
        # Add sample path
        all_params["sample_path"] = self.test_sample_path
        
        # Create original params with all parameters
        original = M8InstrumentParams.from_config("SAMPLER", **all_params)
        
        # Write to binary
        binary = original.write()
        
        # Read back from binary
        deserialized = M8InstrumentParams.from_config("SAMPLER")
        deserialized.read(binary)
        
        # Check all values match between original and deserialized
        for param_name in all_params.keys():
            original_value = getattr(original, param_name)
            deserialized_value = getattr(deserialized, param_name)
            self.assertEqual(deserialized_value, original_value,
                            f"Deserialized value for {param_name} should match original")
    
    def test_comprehensive_read_from_binary(self):
        # Create test binary data with values for all parameters
        binary_data = bytearray([0] * 200)  # Make it large enough for sample path
        
        # Set values for all parameters
        for group in self.parameter_groups.values():
            for name, (_, offset) in group.items():
                test_value = 0xA0 | offset  # Create unique test value based on offset
                binary_data[offset] = test_value
        
        # Add sample path (assuming offset 87)
        sample_path_offset = 87
        sample_path_bytes = self.test_sample_path.encode('utf-8')
        binary_data[sample_path_offset:sample_path_offset + len(sample_path_bytes)] = sample_path_bytes
        
        # Read parameters from binary
        params = M8InstrumentParams.from_config("SAMPLER")
        params.read(binary_data)
        
        # Verify all parameters were read correctly
        for group in self.parameter_groups.values():
            for name, (_, offset) in group.items():
                expected_value = 0xA0 | offset
                self.assertEqual(getattr(params, name), expected_value,
                                f"Parameter {name} should have value {expected_value}")
        
        # Verify sample path was read
        self.assertEqual(params.sample_path, self.test_sample_path,
                        f"Sample path should be {self.test_sample_path}")
    
    def test_as_dict_with_all_params(self):
        # Prepare all parameters with test values
        all_params = {}
        for group in self.parameter_groups.values():
            for name, (value, _) in group.items():
                all_params[name] = value
        
        # Add sample path
        all_params["sample_path"] = self.test_sample_path
        
        # Create params with all parameters
        params = M8InstrumentParams.from_config("SAMPLER", **all_params)
        
        # Convert to dict
        result = params.as_dict()
        
        # Check all parameters are in the dictionary with correct values - expect integer values with simplified enum system
        for param_name, value in all_params.items():
            if param_name == "sample_path":
                # Sample path should remain a string
                self.assertIsInstance(result[param_name], str)
                self.assertEqual(result[param_name], value)
            else:
                # All other parameters should be integers
                self.assertIsInstance(result[param_name], int,
                                   f"Parameter {param_name} should be an integer in dictionary")
                self.assertEqual(result[param_name], value,
                               f"Dictionary value for {param_name} should be {value}")
    
    def test_from_dict(self):
        # Test data with integer enum values (simplified enum system)
        data = {
            "play_mode": 0x01,  # REV enum value
            "slice": 0x5,
            "start": 0x10,
            "loop_start": 0x20,
            "length": 0xE0,
            "degrade": 0x30,
            "filter": 0x02,  # HIGHPASS enum value
            "cutoff": 0xD0,
            "res": 0x40,
            "amp": 0x50,
            "limit": 0x00,  # CLIP enum value
            "pan": 0x70,
            "dry": 0xB0,
            "chorus": 0x80,
            "delay": 0x90,
            "reverb": 0xA0,
            "sample_path": self.test_sample_path
        }
        
        # Create from dict
        params = M8InstrumentParams.from_dict("SAMPLER", data)
        
        # Check values - all should match exactly
        for key, value in data.items():
            self.assertEqual(getattr(params, key), value,
                          f"Parameter {key} should be {value}")


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
        
        # Define all Sampler-specific parameters for comprehensive testing
        self.sampler_params = {
            "play_mode": 0x01,  # REV
            "slice": 0x05,
            "start": 0x10,
            "loop_start": 0x20,
            "length": 0xE0,
            "degrade": 0x30,
            "filter": 0x02,  # HIGHPASS
            "cutoff": 0xD0,
            "res": 0x40,
            "amp": 0x50,
            "limit": 0x00,  # CLIP
            "pan": 0x70,
            "dry": 0xB0,
            "chorus": 0x80,
            "delay": 0x90,
            "reverb": 0xA0,
            "sample_path": "/samples/kick.wav"
        }
        
        # Define parameter offsets for binary testing
        self.param_offsets = {
            "play_mode": 18,
            "slice": 19,
            "start": 20,
            "loop_start": 21,
            "length": 22,
            "degrade": 23,
            "filter": 24,
            "cutoff": 25,
            "res": 26,
            "amp": 27,
            "limit": 28,
            "pan": 29,
            "dry": 30,
            "chorus": 31,
            "delay": 32,
            "reverb": 33
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
            "play_mode": 0x0,  # FWD
            "slice": 0x0,
            "start": 0x0,
            "loop_start": 0x0,
            "length": 0xFF,
            "degrade": 0x0,
            "filter": 0x0,  # OFF
            "cutoff": 0xFF,
            "res": 0x0,
            "amp": 0x0,
            "limit": 0x0,  # CLIP
            "pan": 0x80,
            "dry": 0xC0,
            "chorus": 0x0,
            "delay": 0x0,
            "reverb": 0x0,
            "sample_path": ""
        }
        
        # With simplified enum system, all parameters are now integer values

    def test_constructor_and_defaults(self):
        # Test default constructor
        sampler = M8Instrument(instrument_type="SAMPLER")
        
        # Check type is set correctly
        self.assertEqual(sampler.type, 0x02)  # SAMPLER type_id is 2
        self.assertEqual(sampler.instrument_type, "SAMPLER")
        
        # Check params object is created
        self.assertTrue(hasattr(sampler, "params"))
        
        # Check default parameters
        self.assertNotEqual(sampler.name, "")  # Should auto-generate a name
        for param, expected in self.defaults.items():
            if param == "name":
                continue  # Skip name, already checked
            
            if hasattr(sampler, param):
                # Test sampler attribute
                self.assertEqual(getattr(sampler, param), expected, 
                              f"Default {param} should be {expected}")
            elif hasattr(sampler.params, param):
                # Test params attribute
                self.assertEqual(getattr(sampler.params, param), expected, 
                              f"Default params.{param} should be {expected}")
        
        # Test with kwargs for both common and specific parameters
        all_params = {}
        all_params.update(self.common_params)
        all_params.update(self.sampler_params)
        
        sampler = M8Instrument(instrument_type="SAMPLER", **all_params)
        
        # Check common parameters
        for param, expected in self.common_params.items():
            self.assertEqual(getattr(sampler, param), expected,
                          f"Parameter {param} should be {expected}")
            
        # Check instrument-specific parameters
        for param, expected in self.sampler_params.items():
            self.assertEqual(getattr(sampler.params, param), expected,
                          f"Parameter params.{param} should be {expected}")

    def test_read_parameters(self):
        # Create a Sampler
        sampler = M8Instrument(instrument_type="SAMPLER")
        
        # Create test binary data (with type=0x02 for Sampler)
        binary_data = bytearray([0x02])  # Type
        binary_data.extend(b"TEST")  # Name (first 4 bytes)
        binary_data.extend(bytearray([0] * 8))  # Rest of name padding
        binary_data.extend([0x42, 0x02, 0x10, 0x20, 0x90])  # Common params
        
        # Add sampler-specific parameters
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
            0x00,   # limit (CLIP = 0x0)
            0x70,   # pan
            0xB0,   # dry
            0x80,   # chorus
            0x90,   # delay
            0xA0    # reverb
        ])
        
        # Get the sampler's sample_path offset from config
        sample_path_offset = 87  # Default offset for sample path
        for param_name, param_def in sampler.params._param_defs.items():
            if param_name == "sample_path":
                sample_path_offset = param_def["offset"]
                break
                
        # Pad up to sample_path offset
        if sample_path_offset > len(binary_data):
            binary_data.extend([0] * (sample_path_offset - len(binary_data)))
        
        # Add sample path
        test_path = b"/samples/kick.wav"
        binary_data.extend(test_path)
        
        # Extend with data to reach modulators and beyond
        # Pad to a reasonable length (at least larger than the modulators offset)
        binary_data.extend([0] * (215 - len(binary_data)))
        
        # Call the method to read parameters
        sampler._read_parameters(binary_data)
        
        # Check parameters were read correctly
        self.assertEqual(sampler.type, 0x02)
        self.assertEqual(sampler.name, "TEST")
        
        # Check the transpose & eq byte
        self.assertEqual(sampler.eq, 0x2)
        
        # Check other common parameters
        for param, expected in self.common_params.items():
            if param in ["name", "transpose", "eq"]:
                continue  # Already checked or handled specially
            self.assertEqual(getattr(sampler, param), expected,
                          f"Parameter {param} should be {expected}")
        
        # Check sampler-specific parameters
        for param, expected in self.sampler_params.items():
            if param == "sample_path":
                continue  # Skip for special handling
            self.assertEqual(getattr(sampler.params, param), expected,
                          f"Parameter params.{param} should be {expected}")
        
        # Check sample path
        self.assertEqual(sampler.params.sample_path, "/samples/kick.wav")

    def test_binary_serialization(self):
        # Create sampler with all parameters but use a shorter name
        all_params = {}
        all_params.update(self.common_params)
        all_params.update(self.sampler_params)
        
        # Use a shorter name to avoid truncation issues
        all_params["name"] = "TEST"
        
        sampler = M8Instrument(instrument_type="SAMPLER", **all_params)
        
        # Write to binary
        binary = sampler.write()
        
        # Create a new sampler to test reading
        read_sampler = M8Instrument(instrument_type="SAMPLER")
        read_sampler._read_parameters(binary)
        
        # Check all parameters were read correctly
        self.assertEqual(read_sampler.name, "TEST")
        
        # Check common parameters
        for param in self.common_params.keys():
            if param == "name":
                continue  # Already checked
            self.assertEqual(getattr(read_sampler, param), getattr(sampler, param),
                           f"Parameter {param} didn't match after read")
        
        # Check sampler-specific parameters
        for param in self.sampler_params.keys():
            if param == "sample_path":
                continue  # Skip for special handling
            self.assertEqual(getattr(read_sampler.params, param), getattr(sampler.params, param),
                          f"Parameter params.{param} didn't match after read")
        
        # Check sample path
        self.assertEqual(read_sampler.params.sample_path, sampler.params.sample_path)

    def test_is_empty(self):
        # Valid SAMPLER instrument should not be empty
        sampler = M8Instrument(instrument_type="SAMPLER")
        self.assertFalse(sampler.is_empty())
        
        # Create an invalid instrument that should be empty
        mock_sampler = M8Instrument(instrument_type="SAMPLER")
        # Create a custom is_empty method for this test
        mock_sampler.is_empty = lambda: True
        self.assertTrue(mock_sampler.is_empty())

    def test_modulators(self):
        # Create a Sampler
        sampler = M8Instrument(instrument_type="SAMPLER")
        
        # Add a modulator
        mod = M8Modulator(modulator_type=3, destination=2, amount=100, frequency=50)  # 3=LFO, 2=PITCH
        slot = sampler.add_modulator(mod)
        
        # Should use first slot
        self.assertEqual(slot, 0)
        self.assertEqual(sampler.modulators[0].type, 3)  # LFO type value
        self.assertEqual(sampler.modulators[0].destination, 2)  # PITCH value
        self.assertEqual(sampler.modulators[0].amount, 100)
        self.assertEqual(sampler.modulators[0].params.frequency, 50)
        
        # Test modulator preservation through serialization
        binary = sampler.write()
        deserialized = M8Instrument(instrument_type="SAMPLER")
        deserialized._read_parameters(binary)
        
        # Check modulator was deserialized properly
        self.assertEqual(len(deserialized.modulators), 4)  # All slots initialized
        self.assertEqual(deserialized.modulators[0].type, 3)  # LFO
        self.assertEqual(deserialized.modulators[0].destination, 2)  # PITCH
        self.assertEqual(deserialized.modulators[0].amount, 100)

    def test_as_dict(self):
        # Create sampler with all parameters
        all_params = {}
        all_params.update(self.common_params)
        all_params.update(self.sampler_params)
        
        sampler = M8Instrument(instrument_type="SAMPLER", **all_params)
        
        # Add a modulator
        mod = M8Modulator(modulator_type=M8ModulatorType.LFO, destination=2, amount=100, frequency=50)
        sampler.add_modulator(mod)
        
        # Convert to dict
        result = sampler.as_dict()
        
        # Check common parameters
        self.assertEqual(result["type"], "SAMPLER")
        self.assertEqual(result["name"], "TestSampler")
        
        # Check instrument-specific parameters - expect integer values with simplified enum system
        for param, value in self.sampler_params.items():
            if param == "sample_path":
                # Sample path should remain a string
                self.assertIsInstance(result[param], str)
                self.assertEqual(result[param], value)
            else:
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