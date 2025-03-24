import unittest
from m8.api.project import M8Project
from m8.api.instruments import M8Instrument


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
        self.assertEqual(self.instrument_dict['type'], 0)  # When loading from file, the numeric ID is preserved
        # Check that the instrument is recognized as a WavSynth
        self.assertEqual(self.instrument.instrument_type, "WAVSYNTH")
        
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
            'shape': "WT_VOXSYNTH", # 0x45 (Now using enum name)
            'size': 64,            # 0x40
            'mult': 32,            # 0x20
            'warp': 16,            # 0x10
            'scan': 16,            # 0x10
            'filter': "LOWPASS",   # 0x01 (Enum value from M8FilterTypes)
            'cutoff': 32,          # 0x20
            'res': 208,            # 0xD0
            'amp': 80,             # 0x50
            'limit': "SIN",        # 0x01 (Enum value from M8LimitTypes)
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
        # Test modulators - focusing on the ones with non-zero destination
        # Filter modulators to only include ones with a destination (OLD definition of non-empty)
        non_zero_destination_mods = [mod for mod in self.instrument_dict['modulators'] 
                                    if mod['destination'] != 0]
        
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
        
        # Verify we have the right number of non-zero destination modulators
        self.assertEqual(len(non_zero_destination_mods), len(expected_modulators),
                        "Number of non-zero destination modulators doesn't match")
        
        # Sort both lists by index to ensure comparison works
        non_zero_destination_mods.sort(key=lambda x: x['index'])
        expected_modulators.sort(key=lambda x: x['index'])
        
        # Compare just the modulators with non-zero destinations
        for i, expected_modulator in enumerate(expected_modulators):
            actual_modulator = non_zero_destination_mods[i]
            for field, expected_value in expected_modulator.items():
                with self.subTest(modulator=i, field=field):
                    self.assertEqual(actual_modulator[field], expected_value,
                                    f"Modulator {i} field '{field}' doesn't match expected value")


if __name__ == '__main__':
    unittest.main()