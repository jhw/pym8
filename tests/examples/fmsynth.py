import unittest
from m8.api.project import M8Project
from m8.api.instruments import M8Instrument


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


if __name__ == '__main__':
    unittest.main()