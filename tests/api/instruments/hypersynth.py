import unittest
from m8.api.instruments import M8InstrumentParams, M8Instrument
from m8.api.instruments.hypersynth import M8HyperSynth
from m8.api.modulators import M8Modulator, M8ModulatorType

class TestM8HyperSynthParams(unittest.TestCase):
    def setUp(self):
        # Define parameter groups for easier testing
        self.parameter_groups = {
            "chord_scale": {
                "chord": (0x10, 18),  # (test_value, binary_offset)
                "scale": (0x20, 25)
            },
            "notes": {
                "note1": (0x31, 19),
                "note2": (0x32, 20),
                "note3": (0x33, 21),
                "note4": (0x34, 22),
                "note5": (0x35, 23),
                "note6": (0x36, 24)
            },
            "synth_params": {
                "shift": (0x41, 26),
                "swarm": (0x42, 27),
                "width": (0x43, 28),
                "subosc": (0x44, 29)
            },
            "filter_params": {
                "filter": (0x02, 30),  # HIGHPASS
                "cutoff": (0xE0, 31),
                "res": (0x30, 32)
            },
            "amp_params": {
                "amp": (0x40, 33),
                "limit": (0x01, 34),  # SIN
                "pan": (0x60, 35)
            },
            "fx_params": {
                "dry": (0xB0, 36),
                "chorus": (0x70, 37),
                "delay": (0x80, 38),
                "reverb": (0x90, 39)
            }
        }
        
        # Define expected default values
        self.default_values = {
            "filter": 0x0,  # OFF
            "cutoff": 0xFF,
            "res": 0x0,
            "amp": 0x0,
            "limit": 0x0,  # CLIP = 0
            "pan": 0x80,
            "dry": 0xC0,
            "chorus": 0x0,
            "delay": 0x0, 
            "reverb": 0x0,
            "shift": 0x0,
            "swarm": 0x0,
            "width": 0x0, 
            "subosc": 0x0,
            "chord": 0x0,
            "scale": 0x0,
            "note1": 0x0,
            "note2": 0x0,
            "note3": 0x0,
            "note4": 0x0,
            "note5": 0x0,
            "note6": 0x0
        }

    def test_constructor_and_defaults(self):
        # Test default constructor for HyperSynth params
        params = M8InstrumentParams.from_config("HYPERSYNTH")
        
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
        params = M8InstrumentParams.from_config("HYPERSYNTH", **kwargs)
        
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
        read_params = M8InstrumentParams.from_config("HYPERSYNTH")
        read_params.read(binary_data)
        
        # Check parameters were read correctly
        for param_name, (_, offset) in params_dict.items():
            expected_value = getattr(params, param_name) + 5
            self.assertEqual(getattr(read_params, param_name), expected_value,
                            f"Read value for {param_name} should be {expected_value}")
        
        # Test write to binary
        write_params = M8InstrumentParams.from_config("HYPERSYNTH", **kwargs)
        binary = write_params.write()
        
        # Check binary has all parameters with correct values
        for param_name, (value, offset) in params_dict.items():
            self.assertEqual(binary[offset], value,
                            f"Binary at offset {offset} for {param_name} should be {value}")
        
        # Test dictionary serialization
        dict_params = M8InstrumentParams.from_config("HYPERSYNTH", **kwargs)
        result = dict_params.as_dict()
        
        # Check dictionary has all values correctly
        for param_name, (value, _) in params_dict.items():
            # Enum values are serialized as strings in dictionaries
            if param_name == "filter" and value == 0x2:
                self.assertEqual(result[param_name], "HIGHPASS",
                               f"Dictionary value for {param_name} should be 'HIGHPASS'")
            elif param_name == "limit" and value == 0x1:
                self.assertEqual(result[param_name], "SIN",
                               f"Dictionary value for {param_name} should be 'SIN'")
            else:
                self.assertEqual(result[param_name], value,
                               f"Dictionary value for {param_name} should be {value}")
    
    def test_read_write_consistency(self):
        # Prepare all parameters with test values
        all_params = {}
        for group in self.parameter_groups.values():
            for name, (value, _) in group.items():
                all_params[name] = value
        
        # Create original params with all parameters
        original = M8InstrumentParams.from_config("HYPERSYNTH", **all_params)
        
        # Write to binary
        binary = original.write()
        
        # Read back from binary
        deserialized = M8InstrumentParams.from_config("HYPERSYNTH")
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
        params = M8InstrumentParams.from_config("HYPERSYNTH")
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
        params = M8InstrumentParams.from_config("HYPERSYNTH", **all_params)
        
        # Convert to dict
        result = params.as_dict()
        
        # Check all parameters are in the dictionary with correct values
        for param_name, value in all_params.items():
            if param_name in ["filter", "limit"]:
                # Check enum values are strings
                self.assertIsInstance(result[param_name], str,
                                    f"Parameter {param_name} should be a string in dictionary")
            else:
                # Check other values match what we set
                self.assertEqual(result[param_name], value,
                                f"Dictionary value for {param_name} should be {value}")

    def test_write_to_binary_with_all_params(self):
        # Prepare all parameters with test values
        all_params = {}
        for group in self.parameter_groups.values():
            for name, (value, _) in group.items():
                all_params[name] = value
        
        # Create params with all parameters
        params = M8InstrumentParams.from_config("HYPERSYNTH", **all_params)
        
        # Write to binary
        binary = params.write()
        
        # Check binary has sufficient size
        min_size = 40  # Should at least include up to reverb at offset 39
        self.assertGreaterEqual(len(binary), min_size)
        
        # Check all parameters were written correctly
        for group in self.parameter_groups.values():
            for name, (value, offset) in group.items():
                self.assertEqual(binary[offset], value,
                                f"Binary at offset {offset} for {name} should be {value}")


class TestM8HyperSynthInstrument(unittest.TestCase):
    def setUp(self):
        # Define common instrument parameters
        self.common_params = {
            "name": "TestHyperSynth",
            "transpose": 0x5,
            "eq": 0x2,
            "table_tick": 0x2,
            "volume": 0x10,
            "pitch": 0x20,
            "finetune": 0x90
        }
        
        # Define all HyperSynth-specific parameters for comprehensive testing
        self.hypersynth_params = {
            "chord": 0x0C,
            "note1": 0x11,
            "note2": 0x22,
            "note3": 0x33,
            "note4": 0x44,
            "note5": 0x55,
            "note6": 0x66,
            "scale": 0x0D,
            "shift": 0x41,
            "swarm": 0x42,
            "width": 0x43,
            "subosc": 0x44,
            "filter": 0x02,  # HIGHPASS
            "cutoff": 0xE0,
            "res": 0x30,
            "amp": 0x40,
            "limit": 0x01,  # SIN
            "pan": 0x60,
            "dry": 0xB0,
            "chorus": 0x70,
            "delay": 0x80,
            "reverb": 0x90
        }
        
        # Define parameter offsets for binary testing
        self.param_offsets = {
            "chord": 18,
            "note1": 19,
            "note2": 20,
            "note3": 21,
            "note4": 22,
            "note5": 23,
            "note6": 24,
            "scale": 25,
            "shift": 26,
            "swarm": 27,
            "width": 28,
            "subosc": 29,
            "filter": 30,
            "cutoff": 31,
            "res": 32,
            "amp": 33,
            "limit": 34,
            "pan": 35,
            "dry": 36,
            "chorus": 37,
            "delay": 38,
            "reverb": 39
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
            "filter": 0x0,  # OFF
            "cutoff": 0xFF,
            "res": 0x0,
            "amp": 0x0,
            "limit": 0x0,  # CLIP = 0
            "pan": 0x80,
            "dry": 0xC0,
            "chorus": 0x0,
            "delay": 0x0,
            "reverb": 0x0,
            "shift": 0x0,
            "swarm": 0x0,
            "width": 0x0,
            "subosc": 0x0,
            "chord": 0x0,
            "scale": 0x0,
            "note1": 0x0,
            "note2": 0x0,
            "note3": 0x0,
            "note4": 0x0,
            "note5": 0x0,
            "note6": 0x0
        }
        
        # For dict serialization testing
        self.enum_params = ["filter", "limit"]

    def test_constructor_and_defaults(self):
        # Test default constructor
        synth = M8HyperSynth()
        
        # Check type is set correctly
        self.assertEqual(synth.type, 0x05)  # HYPERSYNTH type_id is 5
        self.assertEqual(synth.instrument_type, "HYPERSYNTH")
        
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
        all_params.update(self.hypersynth_params)
        
        synth = M8HyperSynth(**all_params)
        
        # Check common parameters
        for param, expected in self.common_params.items():
            self.assertEqual(getattr(synth, param), expected,
                          f"Parameter {param} should be {expected}")
            
        # Check instrument-specific parameters
        for param, expected in self.hypersynth_params.items():
            self.assertEqual(getattr(synth.params, param), expected,
                          f"Parameter params.{param} should be {expected}")
    
    def test_from_dict(self):
        # Test creating from dict
        data = {"type": "HYPERSYNTH"}
        data.update(self.common_params)
        
        # Add the HyperSynth-specific parameters
        data.update(self.hypersynth_params)
        
        # Convert enum values to strings for the test
        data["filter"] = "HIGHPASS"
        data["limit"] = "SIN"
        
        # Create from dict
        synth = M8HyperSynth.from_dict(data)
        
        # Check type
        self.assertEqual(synth.instrument_type, "HYPERSYNTH")
        self.assertEqual(synth.type, 0x05)
        
        # Check it's the right class
        self.assertIsInstance(synth, M8HyperSynth)
        
        # Check common parameters
        for param, expected in self.common_params.items():
            self.assertEqual(getattr(synth, param), expected,
                          f"Parameter {param} should be {expected}")
        
        # Check hypersynth parameters (replacing the string enums with numeric values)
        expected_params = dict(self.hypersynth_params)
        for param, expected in expected_params.items():
            self.assertEqual(getattr(synth.params, param), expected,
                          f"Parameter params.{param} should be {expected}")
    
    def test_as_dict(self):
        # Create synth with all parameters
        all_params = {}
        all_params.update(self.common_params)
        all_params.update(self.hypersynth_params)
        
        synth = M8HyperSynth(**all_params)
        
        # Convert to dict
        result = synth.as_dict()
        
        # Check type and name
        self.assertEqual(result["type"], "HYPERSYNTH")
        self.assertEqual(result["name"], self.common_params["name"])
        
        # Check all parameters are in the dictionary with correct values
        for param, expected in all_params.items():
            if param in self.enum_params:
                # Check enum values are strings
                self.assertIsInstance(result[param], str,
                                   f"Parameter {param} should be a string in dictionary")
                if param == "filter":
                    self.assertEqual(result[param], "HIGHPASS")
                elif param == "limit":
                    self.assertEqual(result[param], "SIN")
            else:
                # Check other values match what we set
                self.assertEqual(result[param], expected,
                              f"Dictionary value for {param} should be {expected}")
    
    def test_binary_serialization(self):
        # Create synth with all parameters but use a shorter name
        all_params = {}
        all_params.update(self.common_params)
        all_params.update(self.hypersynth_params)
        
        # Use a shorter name to avoid truncation issues
        all_params["name"] = "TEST"
        
        synth = M8HyperSynth(**all_params)
        
        # Write to binary
        binary = synth.write()
        
        # Create a new synth to test reading
        read_synth = M8HyperSynth()
        read_synth._read_parameters(binary)
        
        # Check all parameters were read correctly
        self.assertEqual(read_synth.name, "TEST")
        for param in self.common_params.keys():
            if param == "name":
                continue  # Already checked
            self.assertEqual(getattr(read_synth, param), getattr(synth, param),
                           f"Parameter {param} didn't match after read")
        
        for param in self.hypersynth_params.keys():
            self.assertEqual(getattr(read_synth.params, param), getattr(synth.params, param),
                          f"Parameter params.{param} didn't match after read")
    
    def test_modulators(self):
        # Create a HyperSynth
        synth = M8HyperSynth()
        
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
        deserialized = M8HyperSynth()
        deserialized._read_parameters(binary)
        
        # Check modulator was deserialized properly
        self.assertEqual(len(deserialized.modulators), 4)  # All slots initialized
        self.assertEqual(deserialized.modulators[0].type, 3)  # LFO
        self.assertEqual(deserialized.modulators[0].destination, 2)  # PITCH
        self.assertEqual(deserialized.modulators[0].amount, 100)


if __name__ == '__main__':
    unittest.main()