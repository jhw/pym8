import unittest
from m8.api.project import M8Project


class TestWavSynthMapping(unittest.TestCase):
    """
    Test that WavSynth instruments from M8S files get correctly mapped when read 
    into Python objects.
    """
    
    def setUp(self):
        # Load the M8S file with WavSynth instrument
        self.project = M8Project.read_from_file("tests/examples/fixtures/WAVSYNTH.m8s")
        # Get the first instrument (WavSynth)
        self.instrument = self.project.instruments[0]
        # Get its dictionary representation
        self.instrument_dict = self.instrument.as_dict()
    
    def test_wavsynth_type(self):
        # Verify instrument type
        self.assertEqual(self.instrument_dict['type'], 0)
        
    def test_wavsynth_name(self):
        # Test that the instrument name should be "MYWAV" after stripping
        # In the binary file, the name field is "MYWAV" followed by 0xFF bytes
        name = self.instrument_dict['name']
        self.assertEqual(name, "MYWAV", 
                        "Instrument name should be 'MYWAV'")
    
    def test_wavsynth_numeric_fields(self):
        # Test all numeric fields except name
        expected_values = {
            'transpose': 4,        # 0x04
            'eq': 1,               # 0x01
            'table_tick': 1,       # 0x01
            'volume': 0,           # 0x00
            'pitch': 0,            # 0x00
            'finetune': 128,       # 0x80
            'shape': 69,           # 0x45 (WT_VOXSYNTH)
            'size': 64,            # 0x40
            'mult': 32,            # 0x20
            'warp': 16,            # 0x10
            'scan': 16,            # 0x10
            'filter': 1,           # 0x01
            'cutoff': 32,          # 0x20
            'res': 208,            # 0xD0
            'amp': 80,             # 0x50
            'limit': 1,            # 0x01
            'pan': 128,            # 0x80
            'dry': 176,            # 0xB0
            'chorus': 144,         # 0x90
            'delay': 96,           # 0x60
            'reverb': 96           # 0x60
        }
        
        for field, expected_value in expected_values.items():
            with self.subTest(field=field):
                self.assertEqual(self.instrument_dict[field], expected_value, 
                                f"Field '{field}' doesn't match expected value")
    
    def test_wavsynth_modulators(self):
        # Test modulators
        expected_modulators = [
            {
                'destination': 1,    # 0x01
                'amount': 255,       # 0xFF
                'attack': 0,         # 0x00
                'hold': 0,           # 0x00
                'decay': 128,        # 0x80
                'type': 0,           # 0x00
                'index': 0           # 0x00
            },
            {
                'destination': 7,    # 0x07
                'amount': 128,       # 0x80
                'attack': 0,         # 0x00
                'hold': 0,           # 0x00
                'decay': 64,         # 0x40
                'type': 0,           # 0x00
                'index': 1           # 0x01
            }
        ]
        
        self.assertEqual(len(self.instrument_dict['modulators']), len(expected_modulators),
                        "Number of modulators doesn't match")
        
        for i, expected_modulator in enumerate(expected_modulators):
            actual_modulator = self.instrument_dict['modulators'][i]
            for field, expected_value in expected_modulator.items():
                with self.subTest(modulator=i, field=field):
                    self.assertEqual(actual_modulator[field], expected_value,
                                    f"Modulator {i} field '{field}' doesn't match expected value")


if __name__ == '__main__':
    unittest.main()