import unittest
from m8.api.instruments import M8InstrumentParams, M8Instrument, create_instrument
from m8.api.instruments.fmsynth import M8FMSynth, FMOperator
from m8.api.modulators import M8Modulator, M8ModulatorType

class TestM8FMSynthParams(unittest.TestCase):
    def test_constructor_and_defaults(self):
        # Test default constructor for FMSynth params
        params = M8InstrumentParams.from_config("FMSYNTH")
        
        # Check defaults for key parameters
        self.assertEqual(params.algo, 0x0)  # A_B_C_D
        self.assertEqual(params.shape1, 0x0)  # SIN
        self.assertEqual(params.ratio1, 0x0)
        self.assertEqual(params.level1, 0x0)
        self.assertEqual(params.feedback1, 0x0)
        self.assertEqual(params.filter, 0x0)
        self.assertEqual(params.cutoff, 0xFF)
        self.assertEqual(params.res, 0x0)
        self.assertEqual(params.amp, 0x0)
        self.assertEqual(params.limit, 0x0)  # CLIP = 0
        self.assertEqual(params.pan, 0x80)
        self.assertEqual(params.dry, 0xC0)
        self.assertEqual(params.chorus, 0x0)
        self.assertEqual(params.delay, 0x0)
        self.assertEqual(params.reverb, 0x0)
        
        # Test with kwargs
        params = M8InstrumentParams.from_config("FMSYNTH",
            algo=0x02,  # A_B_PLUS_C_D
            shape1=0x06,  # TRI
            shape2=0x07,  # SAW
            shape3=0x08,  # SQR
            shape4=0x09,  # PUL
            ratio1=0x08,
            ratio2=0x04,
            ratio3=0x02,
            ratio4=0x01,
            level1=0xF0,
            level2=0xE0,
            level3=0xD0,
            level4=0xC0,
            feedback1=0x10,
            feedback2=0x20,
            feedback3=0x30,
            feedback4=0x40,
            filter=0x02,  # HIGHPASS
            cutoff=0xE0,
            res=0x30,
            amp=0x40,
            limit=0x01,  # FOLD
            pan=0x60,
            dry=0xB0,
            chorus=0x70,
            delay=0x80,
            reverb=0x90
        )
        
        # Check values
        self.assertEqual(params.algo, 0x02)
        self.assertEqual(params.shape1, 0x06)
        self.assertEqual(params.ratio1, 0x08)
        self.assertEqual(params.level1, 0xF0)
        self.assertEqual(params.feedback1, 0x10)
        self.assertEqual(params.filter, 0x02)
        self.assertEqual(params.cutoff, 0xE0)
        self.assertEqual(params.res, 0x30)
        self.assertEqual(params.amp, 0x40)
        self.assertEqual(params.limit, 0x01)
        self.assertEqual(params.pan, 0x60)
        self.assertEqual(params.dry, 0xB0)
        self.assertEqual(params.chorus, 0x70)
        self.assertEqual(params.delay, 0x80)
        self.assertEqual(params.reverb, 0x90)
    
    def test_read_from_binary(self):
        # Create test binary data with key parameters
        binary_data = bytearray([0] * 100)  # Create a buffer large enough
        
        # Set values at the exact offsets from the YAML config
        binary_data[18] = 0x02  # algo (offset 18)
        binary_data[19] = 0x06  # shape1 (offset 19)
        binary_data[23] = 0x08  # ratio1 (offset 23)
        binary_data[31] = 0xF0  # level1 (offset 31)
        binary_data[32] = 0x10  # feedback1 (offset 32)
        binary_data[51] = 0x02  # filter (offset 51)
        binary_data[52] = 0xE0  # cutoff (offset 52)
        binary_data[60] = 0x90  # reverb (offset 60)
        
        # Create params and read from binary
        params = M8InstrumentParams.from_config("FMSYNTH")
        params.read(binary_data)
        
        # Check key parameter values
        self.assertEqual(params.algo, 0x02)
        self.assertEqual(params.shape1, 0x06)
        self.assertEqual(params.ratio1, 0x08)
        self.assertEqual(params.level1, 0xF0)
        self.assertEqual(params.feedback1, 0x10)
        self.assertEqual(params.filter, 0x02)
        self.assertEqual(params.cutoff, 0xE0)
        self.assertEqual(params.reverb, 0x90)
    
    def test_write_to_binary(self):
        # Create params with specific values
        params = M8InstrumentParams.from_config("FMSYNTH",
            algo=0x02,
            shape1=0x06,
            ratio1=0x08,
            level1=0xF0,
            feedback1=0x10,
            filter=0x02,
            cutoff=0xE0,
            reverb=0x90
        )
        
        # Write to binary
        binary = params.write()
        
        # Check binary has sufficient size
        min_size = 61  # Should at least include up to reverb at offset 60
        self.assertGreaterEqual(len(binary), min_size)
        
        # Check key parameters
        self.assertEqual(binary[18], 0x02)  # algo
        self.assertEqual(binary[19], 0x06)  # shape1
        self.assertEqual(binary[23], 0x08)  # ratio1
        self.assertEqual(binary[31], 0xF0)  # level1
        self.assertEqual(binary[32], 0x10)  # feedback1
        self.assertEqual(binary[51], 0x02)  # filter
        self.assertEqual(binary[52], 0xE0)  # cutoff
        self.assertEqual(binary[60], 0x90)  # reverb
    
    def test_read_write_consistency(self):
        # Create original params
        original = M8InstrumentParams.from_config("FMSYNTH",
            algo=0x02,
            shape1=0x06,
            shape2=0x07,
            ratio1=0x08,
            ratio2=0x04,
            level1=0xF0,
            level2=0xE0,
            feedback1=0x10,
            feedback2=0x20,
            filter=0x02,
            cutoff=0xE0,
            res=0x30,
            amp=0x40,
            limit=0x01,
            pan=0x60,
            dry=0xB0,
            chorus=0x70,
            delay=0x80,
            reverb=0x90
        )
        
        # Write to binary
        binary = original.write()
        
        # Read back from binary
        deserialized = M8InstrumentParams.from_config("FMSYNTH")
        deserialized.read(binary)
        
        # Check values match
        self.assertEqual(deserialized.algo, original.algo)
        self.assertEqual(deserialized.shape1, original.shape1)
        self.assertEqual(deserialized.ratio1, original.ratio1)
        self.assertEqual(deserialized.level1, original.level1)
        self.assertEqual(deserialized.feedback1, original.feedback1)
        self.assertEqual(deserialized.filter, original.filter)
        self.assertEqual(deserialized.cutoff, original.cutoff)
        self.assertEqual(deserialized.reverb, original.reverb)
    
    def test_as_dict(self):
        # Create params
        params = M8InstrumentParams.from_config("FMSYNTH",
            algo=0x02,  # A_B_PLUS_C_D
            shape1=0x06,  # TRI
            ratio1=0x08,
            level1=0xF0,
            feedback1=0x10,
            filter=0x02,  # HIGHPASS
            cutoff=0xE0,
            limit=0x01,  # FOLD
            reverb=0x90
        )
        
        # Convert to dict
        result = params.as_dict()
        
        # Check non-enum values
        self.assertEqual(result["ratio1"], 0x08)
        self.assertEqual(result["level1"], 0xF0)
        self.assertEqual(result["feedback1"], 0x10)
        self.assertEqual(result["cutoff"], 0xE0)
        self.assertEqual(result["reverb"], 0x90)
        
        # Check enum values are strings
        self.assertIsInstance(result["algo"], str)
        self.assertIsInstance(result["shape1"], str)
        self.assertIsInstance(result["filter"], str)
        self.assertIsInstance(result["limit"], str)


class TestFMOperator(unittest.TestCase):
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
        op = FMOperator(
            shape=0x06,  # TRI
            ratio=0x08,
            level=0xF0,
            feedback=0x10,
            mod_a=0x01,
            mod_b=0x02
        )
        
        # Check values
        self.assertEqual(op.shape, 0x06)
        self.assertEqual(op.ratio, 0x08)
        self.assertEqual(op.level, 0xF0)
        self.assertEqual(op.feedback, 0x10)
        self.assertEqual(op.mod_a, 0x01)
        self.assertEqual(op.mod_b, 0x02)
    
    def test_as_dict(self):
        # Create operator with specific values
        op = FMOperator(
            shape=0x06,  # TRI
            ratio=0x08,
            level=0xF0,
            feedback=0x10,
            mod_a=0x01,
            mod_b=0x02
        )
        
        # Convert to dict
        result = op.as_dict()
        
        # Check values
        self.assertEqual(result["shape"], 0x06)
        self.assertEqual(result["ratio"], 0x08)
        self.assertEqual(result["level"], 0xF0)
        self.assertEqual(result["feedback"], 0x10)
        self.assertEqual(result["mod_a"], 0x01)
        self.assertEqual(result["mod_b"], 0x02)
    
    def test_from_dict(self):
        # Create test data
        data = {
            "shape": 0x06,  # TRI
            "ratio": 0x08,
            "level": 0xF0,
            "feedback": 0x10,
            "mod_a": 0x01,
            "mod_b": 0x02
        }
        
        # Create from dict
        op = FMOperator.from_dict(data)
        
        # Check values
        self.assertEqual(op.shape, 0x06)
        self.assertEqual(op.ratio, 0x08)
        self.assertEqual(op.level, 0xF0)
        self.assertEqual(op.feedback, 0x10)
        self.assertEqual(op.mod_a, 0x01)
        self.assertEqual(op.mod_b, 0x02)


class TestM8FMSynthInstrument(unittest.TestCase):
    def test_constructor_and_defaults(self):
        # Test default constructor
        synth = M8FMSynth()
        
        # Check type is set correctly
        self.assertEqual(synth.type, 0x04)  # FMSYNTH type_id is 4
        self.assertEqual(synth.instrument_type, "FMSYNTH")
        
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
        
        # Check operators were created
        self.assertEqual(len(synth.operators), 4)
        
        # Test with kwargs for common parameters
        synth = M8FMSynth(
            # Common instrument parameters
            name="TestFMSynth",
            transpose=0x5,
            eq=0x2,
            table_tick=0x02,
            volume=0x10,
            pitch=0x20,
            finetune=0x90,
            algo=0x02  # A_B_PLUS_C_D = 0x02
        )
        
        # Check common parameters
        self.assertEqual(synth.name, "TestFMSynth")
        self.assertEqual(synth.transpose, 0x5)
        self.assertEqual(synth.eq, 0x2)
        self.assertEqual(synth.table_tick, 0x02)
        self.assertEqual(synth.volume, 0x10)
        self.assertEqual(synth.pitch, 0x20)
        self.assertEqual(synth.finetune, 0x90)
        
        # Check algorithm parameter
        self.assertEqual(synth.params.algo, 0x02)
    
    def test_constructor_with_operators(self):
        # Create operators
        operators = [
            FMOperator(shape=0x06, ratio=0x08, level=0xF0, feedback=0x10),
            FMOperator(shape=0x07, ratio=0x09, level=0xE0, feedback=0x20),
            FMOperator(shape=0x08, ratio=0x0A, level=0xD0, feedback=0x30),
            FMOperator(shape=0x09, ratio=0x0B, level=0xC0, feedback=0x40)
        ]
        
        # Create synth with operators
        synth = M8FMSynth(operators=operators, algo=0x02)
        
        # Check common parameters
        self.assertEqual(synth.params.algo, 0x02)
        
        # Check operators were mapped to underlying params
        self.assertEqual(synth.params.shape1, 0x06)
        self.assertEqual(synth.params.ratio1, 0x08)
        self.assertEqual(synth.params.level1, 0xF0)
        self.assertEqual(synth.params.feedback1, 0x10)
        
        self.assertEqual(synth.params.shape2, 0x07)
        self.assertEqual(synth.params.ratio2, 0x09)
        self.assertEqual(synth.params.level2, 0xE0)
        self.assertEqual(synth.params.feedback2, 0x20)
        
        self.assertEqual(synth.params.shape3, 0x08)
        self.assertEqual(synth.params.ratio3, 0x0A)
        self.assertEqual(synth.params.level3, 0xD0)
        self.assertEqual(synth.params.feedback3, 0x30)
        
        self.assertEqual(synth.params.shape4, 0x09)
        self.assertEqual(synth.params.ratio4, 0x0B)
        self.assertEqual(synth.params.level4, 0xC0)
        self.assertEqual(synth.params.feedback4, 0x40)
    
    def test_operators_property(self):
        # Create synth with specific params using raw values
        synth = M8FMSynth(
            shape1=0x06, ratio1=0x08, level1=0xF0, feedback1=0x10,
            shape2=0x07, ratio2=0x09, level2=0xE0, feedback2=0x20,
            shape3=0x08, ratio3=0x0A, level3=0xD0, feedback3=0x30,
            shape4=0x09, ratio4=0x0B, level4=0xC0, feedback4=0x40
        )
        
        # Get parameters to check initial values
        self.assertEqual(synth.params.shape1, 0x06)
        self.assertEqual(synth.params.ratio1, 0x08)
        self.assertEqual(synth.params.level1, 0xF0)
        self.assertEqual(synth.params.feedback1, 0x10)
        
        # Get operators
        operators = synth.operators
        
        # Check operators were mapped from params
        self.assertEqual(len(operators), 4)
        
        # Testing the exact type of returned values is less important than
        # making sure they can round-trip correctly
        
        # Test setting operators
        new_operators = [
            FMOperator(shape=0x01, ratio=0x01, level=0x11, feedback=0x21),
            FMOperator(shape=0x02, ratio=0x02, level=0x12, feedback=0x22),
            FMOperator(shape=0x03, ratio=0x03, level=0x13, feedback=0x23),
            FMOperator(shape=0x04, ratio=0x04, level=0x14, feedback=0x24)
        ]
        
        synth.operators = new_operators
        
        # Check params were updated
        self.assertEqual(synth.params.shape1, 0x01)
        self.assertEqual(synth.params.ratio1, 0x01)
        self.assertEqual(synth.params.level1, 0x11)
        self.assertEqual(synth.params.feedback1, 0x21)
        
        self.assertEqual(synth.params.shape2, 0x02)
        self.assertEqual(synth.params.ratio2, 0x02)
        self.assertEqual(synth.params.level2, 0x12)
        self.assertEqual(synth.params.feedback2, 0x22)
        
        self.assertEqual(synth.params.shape3, 0x03)
        self.assertEqual(synth.params.ratio3, 0x03)
        self.assertEqual(synth.params.level3, 0x13)
        self.assertEqual(synth.params.feedback3, 0x23)
        
        self.assertEqual(synth.params.shape4, 0x04)
        self.assertEqual(synth.params.ratio4, 0x04)
        self.assertEqual(synth.params.level4, 0x14)
        self.assertEqual(synth.params.feedback4, 0x24)
    
    def test_from_dict(self):
        # Test creating from dict with operators
        data = {
            "type": "FMSYNTH",
            "name": "TestFMSynth",
            "algo": 2,  # A_B_PLUS_C_D = 0x02
            "operators": [
                {"shape": 0x06, "ratio": 0x08, "level": 0xF0, "feedback": 0x10},
                {"shape": 0x07, "ratio": 0x09, "level": 0xE0, "feedback": 0x20},
                {"shape": 0x08, "ratio": 0x0A, "level": 0xD0, "feedback": 0x30},
                {"shape": 0x09, "ratio": 0x0B, "level": 0xC0, "feedback": 0x40}
            ]
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
        
        self.assertEqual(operators[0].shape, 0x06)
        self.assertEqual(operators[0].ratio, 0x08)
        self.assertEqual(operators[0].level, 0xF0)
        self.assertEqual(operators[0].feedback, 0x10)
        
        self.assertEqual(operators[1].shape, 0x07)
        self.assertEqual(operators[1].ratio, 0x09)
        self.assertEqual(operators[1].level, 0xE0)
        self.assertEqual(operators[1].feedback, 0x20)
        
        self.assertEqual(operators[2].shape, 0x08)
        self.assertEqual(operators[2].ratio, 0x0A)
        self.assertEqual(operators[2].level, 0xD0)
        self.assertEqual(operators[2].feedback, 0x30)
        
        self.assertEqual(operators[3].shape, 0x09)
        self.assertEqual(operators[3].ratio, 0x0B)
        self.assertEqual(operators[3].level, 0xC0)
        self.assertEqual(operators[3].feedback, 0x40)
    
    def test_as_dict(self):
        # Create operators
        operators = [
            FMOperator(shape=0x06, ratio=0x08, level=0xF0, feedback=0x10),
            FMOperator(shape=0x07, ratio=0x09, level=0xE0, feedback=0x20),
            FMOperator(shape=0x08, ratio=0x0A, level=0xD0, feedback=0x30),
            FMOperator(shape=0x09, ratio=0x0B, level=0xC0, feedback=0x40)
        ]
        
        # Create synth with operators
        synth = M8FMSynth(
            name="TestFMSynth",
            operators=operators,
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
        self.assertEqual(result["algo"], "A_B_PLUS_C_D")
        self.assertEqual(result["filter"], "HIGHPASS")
        self.assertEqual(result["cutoff"], 0xE0)
        self.assertEqual(result["res"], 0x30)
        
        # Check operators
        self.assertIn("operators", result)
        self.assertEqual(len(result["operators"]), 4)
        
        # In the dictionary, operators have serialized enum values as strings
        self.assertEqual(result["operators"][0]["shape"], "TRI")
        self.assertEqual(result["operators"][0]["ratio"], 0x08)
        self.assertEqual(result["operators"][0]["level"], 0xF0)
        self.assertEqual(result["operators"][0]["feedback"], 0x10)
        
        self.assertEqual(result["operators"][1]["shape"], "SAW")
        self.assertEqual(result["operators"][1]["ratio"], 0x09)
        self.assertEqual(result["operators"][1]["level"], 0xE0)
        self.assertEqual(result["operators"][1]["feedback"], 0x20)
    
    def test_read_parameters(self):
        # Create a FMSynth
        synth = M8FMSynth()
        
        # Create test binary data
        binary_data = bytearray([
            0x04,   # type (FMSynth)
            0x54, 0x45, 0x53, 0x54, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # name "TEST"
            0x42,   # transpose/eq (4/2)
            0x02,   # table_tick
            0x10,   # volume
            0x20,   # pitch
            0x90,   # finetune
            0x02,   # algo
            0x06,   # shape1
            0x07,   # shape2
            0x08,   # shape3
            0x09,   # shape4
            0x08,   # ratio1
            0x00,   # ratio_fine1
            0x09,   # ratio2
            0x00,   # ratio_fine2
            0x0A,   # ratio3
            0x00,   # ratio_fine3
            0x0B,   # ratio4
            0x00,   # ratio_fine4
            0xF0,   # level1
            0x10,   # feedback1
            0xE0,   # level2
            0x20,   # feedback2
            0xD0,   # level3
            0x30,   # feedback3
            0xC0,   # level4
            0x40    # feedback4
        ])
        
        # Add additional parameter bytes
        binary_data.extend([0] * (63 - len(binary_data)))  # Fill up to modulator offset
        binary_data.extend([0] * 24)  # Four empty modulators (6 bytes each)
        
        # Call the method to read parameters
        synth._read_parameters(binary_data)
        
        # Check common parameters
        self.assertEqual(synth.type, 0x04)
        self.assertEqual(synth.name, "TEST")
        self.assertEqual(synth.transpose, 0x4)
        self.assertEqual(synth.eq, 0x2)
        self.assertEqual(synth.table_tick, 0x02)
        self.assertEqual(synth.volume, 0x10)
        self.assertEqual(synth.pitch, 0x20)
        self.assertEqual(synth.finetune, 0x90)
        
        # Check algorithm
        self.assertEqual(synth.params.algo, 0x02)
        
        # Check operators were created and mapped correctly
        operators = synth.operators
        self.assertEqual(len(operators), 4)
        
        self.assertEqual(operators[0].shape, 0x06)
        self.assertEqual(operators[0].ratio, 0x08)
        self.assertEqual(operators[0].level, 0xF0)
        self.assertEqual(operators[0].feedback, 0x10)
        
        self.assertEqual(operators[1].shape, 0x07)
        self.assertEqual(operators[1].ratio, 0x09)
        self.assertEqual(operators[1].level, 0xE0)
        self.assertEqual(operators[1].feedback, 0x20)
        
        self.assertEqual(operators[2].shape, 0x08)
        self.assertEqual(operators[2].ratio, 0x0A)
        self.assertEqual(operators[2].level, 0xD0)
        self.assertEqual(operators[2].feedback, 0x30)
        
        self.assertEqual(operators[3].shape, 0x09)
        self.assertEqual(operators[3].ratio, 0x0B)
        self.assertEqual(operators[3].level, 0xC0)
        self.assertEqual(operators[3].feedback, 0x40)
    
    def test_write(self):
        # Create operators
        operators = [
            FMOperator(shape=0x06, ratio=0x08, level=0xF0, feedback=0x10),
            FMOperator(shape=0x07, ratio=0x09, level=0xE0, feedback=0x20),
            FMOperator(shape=0x08, ratio=0x0A, level=0xD0, feedback=0x30),
            FMOperator(shape=0x09, ratio=0x0B, level=0xC0, feedback=0x40)
        ]
        
        # Create synth with operators
        synth = M8FMSynth(
            name="TEST",
            operators=operators,
            algo=0x02,  # A_B_PLUS_C_D
            transpose=0x4,
            eq=0x2,
            table_tick=0x02,
            volume=0x10,
            pitch=0x20,
            finetune=0x90
        )
        
        # Call the method to write
        binary = synth.write()
        
        # Check the binary output
        self.assertEqual(len(binary), 215)  # Should be BLOCK_SIZE bytes
        
        # Check common parameters
        self.assertEqual(binary[0], 0x04)  # type
        self.assertEqual(binary[1:5], b"TEST")  # name (first 4 bytes)
        self.assertEqual(binary[13], 0x42)  # transpose/eq
        self.assertEqual(binary[14], 0x02)  # table_tick
        self.assertEqual(binary[15], 0x10)  # volume
        self.assertEqual(binary[16], 0x20)  # pitch
        self.assertEqual(binary[17], 0x90)  # finetune
        
        # Check algorithm
        self.assertEqual(binary[18], 0x02)  # algo
        
        # Check operator parameters
        self.assertEqual(binary[19], 0x06)  # shape1
        self.assertEqual(binary[20], 0x07)  # shape2
        self.assertEqual(binary[21], 0x08)  # shape3
        self.assertEqual(binary[22], 0x09)  # shape4
        
        self.assertEqual(binary[23], 0x08)  # ratio1
        self.assertEqual(binary[25], 0x09)  # ratio2
        self.assertEqual(binary[27], 0x0A)  # ratio3
        self.assertEqual(binary[29], 0x0B)  # ratio4
        
        self.assertEqual(binary[31], 0xF0)  # level1
        self.assertEqual(binary[32], 0x10)  # feedback1
        self.assertEqual(binary[33], 0xE0)  # level2
        self.assertEqual(binary[34], 0x20)  # feedback2
        self.assertEqual(binary[35], 0xD0)  # level3
        self.assertEqual(binary[36], 0x30)  # feedback3
        self.assertEqual(binary[37], 0xC0)  # level4
        self.assertEqual(binary[38], 0x40)  # feedback4
    
    def test_add_modulator(self):
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
    
    def test_create_instrument_factory(self):
        # Test that the factory creates the right subclass
        synth = create_instrument("FMSYNTH")
        self.assertIsInstance(synth, M8FMSynth)
        
        # For dictionaries we need to use create_instrument_from_dict, not directly create_instrument
        from m8.api.instruments import create_instrument_from_dict
        
        # Test with dictionary data
        data = {
            "type": "FMSYNTH",
            "name": "TestFMSynth"
        }
        
        synth = create_instrument_from_dict(data)
        self.assertIsInstance(synth, M8FMSynth)
    
    def test_read_write_consistency(self):
        # Create operators
        operators = [
            FMOperator(shape=0x06, ratio=0x08, level=0xF0, feedback=0x10),
            FMOperator(shape=0x07, ratio=0x09, level=0xE0, feedback=0x20),
            FMOperator(shape=0x08, ratio=0x0A, level=0xD0, feedback=0x30),
            FMOperator(shape=0x09, ratio=0x0B, level=0xC0, feedback=0x40)
        ]
        
        # Create original synth with operators
        original = M8FMSynth(
            name="TestFMSynth",
            operators=operators,
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
            self.assertEqual(deserialized.operators[i].shape, original.operators[i].shape)
            self.assertEqual(deserialized.operators[i].ratio, original.operators[i].ratio)
            self.assertEqual(deserialized.operators[i].level, original.operators[i].level)
            self.assertEqual(deserialized.operators[i].feedback, original.operators[i].feedback)
        
        # Check modulator
        self.assertEqual(len(deserialized.modulators), 4)  # All slots initialized
        self.assertEqual(deserialized.modulators[0].type, 3)  # LFO
        self.assertEqual(deserialized.modulators[0].destination, 2)  # PITCH
        self.assertEqual(deserialized.modulators[0].amount, 100)


if __name__ == '__main__':
    unittest.main()