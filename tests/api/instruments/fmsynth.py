import unittest
from m8.api.instruments import M8InstrumentParams, M8Instrument, create_instrument
from m8.api.instruments.fmsynth import M8FMSynth, FMOperator
from m8.api.modulators import M8Modulator, M8ModulatorType
from m8.api.instruments import create_instrument_from_dict

class TestM8FMSynthParams(unittest.TestCase):
    def setUp(self):
        # Define parameter groups for easier testing
        self.parameter_groups = {
            "algorithm": {
                "algo": (0x02, 18),  # (test_value, binary_offset)
            },
            "operator1": {
                "shape1": (0x06, 19),  # TRI
                "ratio1": (0x08, 23),
                "level1": (0xF0, 31),
                "feedback1": (0x10, 32)
            },
            "operator2": {
                "shape2": (0x07, 20),  # SAW
                "ratio2": (0x04, 25),
                "level2": (0xE0, 33),
                "feedback2": (0x20, 34)
            },
            "operator3": {
                "shape3": (0x08, 21),  # SQR
                "ratio3": (0x02, 27),
                "level3": (0xD0, 35),
                "feedback3": (0x30, 36)
            },
            "operator4": {
                "shape4": (0x09, 22),  # PUL
                "ratio4": (0x01, 29),
                "level4": (0xC0, 37),
                "feedback4": (0x40, 38)
            },
            "filter_params": {
                "filter": (0x02, 51),  # HIGHPASS
                "cutoff": (0xE0, 52),
                "res": (0x30, 53)
            },
            "amp_params": {
                "amp": (0x40, 54),
                "limit": (0x01, 55),  # SIN
                "pan": (0x60, 56)
            },
            "fx_params": {
                "dry": (0xB0, 57),
                "chorus": (0x70, 58),
                "delay": (0x80, 59),
                "reverb": (0x90, 60)
            }
        }
        
        # Define expected default values
        self.default_values = {
            "algo": 0x0,  # A_B_C_D
            "shape1": 0x0,  # SIN
            "shape2": 0x0,  # SIN
            "shape3": 0x0,  # SIN
            "shape4": 0x0,  # SIN
            "ratio1": 0,
            "ratio2": 0,
            "ratio3": 0,
            "ratio4": 0,
            "level1": 0x0,
            "level2": 0x0,
            "level3": 0x0,
            "level4": 0x0,
            "feedback1": 0x0,
            "feedback2": 0x0,
            "feedback3": 0x0,
            "feedback4": 0x0,
            "filter": 0x0,  # OFF
            "cutoff": 0xFF,
            "res": 0x0,
            "amp": 0x0,
            "limit": 0x0,  # CLIP = 0
            "pan": 0x80,
            "dry": 0xC0,
            "chorus": 0x0,
            "delay": 0x0,
            "reverb": 0x0
        }
        
        # With simplified enum system, all parameters are now integer values

    def test_constructor_and_defaults(self):
        # Test default constructor for FMSynth params
        params = M8InstrumentParams.from_config("FMSYNTH")
        
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
        params = M8InstrumentParams.from_config("FMSYNTH", **kwargs)
        
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
        read_params = M8InstrumentParams.from_config("FMSYNTH")
        read_params.read(binary_data)
        
        # Check parameters were read correctly
        for param_name, (_, offset) in params_dict.items():
            expected_value = getattr(params, param_name) + 5
            self.assertEqual(getattr(read_params, param_name), expected_value,
                            f"Read value for {param_name} should be {expected_value}")
        
        # Test write to binary
        write_params = M8InstrumentParams.from_config("FMSYNTH", **kwargs)
        binary = write_params.write()
        
        # Check binary has all parameters with correct values
        for param_name, (value, offset) in params_dict.items():
            self.assertEqual(binary[offset], value,
                            f"Binary at offset {offset} for {param_name} should be {value}")
        
        # Test dictionary serialization
        dict_params = M8InstrumentParams.from_config("FMSYNTH", **kwargs)
        result = dict_params.as_dict()
        
        # Check dictionary has all values correctly
        for param_name, (value, _) in params_dict.items():
            # With simplified enum system, all values are now integers
            self.assertEqual(result[param_name], value,
                           f"Dictionary value for {param_name} should be {value}")
    
    def test_read_write_consistency(self):
        # Prepare all parameters with test values
        all_params = {}
        for group in self.parameter_groups.values():
            for name, (value, _) in group.items():
                all_params[name] = value
        
        # Create original params with all parameters
        original = M8InstrumentParams.from_config("FMSYNTH", **all_params)
        
        # Write to binary
        binary = original.write()
        
        # Read back from binary
        deserialized = M8InstrumentParams.from_config("FMSYNTH")
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
        params = M8InstrumentParams.from_config("FMSYNTH")
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
        params = M8InstrumentParams.from_config("FMSYNTH", **all_params)
        
        # Convert to dict
        result = params.as_dict()
        
        # Check all parameters are in the dictionary with correct values
        for param_name, value in all_params.items():
            # With simplified enum system, all values are integers
            self.assertEqual(result[param_name], value,
                           f"Dictionary value for {param_name} should be {value}")


class TestFMOperator(unittest.TestCase):
    def setUp(self):
        # Define standard test values for operators
        self.test_values = {
            "shape": 0x06,  # TRI
            "ratio": 0x08,
            "level": 0xF0,
            "feedback": 0x10,
            "mod_a": 0x01,
            "mod_b": 0x02
        }

    def test_constructor_and_defaults(self):
        # Test default constructor
        op = FMOperator()
        
        # Check defaults
        self.assertEqual(op.shape, 0)
        self.assertEqual(op.ratio, 0)
        self.assertEqual(op.level, 0)
        self.assertEqual(op.feedback, 0)
        self.assertEqual(op.mod_a, 0)
        self.assertEqual(op.mod_b, 0)
        
        # Test with custom values
        op = FMOperator(**self.test_values)
        
        # Check values
        for param, value in self.test_values.items():
            self.assertEqual(getattr(op, param), value,
                          f"Parameter {param} should be {value}")
    
    def test_as_dict(self):
        # Create operator with specific values
        op = FMOperator(**self.test_values)
        
        # Convert to dict
        result = op.as_dict()
        
        # Check values
        for param, value in self.test_values.items():
            self.assertEqual(result[param], value,
                         f"Dictionary value for {param} should be {value}")
    
    def test_from_dict(self):
        # Create from dict
        op = FMOperator.from_dict(self.test_values)
        
        # Check values
        for param, value in self.test_values.items():
            self.assertEqual(getattr(op, param), value,
                          f"Parameter {param} should be {value}")


class TestM8FMSynthInstrument(unittest.TestCase):
    def setUp(self):
        # Define common instrument parameters
        self.common_params = {
            "name": "TestFMSynth",
            "transpose": 0x5,
            "eq": 0x2,
            "table_tick": 0x2,
            "volume": 0x10,
            "pitch": 0x20,
            "finetune": 0x90
        }
        
        # Define all FMSynth-specific parameters for comprehensive testing
        self.fmsynth_params = {
            "algo": 0x02,  # A_B_PLUS_C_D = 0x02
            "shape1": 0x06,  # TRI
            "shape2": 0x07,  # SAW
            "shape3": 0x08,  # SQR
            "shape4": 0x09,  # PUL
            "ratio1": 0x08,
            "ratio2": 0x09,
            "ratio3": 0x0A,
            "ratio4": 0x0B,
            "level1": 0xF0,
            "level2": 0xE0,
            "level3": 0xD0,
            "level4": 0xC0,
            "feedback1": 0x10,
            "feedback2": 0x20,
            "feedback3": 0x30,
            "feedback4": 0x40,
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
        
        # Define test values for operators (for testing operators property)
        self.operator_test_values = [
            {"shape": 0x06, "ratio": 0x08, "level": 0xF0, "feedback": 0x10},
            {"shape": 0x07, "ratio": 0x09, "level": 0xE0, "feedback": 0x20},
            {"shape": 0x08, "ratio": 0x0A, "level": 0xD0, "feedback": 0x30},
            {"shape": 0x09, "ratio": 0x0B, "level": 0xC0, "feedback": 0x40}
        ]
        
        # Define expected default values
        self.defaults = {
            "name": "",  # Auto-generated, should not be empty
            "transpose": 0x4,
            "eq": 0x1,
            "table_tick": 0x01,
            "volume": 0x0,
            "pitch": 0x0,
            "finetune": 0x80,
            "algo": 0x0,  # A_B_C_D
            "shape1": 0x0,  # SIN
            "shape2": 0x0,  # SIN
            "shape3": 0x0,  # SIN
            "shape4": 0x0,  # SIN
            "ratio1": 0,
            "ratio2": 0,
            "ratio3": 0,
            "ratio4": 0,
            "level1": 0x0,
            "level2": 0x0,
            "level3": 0x0,
            "level4": 0x0,
            "feedback1": 0x0,
            "feedback2": 0x0,
            "feedback3": 0x0,
            "feedback4": 0x0,
            "filter": 0x0,  # OFF
            "cutoff": 0xFF,
            "res": 0x0,
            "amp": 0x0,
            "limit": 0x0,  # CLIP = 0
            "pan": 0x80,
            "dry": 0xC0,
            "chorus": 0x0,
            "delay": 0x0,
            "reverb": 0x0
        }
        
        # With simplified enum system, all parameters are now integer values
        
        # Create operators list that matches the test values
        self.test_operators = [
            FMOperator(**self.operator_test_values[0]),
            FMOperator(**self.operator_test_values[1]),
            FMOperator(**self.operator_test_values[2]),
            FMOperator(**self.operator_test_values[3])
        ]
        
        # This dict maps operator values to parameter names for easier testing
        self.operator_to_param_mapping = [
            {"shape": "shape1", "ratio": "ratio1", "level": "level1", "feedback": "feedback1"},
            {"shape": "shape2", "ratio": "ratio2", "level": "level2", "feedback": "feedback2"},
            {"shape": "shape3", "ratio": "ratio3", "level": "level3", "feedback": "feedback3"},
            {"shape": "shape4", "ratio": "ratio4", "level": "level4", "feedback": "feedback4"}
        ]

    def test_constructor_and_defaults(self):
        # Test default constructor
        synth = M8FMSynth()
        
        # Check type is set correctly
        self.assertEqual(synth.type, 0x04)  # FMSYNTH type_id is 4
        self.assertEqual(synth.instrument_type, "FMSYNTH")
        
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
        
        # Check operators were created
        self.assertEqual(len(synth.operators), 4)
        
        # Test with kwargs for both common and specific parameters
        all_params = {}
        all_params.update(self.common_params)
        all_params.update(self.fmsynth_params)
        
        synth = M8FMSynth(**all_params)
        
        # Check common parameters
        for param, expected in self.common_params.items():
            self.assertEqual(getattr(synth, param), expected,
                          f"Parameter {param} should be {expected}")
            
        # Check instrument-specific parameters
        for param, expected in self.fmsynth_params.items():
            self.assertEqual(getattr(synth.params, param), expected,
                          f"Parameter params.{param} should be {expected}")

    def test_constructor_with_operators(self):
        # Create synth with operators
        synth = M8FMSynth(operators=self.test_operators, algo=0x02)
        
        # Check algorithm parameter
        self.assertEqual(synth.params.algo, 0x02)
        
        # Check operators were mapped to underlying params
        for i, op in enumerate(self.test_operators):
            op_mapping = self.operator_to_param_mapping[i]
            for op_attr, param_name in op_mapping.items():
                self.assertEqual(getattr(synth.params, param_name), getattr(op, op_attr),
                              f"Parameter params.{param_name} should be {getattr(op, op_attr)}")

    def test_operators_property(self):
        # Create synth with specific params using raw values from fmsynth_params
        synth = M8FMSynth(**self.fmsynth_params)
        
        # Get operators
        operators = synth.operators
        
        # Check operators were mapped from params
        self.assertEqual(len(operators), 4)
        
        # Check operator values match the params
        for i, op in enumerate(operators):
            op_mapping = self.operator_to_param_mapping[i]
            for op_attr, param_name in op_mapping.items():
                self.assertEqual(getattr(op, op_attr), getattr(synth.params, param_name),
                              f"Operator {i}.{op_attr} should be {getattr(synth.params, param_name)}")
        
        # Test setting operators
        new_operators = [
            FMOperator(shape=0x01, ratio=0x01, level=0x11, feedback=0x21),
            FMOperator(shape=0x02, ratio=0x02, level=0x12, feedback=0x22),
            FMOperator(shape=0x03, ratio=0x03, level=0x13, feedback=0x23),
            FMOperator(shape=0x04, ratio=0x04, level=0x14, feedback=0x24)
        ]
        
        synth.operators = new_operators
        
        # Check params were updated
        for i, op in enumerate(new_operators):
            op_mapping = self.operator_to_param_mapping[i]
            for op_attr, param_name in op_mapping.items():
                self.assertEqual(getattr(synth.params, param_name), getattr(op, op_attr),
                              f"Parameter params.{param_name} should be {getattr(op, op_attr)}")

    def test_from_dict(self):
        # Test creating from dict with operators
        data = {
            "type": "FMSYNTH",
            "name": "TestFMSynth",
            "algo": 2,  # A_B_PLUS_C_D = 0x02
            "operators": self.operator_test_values
        }
        
        # Create from dict
        synth = M8FMSynth.from_dict(data)
        
        # Check type
        self.assertEqual(synth.instrument_type, "FMSYNTH")
        self.assertEqual(synth.type, 0x04)
        
        # Check it's the right class
        self.assertIsInstance(synth, M8FMSynth)
        
        # Check parameters
        self.assertEqual(synth.name, "TestFMSynth")
        self.assertEqual(synth.params.algo, 0x02)
        
        # Check operators
        operators = synth.operators
        self.assertEqual(len(operators), 4)
        
        # Check operator values match the test values
        for i, op in enumerate(operators):
            for param, value in self.operator_test_values[i].items():
                self.assertEqual(getattr(op, param), value,
                              f"Operator {i}.{param} should be {value}")

    def test_as_dict(self):
        # Create synth with operators
        synth = M8FMSynth(
            name="TestFMSynth",
            operators=self.test_operators,
            algo=0x02,  # A_B_PLUS_C_D
            filter=0x02,  # HIGHPASS
            cutoff=0xE0,
            res=0x30
        )
        
        # Convert to dict
        result = synth.as_dict()
        
        # Check common parameters
        self.assertEqual(result["type"], "FMSYNTH")
        self.assertEqual(result["name"], "TestFMSynth")
        self.assertEqual(result["algo"], 0x02)  # A_B_PLUS_C_D enum value
        self.assertEqual(result["filter"], 0x02)  # HIGHPASS enum value
        self.assertEqual(result["cutoff"], 0xE0)
        self.assertEqual(result["res"], 0x30)
        
        # Check operators
        self.assertIn("operators", result)
        self.assertEqual(len(result["operators"]), 4)
        
        # Check operator values in the dictionary
        for i, op in enumerate(self.test_operators):
            for param, value in self.operator_test_values[i].items():
                # With simplified enum system, shape is now an integer enum value
                self.assertEqual(result["operators"][i][param], value,
                               f"Operator {i}.{param} should be {value}")

    def test_binary_serialization(self):
        # Create synth with all parameters but use a shorter name
        all_params = {}
        all_params.update(self.common_params)
        all_params.update(self.fmsynth_params)
        
        # Use a shorter name to avoid truncation issues
        all_params["name"] = "TEST"
        
        synth = M8FMSynth(**all_params)
        
        # Write to binary
        binary = synth.write()
        
        # Create a new synth to test reading
        read_synth = M8FMSynth()
        read_synth._read_parameters(binary)
        
        # Check all parameters were read correctly
        self.assertEqual(read_synth.name, "TEST")
        for param in self.common_params.keys():
            if param == "name":
                continue  # Already checked
            self.assertEqual(getattr(read_synth, param), getattr(synth, param),
                           f"Parameter {param} didn't match after read")
        
        for param in self.fmsynth_params.keys():
            self.assertEqual(getattr(read_synth.params, param), getattr(synth.params, param),
                          f"Parameter params.{param} didn't match after read")

    def test_modulators(self):
        # Create a FMSynth
        synth = M8FMSynth()
        
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
        deserialized = M8FMSynth()
        deserialized._read_parameters(binary)
        
        # Check modulator was deserialized properly
        self.assertEqual(len(deserialized.modulators), 4)  # All slots initialized
        self.assertEqual(deserialized.modulators[0].type, 3)  # LFO
        self.assertEqual(deserialized.modulators[0].destination, 2)  # PITCH
        self.assertEqual(deserialized.modulators[0].amount, 100)

    def test_create_instrument_factory(self):
        # Test that the factory creates the right subclass
        synth = create_instrument("FMSYNTH")
        self.assertIsInstance(synth, M8FMSynth)
        
        # Test with dictionary data
        data = {
            "type": "FMSYNTH",
            "name": "TestFMSynth"
        }
        
        synth = create_instrument_from_dict(data)
        self.assertIsInstance(synth, M8FMSynth)

    def test_read_write_consistency(self):
        # Create operators
        original = M8FMSynth(
            name="TestFMSynth",
            operators=self.test_operators,
            algo=0x02  # A_B_PLUS_C_D
        )
        
        # Add a modulator
        mod = M8Modulator(modulator_type=3, destination=2, amount=100, frequency=50)  # 3=LFO, 2=PITCH
        original.add_modulator(mod)
        
        # Write to binary
        binary = original.write()
        
        # Create a new instance and read the binary
        deserialized = M8FMSynth()
        deserialized._read_parameters(binary)
        
        # Check values match
        self.assertEqual(deserialized.name, original.name)
        self.assertEqual(deserialized.params.algo, original.params.algo)
        
        # Check operators
        for i in range(4):
            for attr in ["shape", "ratio", "level", "feedback"]:
                self.assertEqual(getattr(deserialized.operators[i], attr), 
                               getattr(original.operators[i], attr),
                              f"Operator {i}.{attr} didn't match after deserialization")
        
        # Check modulator
        self.assertEqual(len(deserialized.modulators), 4)  # All slots initialized
        self.assertEqual(deserialized.modulators[0].type, 3)  # LFO
        self.assertEqual(deserialized.modulators[0].destination, 2)  # PITCH
        self.assertEqual(deserialized.modulators[0].amount, 100)


if __name__ == '__main__':
    unittest.main()