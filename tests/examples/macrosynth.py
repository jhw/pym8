import unittest
from m8.api.instruments import M8Instrument


class TestMacroSynthMapping(unittest.TestCase):
    """
    Test that MacroSynth instruments from M8S files get correctly mapped when read 
    into Python objects.
    """
    
    def setUp(self):
        # Load the M8I instrument file
        self.instrument = M8Instrument.read_from_file("tests/examples/fixtures/MACROSYNTH.m8i")
        # Get its dictionary representation
        self.instrument_dict = self.instrument.as_dict()
    
    def test_macrosynth_type(self):
        # Verify instrument type - note that with current serialization it returns a string name
        # TODO: When read() properly handles parent-child relationships for enum serialization,
        # this test can be adjusted to expect string values consistently
        self.assertEqual(self.instrument_dict['type'], "MACROSYNTH")
        # Check that the instrument is recognized as a MacroSynth
        self.assertEqual(self.instrument.instrument_type, "MACROSYNTH")
        
    def test_macrosynth_name(self):
        # Test that the instrument name should be "MYMACRO" after stripping
        # In the binary file, the name field is "MYMACRO" followed by 0xFF bytes
        name = self.instrument_dict['name']
        self.assertEqual(name, "MYMACRO", 
                        "Instrument name should be 'MYMACRO'")
    
    def test_macrosynth_numeric_fields(self):
        # Test all numeric fields except name
        expected_values = {
            'transpose': 4,        # 0x04
            'eq': 1,               # 0x01
            'table_tick': 1,       # 0x01
            'volume': 0,           # 0x00
            'pitch': 0,            # 0x00
            'finetune': 128,       # 0x80
            'shape': 'SAW_SUB',    # 0x06 (Enum value from M8MacroSynthShapes)
            'timbre': 112,         # 0x70
            'color': 144,          # 0x90
            'degrade': 1,          # 0x01
            'redux': 208,          # 0xD0
            'filter': "LOWPASS",   # 0x01 (Enum value from M8FilterTypes)
            'cutoff': 48,          # 0x30
            'res': 224,            # 0xE0
            'amp': 32,             # 0x20
            'limit': "FOLD",       # 0x02 (Enum value from M8LimitTypes)
            'pan': 128,            # 0x80
            'dry': 160,            # 0xA0
            'chorus': 176,         # 0xB0
            'delay': 128,          # 0x80
            'reverb': 64           # 0x40
        }
        
        for field, expected_value in expected_values.items():
            with self.subTest(field=field):
                self.assertEqual(self.instrument_dict[field], expected_value, 
                                f"Field '{field}' doesn't match expected value")
    
    def test_macrosynth_modulators(self):
        # Test modulators - M8Modulator.is_empty() now filters out those with destination 'OFF'
        # so we can directly test the modulators collection
        
        # Now read() properly handles parent-child relationships for enum serialization,
        # so destination is using string enum names
        expected_modulators = [
            {
                'destination': 'VOLUME',  # 0x01
                'amount': 255,       # 0xFF
                'attack': 0,         # 0x00
                'hold': 255,         # 0xFF
                'decay': 0,          # 0x00
                'type': 'AHD_ENVELOPE',  # 0x00
                'index': 0           # 0x00
            },
            {
                'destination': 'CUTOFF',  # 0x07
                'amount': 112,       # 0x70
                'attack': 0,         # 0x00
                'hold': 112,         # 0x70
                'decay': 0,          # 0x00
                'type': 'AHD_ENVELOPE',  # 0x00
                'index': 1           # 0x01
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
                        # Check if we have a number vs string situation (e.g., 1 vs 'VOLUME')
                        if isinstance(actual_modulator[field], int) and isinstance(expected_value, str):
                            # Map common destination values
                            destination_map = {1: 'VOLUME', 7: 'CUTOFF'}
                            if actual_modulator[field] in destination_map:
                                self.assertEqual(destination_map[actual_modulator[field]], expected_value,
                                            f"Modulator {i} field '{field}' doesn't match expected value")
                                continue
                    
                    # Standard equality check for everything else
                    self.assertEqual(actual_modulator[field], expected_value,
                                    f"Modulator {i} field '{field}' doesn't match expected value")


if __name__ == '__main__':
    unittest.main()