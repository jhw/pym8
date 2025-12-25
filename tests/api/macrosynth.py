import unittest
from m8.api.instruments.macrosynth import M8Macrosynth, DEFAULT_PARAMETERS, M8MacrosynthParam, M8MacroShape
from m8.api.instrument import MODULATORS_OFFSET
from m8.api.modulator import M8Modulators


class TestM8Macrosynth(unittest.TestCase):
    def setUp(self):
        # Define Macrosynth-specific parameters
        self.test_name = "TestMacro"

    def test_constructor_and_defaults(self):
        # Test default constructor
        macrosynth = M8Macrosynth()

        # Check type is set correctly
        self.assertEqual(macrosynth.get(M8MacrosynthParam.TYPE), 0x01)  # MACROSYNTH type_id is 1

        # Check default parameters
        self.assertEqual(macrosynth.name, "")

        # Check non-zero defaults using generic get
        self.assertEqual(macrosynth.get(M8MacrosynthParam.FINE_TUNE), 0x80)  # FINETUNE
        self.assertEqual(macrosynth.get(M8MacrosynthParam.CUTOFF), 0xFF)     # CUTOFF
        self.assertEqual(macrosynth.get(M8MacrosynthParam.PAN), 0x80)        # PAN
        self.assertEqual(macrosynth.get(M8MacrosynthParam.DRY), 0xC0)        # DRY

    def test_constructor_with_parameters(self):
        # Test with name
        macrosynth = M8Macrosynth(name=self.test_name)

        # Check parameters
        self.assertEqual(macrosynth.name, self.test_name)

        # Set custom values using generic set
        macrosynth.set(M8MacrosynthParam.CUTOFF, 0x20)
        macrosynth.set(M8MacrosynthParam.RESONANCE, 0xC0)
        macrosynth.set(M8MacrosynthParam.SHAPE, M8MacroShape.FM)
        macrosynth.set(M8MacrosynthParam.TIMBRE, 0x40)

        # Verify using get
        self.assertEqual(macrosynth.get(M8MacrosynthParam.CUTOFF), 0x20)
        self.assertEqual(macrosynth.get(M8MacrosynthParam.RESONANCE), 0xC0)
        self.assertEqual(macrosynth.get(M8MacrosynthParam.SHAPE), M8MacroShape.FM)
        self.assertEqual(macrosynth.get(M8MacrosynthParam.TIMBRE), 0x40)

    def test_binary_serialization(self):
        # Create macrosynth with custom parameters
        macrosynth = M8Macrosynth(name="TEST")
        macrosynth.set(M8MacrosynthParam.CUTOFF, 0x20)
        macrosynth.set(M8MacrosynthParam.RESONANCE, 0xC0)
        macrosynth.set(M8MacrosynthParam.SHAPE, M8MacroShape.BELL)
        macrosynth.set(M8MacrosynthParam.TIMBRE, 0x80)

        # Write to binary
        binary = macrosynth.write()

        # Read it back
        read_macrosynth = M8Macrosynth.read(binary)

        # Check all parameters were preserved
        self.assertEqual(read_macrosynth.name, "TEST")
        self.assertEqual(read_macrosynth.get(M8MacrosynthParam.CUTOFF), 0x20)
        self.assertEqual(read_macrosynth.get(M8MacrosynthParam.RESONANCE), 0xC0)
        self.assertEqual(read_macrosynth.get(M8MacrosynthParam.SHAPE), M8MacroShape.BELL)
        self.assertEqual(read_macrosynth.get(M8MacrosynthParam.TIMBRE), 0x80)

    def test_clone(self):
        # Create macrosynth with custom parameters
        original = M8Macrosynth(name=self.test_name)
        original.set(M8MacrosynthParam.CUTOFF, 0x20)
        original.set(M8MacrosynthParam.RESONANCE, 0xC0)
        original.set(M8MacrosynthParam.SHAPE, M8MacroShape.PLUK)
        original.set(M8MacrosynthParam.COLOUR, 0x60)

        # Clone it
        cloned = original.clone()

        # Check they are different objects
        self.assertIsNot(cloned, original)

        # Check all values match
        self.assertEqual(cloned.name, original.name)
        self.assertEqual(cloned.get(M8MacrosynthParam.CUTOFF), original.get(M8MacrosynthParam.CUTOFF))
        self.assertEqual(cloned.get(M8MacrosynthParam.RESONANCE), original.get(M8MacrosynthParam.RESONANCE))
        self.assertEqual(cloned.get(M8MacrosynthParam.SHAPE), original.get(M8MacrosynthParam.SHAPE))
        self.assertEqual(cloned.get(M8MacrosynthParam.COLOUR), original.get(M8MacrosynthParam.COLOUR))

    def test_modulators_initialized(self):
        """Test that modulators are initialized with defaults."""
        macrosynth = M8Macrosynth()

        # Check modulators exist
        self.assertIsInstance(macrosynth.modulators, M8Modulators)

        # Check 4 modulators
        self.assertEqual(len(macrosynth.modulators), 4)

        # Check default types (2 ADSR, 2 LFO based on rust docs)
        # Note: Default might be different from sampler, but let's verify with 0 (AHD) for now
        self.assertEqual(macrosynth.modulators[0].mod_type, 0)  # AHD/ADSR
        self.assertEqual(macrosynth.modulators[1].mod_type, 0)  # AHD/ADSR

    def test_modulators_read_write(self):
        """Test that modulators are read and written correctly."""
        # Create macrosynth with custom modulator
        original = M8Macrosynth(name="TEST")
        original.modulators[0].destination = 1
        original.modulators[0].set(2, 0x20)  # Attack

        # Write to binary
        binary = original.write()

        # Check length (should be same as sampler block size)
        self.assertEqual(len(binary), 215)  # Full instrument block

        # Read back
        deserialized = M8Macrosynth.read(binary)

        # Verify modulator preserved
        self.assertEqual(deserialized.modulators[0].destination, 1)
        self.assertEqual(deserialized.modulators[0].get(2), 0x20)

    def test_modulators_clone(self):
        """Test that modulators are cloned correctly."""
        original = M8Macrosynth(name="TEST")
        original.modulators[1].destination = 5
        original.modulators[1].set(4, 0x40)  # Decay

        # Clone
        cloned = original.clone()

        # Check modulator values match
        self.assertEqual(cloned.modulators[1].destination, original.modulators[1].destination)
        self.assertEqual(cloned.modulators[1].get(4), original.modulators[1].get(4))

        # Modify clone
        cloned.modulators[1].destination = 2

        # Check original unchanged
        self.assertEqual(original.modulators[1].destination, 5)

    def test_macroshape_enum(self):
        """Test that MacroShape enum values work correctly."""
        macrosynth = M8Macrosynth()

        # Test basic shapes
        macrosynth.set(M8MacrosynthParam.SHAPE, M8MacroShape.CSAW)
        self.assertEqual(macrosynth.get(M8MacrosynthParam.SHAPE), M8MacroShape.CSAW)

        macrosynth.set(M8MacrosynthParam.SHAPE, M8MacroShape.FM)
        self.assertEqual(macrosynth.get(M8MacrosynthParam.SHAPE), M8MacroShape.FM)

        # Test physical modeling shapes
        macrosynth.set(M8MacrosynthParam.SHAPE, M8MacroShape.PLUK)
        self.assertEqual(macrosynth.get(M8MacrosynthParam.SHAPE), M8MacroShape.PLUK)

    def test_macrosynth_specific_params(self):
        """Test MacroSynth-specific parameters (TIMBRE, COLOUR, DEGRADE, REDUX)."""
        macrosynth = M8Macrosynth()

        # Test TIMBRE
        macrosynth.set(M8MacrosynthParam.TIMBRE, 0x40)
        self.assertEqual(macrosynth.get(M8MacrosynthParam.TIMBRE), 0x40)

        # Test COLOUR
        macrosynth.set(M8MacrosynthParam.COLOUR, 0x80)
        self.assertEqual(macrosynth.get(M8MacrosynthParam.COLOUR), 0x80)

        # Test DEGRADE
        macrosynth.set(M8MacrosynthParam.DEGRADE, 0x20)
        self.assertEqual(macrosynth.get(M8MacrosynthParam.DEGRADE), 0x20)

        # Test REDUX
        macrosynth.set(M8MacrosynthParam.REDUX, 0x60)
        self.assertEqual(macrosynth.get(M8MacrosynthParam.REDUX), 0x60)

    def test_to_dict_default_enum_mode(self):
        """Test to_dict() with default enum_mode='value' returns integer values."""
        from m8.api.instrument import M8FilterType, M8LimiterType

        macrosynth = M8Macrosynth(name="EnumTest")
        macrosynth.set(M8MacrosynthParam.SHAPE, M8MacroShape.VOSM)
        macrosynth.set(M8MacrosynthParam.FILTER_TYPE, M8FilterType.LOWPASS)
        macrosynth.set(M8MacrosynthParam.LIMIT, M8LimiterType.SIN)

        # Export with default enum_mode
        result = macrosynth.to_dict()

        # Verify enum values are integers (backward compatibility)
        self.assertEqual(result['params']['SHAPE'], M8MacroShape.VOSM.value)
        self.assertEqual(result['params']['FILTER_TYPE'], M8FilterType.LOWPASS.value)
        self.assertEqual(result['params']['LIMIT'], M8LimiterType.SIN.value)
        self.assertIsInstance(result['params']['SHAPE'], int)
        self.assertIsInstance(result['params']['FILTER_TYPE'], int)
        self.assertIsInstance(result['params']['LIMIT'], int)

    def test_to_dict_enum_mode_name(self):
        """Test to_dict() with enum_mode='name' returns human-readable enum names."""
        from m8.api.instrument import M8FilterType, M8LimiterType

        macrosynth = M8Macrosynth(name="EnumTest")
        macrosynth.set(M8MacrosynthParam.SHAPE, M8MacroShape.VOSM)
        macrosynth.set(M8MacrosynthParam.FILTER_TYPE, M8FilterType.LOWPASS)
        macrosynth.set(M8MacrosynthParam.LIMIT, M8LimiterType.SIN)

        # Export with enum_mode='name'
        result = macrosynth.to_dict(enum_mode='name')

        # Verify enum values are human-readable strings
        self.assertEqual(result['params']['SHAPE'], 'VOSM')
        self.assertEqual(result['params']['FILTER_TYPE'], 'LOWPASS')
        self.assertEqual(result['params']['LIMIT'], 'SIN')
        self.assertIsInstance(result['params']['SHAPE'], str)
        self.assertIsInstance(result['params']['FILTER_TYPE'], str)
        self.assertIsInstance(result['params']['LIMIT'], str)

    def test_from_dict_with_integer_values(self):
        """Test from_dict() accepts integer enum values (backward compatibility)."""
        from m8.api.instrument import M8FilterType, M8LimiterType

        params = {
            'name': 'IntTest',
            'params': {
                'SHAPE': M8MacroShape.FBFM.value,
                'FILTER_TYPE': M8FilterType.HIGHPASS.value,
                'LIMIT': M8LimiterType.CLIP.value,
                'CUTOFF': 0x40,
            },
            'modulators': []
        }

        macrosynth = M8Macrosynth.from_dict(params)

        # Verify values were set correctly
        self.assertEqual(macrosynth.name, 'IntTest')
        self.assertEqual(macrosynth.get(M8MacrosynthParam.SHAPE), M8MacroShape.FBFM.value)
        self.assertEqual(macrosynth.get(M8MacrosynthParam.FILTER_TYPE), M8FilterType.HIGHPASS.value)
        self.assertEqual(macrosynth.get(M8MacrosynthParam.LIMIT), M8LimiterType.CLIP.value)
        self.assertEqual(macrosynth.get(M8MacrosynthParam.CUTOFF), 0x40)

    def test_from_dict_with_string_enum_names(self):
        """Test from_dict() accepts string enum names (human-readable YAML)."""
        from m8.api.instrument import M8FilterType, M8LimiterType

        params = {
            'name': 'StringTest',
            'params': {
                'SHAPE': 'FBFM',
                'FILTER_TYPE': 'HIGHPASS',
                'LIMIT': 'CLIP',
                'CUTOFF': 0x40,
            },
            'modulators': []
        }

        macrosynth = M8Macrosynth.from_dict(params)

        # Verify values were set correctly
        self.assertEqual(macrosynth.name, 'StringTest')
        self.assertEqual(macrosynth.get(M8MacrosynthParam.SHAPE), M8MacroShape.FBFM.value)
        self.assertEqual(macrosynth.get(M8MacrosynthParam.FILTER_TYPE), M8FilterType.HIGHPASS.value)
        self.assertEqual(macrosynth.get(M8MacrosynthParam.LIMIT), M8LimiterType.CLIP.value)
        self.assertEqual(macrosynth.get(M8MacrosynthParam.CUTOFF), 0x40)

    def test_round_trip_serialization_with_enum_names(self):
        """Test round-trip: to_dict(enum_mode='name') -> from_dict() -> to_dict()."""
        from m8.api.instrument import M8FilterType, M8LimiterType

        # Create original macrosynth
        original = M8Macrosynth(name="RoundTrip")
        original.set(M8MacrosynthParam.SHAPE, M8MacroShape.BOWD)
        original.set(M8MacrosynthParam.FILTER_TYPE, M8FilterType.BANDPASS)
        original.set(M8MacrosynthParam.LIMIT, M8LimiterType.FOLD)
        original.set(M8MacrosynthParam.CUTOFF, 0x60)
        original.set(M8MacrosynthParam.RESONANCE, 0xA0)

        # Export with enum_mode='name'
        dict_with_names = original.to_dict(enum_mode='name')

        # Verify enum names are strings
        self.assertEqual(dict_with_names['params']['SHAPE'], 'BOWD')
        self.assertEqual(dict_with_names['params']['FILTER_TYPE'], 'BANDPASS')
        self.assertEqual(dict_with_names['params']['LIMIT'], 'FOLD')

        # Import from dict
        restored = M8Macrosynth.from_dict(dict_with_names)

        # Verify all values match
        self.assertEqual(restored.name, original.name)
        self.assertEqual(restored.get(M8MacrosynthParam.SHAPE), original.get(M8MacrosynthParam.SHAPE))
        self.assertEqual(restored.get(M8MacrosynthParam.FILTER_TYPE), original.get(M8MacrosynthParam.FILTER_TYPE))
        self.assertEqual(restored.get(M8MacrosynthParam.LIMIT), original.get(M8MacrosynthParam.LIMIT))
        self.assertEqual(restored.get(M8MacrosynthParam.CUTOFF), original.get(M8MacrosynthParam.CUTOFF))
        self.assertEqual(restored.get(M8MacrosynthParam.RESONANCE), original.get(M8MacrosynthParam.RESONANCE))

        # Export again with enum_mode='name'
        dict_restored = restored.to_dict(enum_mode='name')

        # Verify enum names are preserved
        self.assertEqual(dict_restored['params']['SHAPE'], 'BOWD')
        self.assertEqual(dict_restored['params']['FILTER_TYPE'], 'BANDPASS')
        self.assertEqual(dict_restored['params']['LIMIT'], 'FOLD')


if __name__ == '__main__':
    unittest.main()
