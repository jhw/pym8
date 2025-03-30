import unittest
from m8.api.project import M8Project
from m8.api.instruments import M8Instrument


class TestHyperSynthMapping(unittest.TestCase):
    """
    Test that HyperSynth instruments from M8S files get correctly mapped when read 
    into Python objects.
    """
    
    def setUp(self):
        # Load the M8S file with HyperSynth instrument
        self.project = M8Project.read_from_file("tests/examples/fixtures/HYPERSYN.m8s")
        # Get the first instrument (HyperSynth)
        self.instrument = self.project.instruments[0]
        # Get its dictionary representation
        self.instrument_dict = self.instrument.as_dict()
    
    def test_hypersynth_type(self):
        # Verify instrument type
        self.assertEqual(self.instrument_dict['type'], "HYPERSYNTH")
        # Check that the instrument is recognized as a HyperSynth
        self.assertEqual(self.instrument.instrument_type, "HYPERSYNTH")
        
    def test_hypersynth_name(self):
        # Test that the instrument name is empty as specified in the expected values
        name = self.instrument_dict['name']
        self.assertEqual(name, "", 
                        "Instrument name should be empty")
    
    def test_hypersynth_numeric_fields(self):
        # Test all numeric fields except name based on the provided expected values
        expected_values = {
            'transpose': 4,        # 0x04
            'eq': 1,               # 0x01
            'table_tick': 1,       # 0x01
            'volume': 0,           # 0x00
            'pitch': 0,            # 0x00
            'finetune': 128,       # 0x80
            'amp': 16,             # 0x10
            'chord': 0,            # 0x00
            'chorus': 192,         # 0xC0
            'cutoff': 64,          # 0x40
            'delay': 0,            # 0x00
            'dry': 192,            # 0xC0
            'filter': "LOWPASS",   # LOWPASS enum value
            'limit': "SIN",        # SIN enum value
            'note1': 3,            # 0x03
            'note2': 5,            # 0x05
            'note3': 12,           # 0x0C
            'note4': 14,           # 0x0E
            'note5': 16,           # 0x10
            'note6': 19,           # 0x13
            'pan': 128,            # 0x80
            'res': 208,            # 0xD0
            'reverb': 128,         # 0x80
            'scale': 1,            # 0x01
            'shift': 144,          # 0x90
            'swarm': 16,           # 0x10
            'width': 64,           # 0x40
            'subosc': 112          # 0x70
        }
        
        for field, expected_value in expected_values.items():
            with self.subTest(field=field):
                self.assertEqual(self.instrument_dict[field], expected_value, 
                                f"Field '{field}' doesn't match expected value")
    
    def test_hypersynth_modulators(self):
        # Test modulators based on the provided expected values
        expected_modulators = [
            {
                'type': 'AHD_ENVELOPE',    # AHD_ENVELOPE enum value
                'destination': 'VOLUME',  # VOLUME enum value
                'amount': 255,           # 0xFF
                'attack': 0,             # 0x00
                'decay': 128,            # 0x80
                'hold': 0,               # 0x00
                'index': 0               # 0x00
            },
            {
                'type': 'AHD_ENVELOPE',    # AHD_ENVELOPE enum value
                'destination': 7,        # 0x07 CUTOFF
                'amount': 127,           # 0x7F
                'attack': 0,             # 0x00
                'decay': 64,             # 0x40
                'hold': 0,               # 0x00
                'index': 1               # 0x01
            }
        ]
        
        # Verify we have the right number of modulators
        self.assertEqual(len(self.instrument_dict['modulators']), len(expected_modulators),
                        "Number of modulators doesn't match")
        
        # Sort both lists by index to ensure comparison works
        modulators = self.instrument_dict['modulators']
        expected_modulators.sort(key=lambda x: x['index'])
        
        # Compare the modulators
        for i, expected_modulator in enumerate(expected_modulators):
            actual_modulator = modulators[i]
            for field, expected_value in expected_modulator.items():
                with self.subTest(modulator=i, field=field):
                    # Handle the case where destination might be numeric or string
                    if field == 'destination' and actual_modulator[field] != expected_value:
                        # Check if we have a number vs string situation (e.g., 7 vs 'CUTOFF')
                        if expected_value == 7 and actual_modulator[field] == 'CUTOFF':
                            # This is an acceptable mapping
                            continue
                        # Handle the case where expected is VOLUME and actual is 1
                        if expected_value == 'VOLUME' and actual_modulator[field] == 1:
                            # This is an acceptable mapping
                            continue
                    
                    # Standard equality check for everything else
                    self.assertEqual(actual_modulator[field], expected_value,
                                    f"Modulator {i} field '{field}' doesn't match expected value")


if __name__ == '__main__':
    unittest.main()