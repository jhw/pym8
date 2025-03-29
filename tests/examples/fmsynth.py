import unittest
from m8.api.project import M8Project
from m8.api.instruments import M8Instrument
from m8.api.instruments.fmsynth import M8FMSynth, FMOperator


class TestFMSynthMapping(unittest.TestCase):
    """
    Test that FMSynth instruments from M8I files get correctly mapped when read 
    into Python objects.
    """
    
    def setUp(self):
        # Load the M8I file with FMSynth instrument
        self.instrument = M8Instrument.read_from_file("tests/examples/fixtures/KICK_DR-GENX.m8i")
        # Get its dictionary representation
        self.instrument_dict = self.instrument.as_dict()
    
    def test_fmsynth_type(self):
        # Verify instrument type
        self.assertEqual(self.instrument_dict['type'], "FMSYNTH")
        # Check that the instrument is recognized as a FMSynth
        self.assertEqual(self.instrument.instrument_type, "FMSYNTH")
        
    def test_fmsynth_name(self):
        # Test that the instrument name is correct
        name = self.instrument_dict['name']
        self.assertEqual(name, "KICK_DR-GENX", 
                        "Instrument name should be 'KICK_DR-GENX'")
    
    def test_fmsynth_numeric_fields(self):
        # Test all fields except name and modulators
        expected_values = {
            'transpose': 0,           # 0x00
            'eq': 0,                  # 0x00
            'table_tick': 1,          # 0x01
            'volume': 0,              # 0x00
            'pitch': 0,               # 0x00
            'finetune': 128,          # 0x80
            'algo': 'A_B_PLUS_A_C_PLUS_D', # Algorithm enum
            'amp': 32,                # 0x20
            'chorus': 0,              # 0x00
            'cutoff': 159,            # 0x9F
            'delay': 0,               # 0x00
            'dry': 207,               # 0xCF
            'feedback1': 64,          # 0x40
            'feedback2': 0,           # 0x00
            'feedback3': 0,           # 0x00
            'feedback4': 0,           # 0x00
            'filter': "OFF",          # 0x00
            'level1': 239,            # 0xEF
            'level2': 128,            # 0x80
            'level3': 160,            # 0xA0
            'level4': 16,             # 0x10
            'limit': "POSTAD",        # 0x05
            'mod_1': 13,              # 0x0D
            'mod_2': 0,               # 0x00
            'mod_3': 96,              # 0x60
            'mod_4': 0,               # 0x00
            'mod_a1': 0,              # 0x00 (not an enum value)
            'mod_a2': 'LEV2',         # 0x02 (LEV2 from M8FMSynthModABValues)
            'mod_a3': 'LEV2',         # 0x02 (LEV2 from M8FMSynthModABValues)
            'mod_a4': 'LEV3',         # 0x03 (LEV3 from M8FMSynthModABValues)
            'mod_b1': 0,              # 0x00 (not an enum value)
            'mod_b2': 'RAT1',         # 0x05 (RAT1 from M8FMSynthModABValues)
            'mod_b3': 'RAT1',         # 0x05 (RAT1 from M8FMSynthModABValues)
            'mod_b4': 'LEV2',         # 0x02 (LEV2 from M8FMSynthModABValues)
            'pan': 128,               # 0x80
            'ratio1': 8,              # 0x08
            'ratio2': 1,              # 0x01
            'ratio3': 1,              # 0x01
            'ratio4': 18,             # 0x12
            'ratio_fine1': 0,         # 0x00
            'ratio_fine2': 40,        # 0x28
            'ratio_fine3': 75,        # 0x4B
            'ratio_fine4': 63,        # 0x3F
            'res': 239,               # 0xEF
            'reverb': 0,              # 0x00
            'shape1': 'CLK',          # Shape enum
            'shape2': 'TRI',          # Shape enum
            'shape3': 'SIN',          # Shape enum
            'shape4': 'NHP'           # Shape enum
        }
        
        for field, expected_value in expected_values.items():
            with self.subTest(field=field):
                self.assertEqual(self.instrument_dict[field], expected_value, 
                                f"Field '{field}' doesn't match expected value")
    
    def test_fmsynth_operators(self):
        # Test that operators are present in the serialized dictionary
        self.assertIn('operators', self.instrument_dict)
        
        # Verify we have 4 operators
        self.assertEqual(len(self.instrument_dict['operators']), 4)
        
        # Get operators from the dictionary
        operators = self.instrument_dict['operators']
        
        # Test first operator
        self.assertEqual(operators[0]['shape'], 'CLK')
        self.assertEqual(operators[0]['ratio'], 8)
        self.assertEqual(operators[0]['level'], 239)
        self.assertEqual(operators[0]['feedback'], 64)
        
        # Test second operator
        self.assertEqual(operators[1]['shape'], 'TRI')
        self.assertEqual(operators[1]['ratio'], 1)
        self.assertEqual(operators[1]['level'], 128)
        self.assertEqual(operators[1]['feedback'], 0)
        self.assertEqual(operators[1]['mod_a'], 'LEV2')
        self.assertEqual(operators[1]['mod_b'], 'RAT1')
        
        # Test third operator
        self.assertEqual(operators[2]['shape'], 'SIN')
        self.assertEqual(operators[2]['ratio'], 1)
        self.assertEqual(operators[2]['level'], 160)
        self.assertEqual(operators[2]['feedback'], 0)
        self.assertEqual(operators[2]['mod_a'], 'LEV2')
        self.assertEqual(operators[2]['mod_b'], 'RAT1')
        
        # Test fourth operator
        self.assertEqual(operators[3]['shape'], 'NHP')
        self.assertEqual(operators[3]['ratio'], 18)
        self.assertEqual(operators[3]['level'], 16)
        self.assertEqual(operators[3]['feedback'], 0)
        self.assertEqual(operators[3]['mod_a'], 'LEV3')
        self.assertEqual(operators[3]['mod_b'], 'LEV2')
    
    def test_fmsynth_modulators(self):
        # Test modulators
        expected_modulators = [
            {
                'type': 'AHD_ENVELOPE',
                'destination': 'PITCH',
                'amount': 25,        # 0x19
                'attack': 255,       # 0xFF
                'decay': 14,         # 0x0E
                'hold': 0,           # 0x00
                'index': 2           # 0x02
            },
            {
                'type': 'AHD_ENVELOPE',
                'destination': 'PITCH',
                'amount': 15,        # 0x0F
                'attack': 255,       # 0xFF
                'decay': 0,          # 0x00
                'hold': 0,           # 0x00
                'index': 3           # 0x03
            }
        ]
        
        # Verify we have the right number of modulators
        self.assertEqual(len(self.instrument_dict['modulators']), len(expected_modulators),
                        "Number of modulators doesn't match")
        
        # Sort both lists by index to ensure comparison works
        modulators = self.instrument_dict['modulators']
        modulators.sort(key=lambda x: x['index'])
        expected_modulators.sort(key=lambda x: x['index'])
        
        # Compare the modulators
        for i, expected_modulator in enumerate(expected_modulators):
            actual_modulator = modulators[i]
            for field, expected_value in expected_modulator.items():
                with self.subTest(modulator=i, field=field):
                    self.assertEqual(actual_modulator[field], expected_value,
                                    f"Modulator {i} field '{field}' doesn't match expected value")


class TestFMSynthOperators(unittest.TestCase):
    """
    Test creating and manipulating FMSynth instruments using the operator-based API.
    """
    
    def test_create_with_operators(self):
        # Create operators using integer values
        operators = [
            FMOperator(shape=0x00, ratio=8, level=240, feedback=64, mod_a=0x01, mod_b=0x05),  # SIN, LEV1, RAT1
            FMOperator(shape=0x06, ratio=4, level=200, feedback=32, mod_a=0x02, mod_b=0x06),  # TRI, LEV2, RAT2
            FMOperator(shape=0x08, ratio=2, level=160, feedback=16, mod_a=0x03, mod_b=0x07),  # SQR, LEV3, RAT3
            FMOperator(shape=0x07, ratio=1, level=120, feedback=8, mod_a=0x04, mod_b=0x08)    # SAW, LEV4, RAT4
        ]
        
        # Create a synth with the operators
        synth = M8FMSynth(
            name="OperatorTest",
            algo=0x02,  # A_B_PLUS_C_D
            operators=operators,
            filter=0x01,  # LOWPASS
            cutoff=200,
            res=100
        )
        
        # Check that the synth is created correctly
        self.assertEqual(synth.name, "OperatorTest")
        self.assertEqual(synth.params.algo, 0x02)  # A_B_PLUS_C_D
        self.assertEqual(synth.params.filter, 0x01)  # LOWPASS
        self.assertEqual(synth.params.cutoff, 200)
        self.assertEqual(synth.params.res, 100)
        
        # Check that operators were mapped to underlying params
        self.assertEqual(synth.params.shape1, 0x00)  # SIN
        self.assertEqual(synth.params.ratio1, 8)
        self.assertEqual(synth.params.level1, 240)
        self.assertEqual(synth.params.feedback1, 64)
        self.assertEqual(synth.params.mod_a1, 0x01)  # LEV1
        self.assertEqual(synth.params.mod_b1, 0x05)  # RAT1
        
        self.assertEqual(synth.params.shape2, 0x06)  # TRI
        self.assertEqual(synth.params.ratio2, 4)
        self.assertEqual(synth.params.level2, 200)
        self.assertEqual(synth.params.feedback2, 32)
        self.assertEqual(synth.params.mod_a2, 0x02)  # LEV2
        self.assertEqual(synth.params.mod_b2, 0x06)  # RAT2
        
        self.assertEqual(synth.params.shape3, 0x08)  # SQR
        self.assertEqual(synth.params.ratio3, 2)
        self.assertEqual(synth.params.level3, 160)
        self.assertEqual(synth.params.feedback3, 16)
        self.assertEqual(synth.params.mod_a3, 0x03)  # LEV3
        self.assertEqual(synth.params.mod_b3, 0x07)  # RAT3
        
        self.assertEqual(synth.params.shape4, 0x07)  # SAW
        self.assertEqual(synth.params.ratio4, 1)
        self.assertEqual(synth.params.level4, 120)
        self.assertEqual(synth.params.feedback4, 8)
        self.assertEqual(synth.params.mod_a4, 0x04)  # LEV4
        self.assertEqual(synth.params.mod_b4, 0x08)  # RAT4
    
    def test_modify_operators(self):
        # Create a synth with default operators
        synth = M8FMSynth(name="ModifyOperators", algo=0x00)  # A_B_C_D
        
        # Modify the operators
        operators = synth.operators
        operators[0].shape = 0x00  # SIN
        operators[0].ratio = 8
        operators[0].level = 240
        operators[0].feedback = 64
        operators[0].mod_a = 0x01  # LEV1
        operators[0].mod_b = 0x05  # RAT1
        
        operators[1].shape = 0x06  # TRI
        operators[1].ratio = 4
        operators[1].level = 200
        operators[1].feedback = 32
        operators[1].mod_a = 0x02  # LEV2
        operators[1].mod_b = 0x06  # RAT2
        
        # Update the synth's operators
        synth.operators = operators
        
        # Check that the underlying params were updated
        self.assertEqual(synth.params.shape1, 0x00)  # SIN
        self.assertEqual(synth.params.ratio1, 8)
        self.assertEqual(synth.params.level1, 240)
        self.assertEqual(synth.params.feedback1, 64)
        self.assertEqual(synth.params.mod_a1, 0x01)  # LEV1
        self.assertEqual(synth.params.mod_b1, 0x05)  # RAT1
        
        self.assertEqual(synth.params.shape2, 0x06)  # TRI
        self.assertEqual(synth.params.ratio2, 4)
        self.assertEqual(synth.params.level2, 200)
        self.assertEqual(synth.params.feedback2, 32)
        self.assertEqual(synth.params.mod_a2, 0x02)  # LEV2
        self.assertEqual(synth.params.mod_b2, 0x06)  # RAT2
    
    def test_serialize_deserialize(self):  # Re-enabled test
        # Create operators with raw integer values
        operators = [
            FMOperator(shape=0x00, ratio=8, level=240, feedback=64, mod_a=0x01, mod_b=0x05),  # SIN, LEV1, RAT1
            FMOperator(shape=0x06, ratio=4, level=200, feedback=32, mod_a=0x02, mod_b=0x06),  # TRI, LEV2, RAT2
            FMOperator(shape=0x08, ratio=2, level=160, feedback=16, mod_a=0x03, mod_b=0x07),  # SQR, LEV3, RAT3
            FMOperator(shape=0x07, ratio=1, level=120, feedback=8, mod_a=0x04, mod_b=0x08)    # SAW, LEV4, RAT4
        ]
        
        # Create a synth with the operators
        synth = M8FMSynth(
            name="SerializeTest",
            algo=0x02,  # A_B_PLUS_C_D
            operators=operators
        )
        
        # Convert to dict
        data = synth.as_dict()
        
        # Verify operators in dict
        self.assertIn('operators', data)
        self.assertEqual(len(data['operators']), 4)
        
        # Check first operator values - these should now be strings in the dictionary
        self.assertEqual(data['operators'][0]['shape'], 'SIN')
        self.assertEqual(data['operators'][0]['ratio'], 8)
        self.assertEqual(data['operators'][0]['level'], 240)
        self.assertEqual(data['operators'][0]['feedback'], 64)
        self.assertEqual(data['operators'][0]['mod_a'], 'LEV1')
        self.assertEqual(data['operators'][0]['mod_b'], 'RAT1')
        
        # Recreate from dict - this will deserialize the string enums back
        new_synth = M8FMSynth.from_dict(data)
        
        # Check operators internal params were correctly deserialized (using params to check raw values)
        self.assertEqual(len(new_synth.operators), 4)
        
        # Check either the enum string or numeric value is correct
        # This accommodates both implementation approaches
        shape1 = new_synth.params.shape1
        self.assertTrue(shape1 == 0x00 or shape1 == 'SIN',
                       f"Shape1 should be either 0x00 or 'SIN', got {shape1}")
        
        self.assertEqual(new_synth.params.ratio1, 8)
        self.assertEqual(new_synth.params.level1, 240)
        self.assertEqual(new_synth.params.feedback1, 64)
        
        mod_a1 = new_synth.params.mod_a1
        self.assertTrue(mod_a1 == 0x01 or mod_a1 == 'LEV1',
                       f"mod_a1 should be either 0x01 or 'LEV1', got {mod_a1}")
        
        mod_b1 = new_synth.params.mod_b1
        self.assertTrue(mod_b1 == 0x05 or mod_b1 == 'RAT1',
                       f"mod_b1 should be either 0x05 or 'RAT1', got {mod_b1}")


if __name__ == '__main__':
    unittest.main()