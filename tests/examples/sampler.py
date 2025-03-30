import unittest
from m8.api.instruments import M8Instrument


class TestSamplerMapping(unittest.TestCase):
    """
    Test that Sampler instruments from M8S files get correctly mapped when read 
    into Python objects.
    """
    
    def setUp(self):
        # Load the M8I instrument file
        self.instrument = M8Instrument.read_from_file("tests/examples/fixtures/SAMPLER.m8i")
        # Get its dictionary representation
        self.instrument_dict = self.instrument.as_dict()
    
    def test_sampler_type(self):
        # Verify instrument type - note that with current serialization it returns a string name
        # TODO: When read() properly handles parent-child relationships for enum serialization,
        # this test can be adjusted to expect string values consistently
        self.assertEqual(self.instrument_dict['type'], "SAMPLER")
        # Check that the instrument is recognized as a Sampler
        self.assertEqual(self.instrument.instrument_type, "SAMPLER")
        
    def test_sampler_name(self):
        # Test that the instrument name should be "MYSAMPLER" after stripping
        # In the binary file, the name field is "MYSAMPLER" followed by 0xFF bytes
        name = self.instrument_dict['name']
        self.assertEqual(name, "MYSAMPLER", 
                        "Instrument name should be 'MYSAMPLER'")
    
    def test_sampler_numeric_fields(self):
        # Test all numeric fields except name and sample_path
        expected_values = {
            'transpose': 4,        # 0x04
            'eq': 1,               # 0x01
            'table_tick': 1,       # 0x01
            'volume': 0,           # 0x00
            'pitch': 0,            # 0x00
            'finetune': 129,       # 0x81
            'play_mode': 'FWD',    # 0x00 (Enum value from M8SamplerPlayMode)
            'slice': 0,            # 0x00
            'start': 0,            # 0x00
            'loop_start': 0,       # 0x00
            'length': 128,         # 0x80
            'degrade': 1,          # 0x01
            'filter': "BANDPASS",  # 0x03 (Enum value from M8FilterTypes)
            'cutoff': 111,         # 0x6F
            'res': 224,            # 0xE0
            'amp': 16,             # 0x10
            'limit': "SIN",        # 0x01 (Enum value from M8LimitTypes)
            'pan': 128,            # 0x80
            'dry': 128,            # 0x80
            'chorus': 144,         # 0x90
            'delay': 128,          # 0x80
            'reverb': 64           # 0x40
        }
        
        for field, expected_value in expected_values.items():
            with self.subTest(field=field):
                self.assertEqual(self.instrument_dict[field], expected_value, 
                                f"Field '{field}' doesn't match expected value")
    
    def test_sampler_path(self):
        # Test the sample path
        self.assertEqual(self.instrument_dict['sample_path'], 
                        "/Samples/Packs/erica-pico/legowelt/26ERIKASimplibell.wav",
                        "Sample path doesn't match expected value")
    
    def test_sampler_modulators(self):
        # Test that there are no modulators with destinations
        # M8Modulator.is_empty() now filters out modulators with destination 'OFF'
        # so the modulators list should be empty
        
        self.assertEqual(len(self.instrument_dict['modulators']), 0,
                        "Number of modulators should be 0")


if __name__ == '__main__':
    unittest.main()