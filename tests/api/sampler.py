import unittest
from m8.api.instruments.sampler import M8Sampler, M8SamplerParam, M8PlayMode, DEFAULT_PARAMETERS
from m8.api.instrument import M8FilterType, M8LimiterType, MODULATORS_OFFSET
from m8.api.modulator import M8Modulators, M8AHDParam


class TestM8Sampler(unittest.TestCase):
    def setUp(self):
        # Define Sampler-specific parameters
        self.test_name = "TestSampler"
        self.test_sample_path = "/samples/kick.wav"

    def test_constructor_and_defaults(self):
        # Test default constructor
        sampler = M8Sampler()

        # Check type is set correctly
        self.assertEqual(sampler.get(0), 0x02)  # SAMPLER type_id is 2

        # Check default parameters
        self.assertEqual(sampler.name, "")
        self.assertEqual(sampler.sample_path, "")

        # Check non-zero defaults using generic get
        self.assertEqual(sampler.get(17), 0x80)  # FINETUNE
        self.assertEqual(sampler.get(22), 0xFF)  # LENGTH
        self.assertEqual(sampler.get(25), 0xFF)  # CUTOFF
        self.assertEqual(sampler.get(29), 0x80)  # PAN
        self.assertEqual(sampler.get(30), 0xC0)  # DRY

    def test_constructor_with_parameters(self):
        # Test with name and sample_path
        sampler = M8Sampler(
            name=self.test_name,
            sample_path=self.test_sample_path
        )

        # Check parameters
        self.assertEqual(sampler.name, self.test_name)
        self.assertEqual(sampler.sample_path, self.test_sample_path)

        # Set custom values using generic set
        sampler.set(22, 0x80)  # LENGTH
        sampler.set(17, 0x70)  # FINETUNE
        sampler.set(25, 0xE0)  # CUTOFF
        sampler.set(29, 0x60)  # PAN
        sampler.set(30, 0xA0)  # DRY

        # Verify using get
        self.assertEqual(sampler.get(22), 0x80)
        self.assertEqual(sampler.get(17), 0x70)
        self.assertEqual(sampler.get(25), 0xE0)
        self.assertEqual(sampler.get(29), 0x60)
        self.assertEqual(sampler.get(30), 0xA0)

    def test_binary_serialization(self):
        """Test write/read round-trip preserves all parameters AND modulators."""
        # Create sampler with custom parameters
        sampler = M8Sampler(
            name="TEST",
            sample_path="/samples/kick.wav"
        )
        sampler.set(22, 0x80)  # LENGTH
        sampler.set(17, 0x70)  # FINETUNE
        sampler.set(25, 0xE0)  # CUTOFF
        sampler.set(29, 0x60)  # PAN
        sampler.set(30, 0xA0)  # DRY

        # Customize modulators
        sampler.modulators[0].destination = 1  # VOLUME
        sampler.modulators[0].amount = 255
        sampler.modulators[0].set(2, 0x00)  # Attack
        sampler.modulators[0].set(4, 0x60)  # Decay

        sampler.modulators[2].destination = 7  # CUTOFF
        sampler.modulators[2].amount = 80
        sampler.modulators[2].set(2, 0x00)  # LFO shape (TRI)

        # Write to binary
        binary = sampler.write()

        # Read it back
        read_sampler = M8Sampler.read(binary)

        # Check all parameters were preserved
        self.assertEqual(read_sampler.name, "TEST")
        self.assertEqual(read_sampler.sample_path, "/samples/kick.wav")
        self.assertEqual(read_sampler.get(22), 0x80)
        self.assertEqual(read_sampler.get(17), 0x70)
        self.assertEqual(read_sampler.get(25), 0xE0)
        self.assertEqual(read_sampler.get(29), 0x60)
        self.assertEqual(read_sampler.get(30), 0xA0)

        # Check modulators were preserved
        self.assertEqual(read_sampler.modulators[0].destination, 1)
        self.assertEqual(read_sampler.modulators[0].amount, 255)
        self.assertEqual(read_sampler.modulators[0].get(2), 0x00)
        self.assertEqual(read_sampler.modulators[0].get(4), 0x60)

        self.assertEqual(read_sampler.modulators[2].destination, 7)
        self.assertEqual(read_sampler.modulators[2].amount, 80)
        self.assertEqual(read_sampler.modulators[2].get(2), 0x00)

    def test_clone(self):
        # Create sampler with custom parameters
        original = M8Sampler(
            name=self.test_name,
            sample_path=self.test_sample_path
        )
        original.set(22, 0x80)  # LENGTH
        original.set(17, 0x70)  # FINETUNE
        original.set(25, 0xE0)  # CUTOFF
        original.set(29, 0x60)  # PAN
        original.set(30, 0xA0)  # DRY

        # Clone it
        cloned = original.clone()

        # Check they are different objects
        self.assertIsNot(cloned, original)

        # Check all values match
        self.assertEqual(cloned.name, original.name)
        self.assertEqual(cloned.sample_path, original.sample_path)
        self.assertEqual(cloned.get(22), original.get(22))
        self.assertEqual(cloned.get(17), original.get(17))
        self.assertEqual(cloned.get(25), original.get(25))
        self.assertEqual(cloned.get(29), original.get(29))
        self.assertEqual(cloned.get(30), original.get(30))

    def test_read_with_zero_defaults(self):
        # Simulate loading from a template with zeros for default parameters
        # Create binary data with type=2 (sampler) but zeros for default params
        from m8.api.instruments.sampler import BLOCK_SIZE
        binary_data = bytearray([0] * BLOCK_SIZE)
        binary_data[0] = 0x02  # Set type to SAMPLER

        # Read it back
        sampler = M8Sampler.read(binary_data)

        # Check that non-zero defaults were applied despite zeros in template
        self.assertEqual(sampler.get(0), 0x02)   # Type should be preserved
        self.assertEqual(sampler.get(17), 0x80)  # FINETUNE should default to 128
        self.assertEqual(sampler.get(22), 0xFF)  # LENGTH should default to 255
        self.assertEqual(sampler.get(25), 0xFF)  # CUTOFF should default to 255
        self.assertEqual(sampler.get(29), 0x80)  # PAN should default to 128
        self.assertEqual(sampler.get(30), 0xC0)  # DRY should default to 192

    def test_read_with_non_zero_values_preserved(self):
        # Test that non-zero values from file are preserved (not overwritten)
        from m8.api.instruments.sampler import BLOCK_SIZE
        binary_data = bytearray([0] * BLOCK_SIZE)
        binary_data[0] = 0x02   # Type
        binary_data[17] = 0x70  # FINETUNE (non-default)
        binary_data[22] = 0x80  # LENGTH (non-default)
        binary_data[25] = 0xE0  # CUTOFF (non-default)
        binary_data[29] = 0x60  # PAN (non-default)
        binary_data[30] = 0xA0  # DRY (non-default)

        # Read it back
        sampler = M8Sampler.read(binary_data)

        # Check that existing non-zero values were preserved
        self.assertEqual(sampler.get(17), 0x70)  # Should preserve 0x70
        self.assertEqual(sampler.get(22), 0x80)  # Should preserve 0x80
        self.assertEqual(sampler.get(25), 0xE0)  # Should preserve 0xE0
        self.assertEqual(sampler.get(29), 0x60)  # Should preserve 0x60
        self.assertEqual(sampler.get(30), 0xA0)  # Should preserve 0xA0

    def test_modulators_initialized(self):
        """Test that modulators are initialized with defaults."""
        sampler = M8Sampler()
        
        # Check modulators exist
        self.assertIsInstance(sampler.modulators, M8Modulators)
        
        # Check 4 modulators
        self.assertEqual(len(sampler.modulators), 4)
        
        # Check default types (2 AHD, 2 LFO)
        self.assertEqual(sampler.modulators[0].mod_type, 0)  # AHD
        self.assertEqual(sampler.modulators[1].mod_type, 0)  # AHD
        self.assertEqual(sampler.modulators[2].mod_type, 3)  # LFO
        self.assertEqual(sampler.modulators[3].mod_type, 3)  # LFO

    def test_modulators_read_write(self):
        """Test that modulators are read and written correctly."""
        # Create sampler with custom modulator
        original = M8Sampler(name="TEST")
        original.modulators[0].destination = 1
        original.modulators[0].set(2, 0x20)  # Attack
        
        # Write to binary
        binary = original.write()
        
        # Check modulators are at correct offset
        self.assertEqual(len(binary), 215)  # Full sampler block
        
        # Read back
        deserialized = M8Sampler.read(binary)
        
        # Verify modulator preserved
        self.assertEqual(deserialized.modulators[0].destination, 1)
        self.assertEqual(deserialized.modulators[0].get(2), 0x20)

    def test_modulators_clone(self):
        """Test that modulators are cloned correctly."""
        original = M8Sampler(name="TEST")
        original.modulators[1].destination = 3
        original.modulators[1].set(4, 0x40)  # Decay
        
        # Clone
        cloned = original.clone()
        
        # Check modulator values match
        self.assertEqual(cloned.modulators[1].destination, original.modulators[1].destination)
        self.assertEqual(cloned.modulators[1].get(4), original.modulators[1].get(4))
        
        # Modify clone
        cloned.modulators[1].destination = 5
        
        # Check original unchanged
        self.assertEqual(original.modulators[1].destination, 3)


class TestM8SamplerEnums(unittest.TestCase):
    """Test sampler-related enum values and usage."""

    def test_play_mode_enum_values(self):
        """Test all M8PlayMode enum values are defined correctly."""
        # Basic modes
        self.assertEqual(M8PlayMode.FWD, 0x00)
        self.assertEqual(M8PlayMode.REV, 0x01)
        self.assertEqual(M8PlayMode.FWDLOOP, 0x02)
        self.assertEqual(M8PlayMode.REVLOOP, 0x03)

        # Ping-pong modes
        self.assertEqual(M8PlayMode.FWD_PP, 0x04)
        self.assertEqual(M8PlayMode.REV_PP, 0x05)

        # Oscillator modes
        self.assertEqual(M8PlayMode.OSC, 0x06)
        self.assertEqual(M8PlayMode.OSC_REV, 0x07)
        self.assertEqual(M8PlayMode.OSC_PP, 0x08)

        # Repitch modes
        self.assertEqual(M8PlayMode.REPITCH, 0x09)
        self.assertEqual(M8PlayMode.REP_REV, 0x0A)
        self.assertEqual(M8PlayMode.REP_PP, 0x0B)

        # BPM sync modes
        self.assertEqual(M8PlayMode.REP_BPM, 0x0C)
        self.assertEqual(M8PlayMode.BPM_REV, 0x0D)
        self.assertEqual(M8PlayMode.BPM_PP, 0x0E)

        # Verify total count
        self.assertEqual(len(M8PlayMode), 15)

    def test_play_mode_default(self):
        """Test that default play mode is FWD (0x00)."""
        sampler = M8Sampler()
        self.assertEqual(sampler.get(M8SamplerParam.PLAY_MODE), M8PlayMode.FWD)

    def test_play_mode_set_and_get(self):
        """Test setting and getting different play modes."""
        sampler = M8Sampler(name="TEST")

        # Test each mode
        test_modes = [
            M8PlayMode.REV,
            M8PlayMode.FWDLOOP,
            M8PlayMode.OSC,
            M8PlayMode.REPITCH,
            M8PlayMode.BPM_PP,
        ]

        for mode in test_modes:
            sampler.set(M8SamplerParam.PLAY_MODE, mode)
            self.assertEqual(sampler.get(M8SamplerParam.PLAY_MODE), mode)

    def test_play_mode_serialization(self):
        """Test that play mode is preserved through write/read cycle."""
        original = M8Sampler(name="LOOP-TEST")
        original.set(M8SamplerParam.PLAY_MODE, M8PlayMode.FWDLOOP)

        # Write to binary
        binary = original.write()

        # Read back
        deserialized = M8Sampler.read(binary)

        # Verify play mode preserved
        self.assertEqual(
            deserialized.get(M8SamplerParam.PLAY_MODE),
            M8PlayMode.FWDLOOP
        )

    def test_filter_type_enum_values(self):
        """Test all M8FilterType enum values are defined correctly."""
        self.assertEqual(M8FilterType.OFF, 0x00)
        self.assertEqual(M8FilterType.LOWPASS, 0x01)
        self.assertEqual(M8FilterType.HIGHPASS, 0x02)
        self.assertEqual(M8FilterType.BANDPASS, 0x03)
        self.assertEqual(M8FilterType.BANDSTOP, 0x04)
        self.assertEqual(M8FilterType.LP_HP, 0x05)
        self.assertEqual(M8FilterType.ZDF_LP, 0x06)
        self.assertEqual(M8FilterType.ZDF_HP, 0x07)

        # Verify total count
        self.assertEqual(len(M8FilterType), 8)

    def test_filter_type_set_and_get(self):
        """Test setting and getting filter types."""
        sampler = M8Sampler(name="FILTER")

        # Test different filter types
        test_filters = [
            M8FilterType.OFF,
            M8FilterType.LOWPASS,
            M8FilterType.HIGHPASS,
            M8FilterType.BANDPASS,
            M8FilterType.ZDF_LP,
        ]

        for filter_type in test_filters:
            sampler.set(M8SamplerParam.FILTER_TYPE, filter_type)
            self.assertEqual(sampler.get(M8SamplerParam.FILTER_TYPE), filter_type)

    def test_filter_type_serialization(self):
        """Test that filter type is preserved through write/read cycle."""
        original = M8Sampler(name="LP-FILTER")
        original.set(M8SamplerParam.FILTER_TYPE, M8FilterType.LOWPASS)
        original.set(M8SamplerParam.CUTOFF, 0xC0)
        original.set(M8SamplerParam.RESONANCE, 0x40)

        # Write to binary
        binary = original.write()

        # Read back
        deserialized = M8Sampler.read(binary)

        # Verify filter settings preserved
        self.assertEqual(
            deserialized.get(M8SamplerParam.FILTER_TYPE),
            M8FilterType.LOWPASS
        )
        self.assertEqual(deserialized.get(M8SamplerParam.CUTOFF), 0xC0)
        self.assertEqual(deserialized.get(M8SamplerParam.RESONANCE), 0x40)

    def test_limiter_type_enum_values(self):
        """Test all M8LimiterType enum values are defined correctly."""
        self.assertEqual(M8LimiterType.CLIP, 0x00)
        self.assertEqual(M8LimiterType.SIN, 0x01)
        self.assertEqual(M8LimiterType.FOLD, 0x02)
        self.assertEqual(M8LimiterType.WRAP, 0x03)
        self.assertEqual(M8LimiterType.POST, 0x04)
        self.assertEqual(M8LimiterType.POSTAD, 0x05)
        self.assertEqual(M8LimiterType.POST_W1, 0x06)
        self.assertEqual(M8LimiterType.POST_W2, 0x07)
        self.assertEqual(M8LimiterType.POST_W3, 0x08)

        # Verify total count
        self.assertEqual(len(M8LimiterType), 9)

    def test_limiter_type_set_and_get(self):
        """Test setting and getting limiter types."""
        sampler = M8Sampler(name="LIMIT")

        # Test different limiter types
        test_limiters = [
            M8LimiterType.CLIP,
            M8LimiterType.SIN,
            M8LimiterType.FOLD,
            M8LimiterType.WRAP,
            M8LimiterType.POST,
        ]

        for limiter_type in test_limiters:
            sampler.set(M8SamplerParam.LIMIT, limiter_type)
            self.assertEqual(sampler.get(M8SamplerParam.LIMIT), limiter_type)

    def test_limiter_type_serialization(self):
        """Test that limiter type is preserved through write/read cycle."""
        original = M8Sampler(name="SIN-LIMIT")
        original.set(M8SamplerParam.LIMIT, M8LimiterType.SIN)
        original.set(M8SamplerParam.AMP, 0x20)

        # Write to binary
        binary = original.write()

        # Read back
        deserialized = M8Sampler.read(binary)

        # Verify limiter settings preserved
        self.assertEqual(
            deserialized.get(M8SamplerParam.LIMIT),
            M8LimiterType.SIN
        )
        self.assertEqual(deserialized.get(M8SamplerParam.AMP), 0x20)

    def test_combined_enum_usage(self):
        """Test using all three enums together in a realistic scenario."""
        sampler = M8Sampler(name="COMBO", sample_path="/samples/test.wav")

        # Configure sampler with all three enums
        sampler.set(M8SamplerParam.PLAY_MODE, M8PlayMode.FWDLOOP)
        sampler.set(M8SamplerParam.FILTER_TYPE, M8FilterType.LOWPASS)
        sampler.set(M8SamplerParam.CUTOFF, 0x80)
        sampler.set(M8SamplerParam.LIMIT, M8LimiterType.SIN)
        sampler.set(M8SamplerParam.AMP, 0x30)

        # Write and read
        binary = sampler.write()
        restored = M8Sampler.read(binary)

        # Verify all settings
        self.assertEqual(restored.name, "COMBO")
        self.assertEqual(restored.sample_path, "/samples/test.wav")
        self.assertEqual(
            restored.get(M8SamplerParam.PLAY_MODE),
            M8PlayMode.FWDLOOP
        )
        self.assertEqual(
            restored.get(M8SamplerParam.FILTER_TYPE),
            M8FilterType.LOWPASS
        )
        self.assertEqual(restored.get(M8SamplerParam.CUTOFF), 0x80)
        self.assertEqual(
            restored.get(M8SamplerParam.LIMIT),
            M8LimiterType.SIN
        )
        self.assertEqual(restored.get(M8SamplerParam.AMP), 0x30)


class TestSamplerDictSerialization(unittest.TestCase):
    """Tests for sampler dict serialization (to_dict/from_dict)."""

    def test_sampler_to_dict(self):
        """Test exporting sampler to dict."""
        sampler = M8Sampler(name="KICK", sample_path="/samples/kick.wav")
        sampler.set(M8SamplerParam.VOLUME, 0xFF)
        sampler.set(M8SamplerParam.PLAY_MODE, M8PlayMode.FWDLOOP)
        sampler.set(M8SamplerParam.FILTER_TYPE, M8FilterType.LOWPASS)
        sampler.set(M8SamplerParam.CUTOFF, 0xC0)

        # Configure a modulator
        sampler.modulators[0].destination = 1
        sampler.modulators[0].set(M8AHDParam.ATTACK, 0x20)

        result = sampler.to_dict()

        # Check structure
        self.assertIn('name', result)
        self.assertIn('sample_path', result)
        self.assertIn('params', result)
        self.assertIn('modulators', result)

        # Check values
        self.assertEqual(result['name'], "KICK")
        self.assertEqual(result['sample_path'], "/samples/kick.wav")
        self.assertEqual(result['params']['VOLUME'], 0xFF)
        self.assertEqual(result['params']['PLAY_MODE'], M8PlayMode.FWDLOOP)
        self.assertEqual(result['params']['FILTER_TYPE'], M8FilterType.LOWPASS)
        self.assertEqual(result['params']['CUTOFF'], 0xC0)

        # Check modulators
        self.assertEqual(len(result['modulators']), 4)
        self.assertEqual(result['modulators'][0]['destination'], 1)
        self.assertEqual(result['modulators'][0]['params']['ATTACK'], 0x20)

    def test_sampler_from_dict(self):
        """Test creating sampler from dict."""
        params = {
            'name': "SNARE",
            'sample_path': "/samples/snare.wav",
            'params': {
                'VOLUME': 0xF0,
                'PLAY_MODE': 2,  # FWDLOOP
                'FILTER_TYPE': 1,  # LOWPASS
                'CUTOFF': 0xA0,
                'RESONANCE': 0x40
            },
            'modulators': [
                {
                    'type': 0,
                    'destination': 1,
                    'amount': 0xFF,
                    'params': {'ATTACK': 0x10, 'DECAY': 0x40}
                }
            ]
        }

        sampler = M8Sampler.from_dict(params)

        # Verify basic properties
        self.assertEqual(sampler.name, "SNARE")
        self.assertEqual(sampler.sample_path, "/samples/snare.wav")

        # Verify parameters
        self.assertEqual(sampler.get(M8SamplerParam.VOLUME), 0xF0)
        self.assertEqual(sampler.get(M8SamplerParam.PLAY_MODE), 2)
        self.assertEqual(sampler.get(M8SamplerParam.FILTER_TYPE), 1)
        self.assertEqual(sampler.get(M8SamplerParam.CUTOFF), 0xA0)
        self.assertEqual(sampler.get(M8SamplerParam.RESONANCE), 0x40)

        # Verify modulators
        self.assertEqual(sampler.modulators[0].destination, 1)
        self.assertEqual(sampler.modulators[0].get(M8AHDParam.ATTACK), 0x10)
        self.assertEqual(sampler.modulators[0].get(M8AHDParam.DECAY), 0x40)

    def test_sampler_roundtrip(self):
        """Test that sampler to_dict -> from_dict preserves all values."""
        original = M8Sampler(name="TEST", sample_path="/test.wav")
        original.set(M8SamplerParam.VOLUME, 0xE0)
        original.set(M8SamplerParam.PLAY_MODE, M8PlayMode.OSC)
        original.set(M8SamplerParam.FILTER_TYPE, M8FilterType.HIGHPASS)
        original.set(M8SamplerParam.CUTOFF, 0x80)
        original.set(M8SamplerParam.LIMIT, M8LimiterType.SIN)

        # Configure modulators
        original.modulators[0].destination = 2
        original.modulators[0].set(M8AHDParam.ATTACK, 0x15)
        original.modulators[0].set(M8AHDParam.DECAY, 0x50)

        # Export and re-import
        params = original.to_dict()
        restored = M8Sampler.from_dict(params)

        # Verify everything matches
        self.assertEqual(restored.name, original.name)
        self.assertEqual(restored.sample_path, original.sample_path)
        self.assertEqual(
            restored.get(M8SamplerParam.VOLUME),
            original.get(M8SamplerParam.VOLUME)
        )
        self.assertEqual(
            restored.get(M8SamplerParam.PLAY_MODE),
            original.get(M8SamplerParam.PLAY_MODE)
        )
        self.assertEqual(
            restored.get(M8SamplerParam.FILTER_TYPE),
            original.get(M8SamplerParam.FILTER_TYPE)
        )
        self.assertEqual(
            restored.get(M8SamplerParam.CUTOFF),
            original.get(M8SamplerParam.CUTOFF)
        )
        self.assertEqual(
            restored.get(M8SamplerParam.LIMIT),
            original.get(M8SamplerParam.LIMIT)
        )

        # Verify modulators
        self.assertEqual(
            restored.modulators[0].destination,
            original.modulators[0].destination
        )
        self.assertEqual(
            restored.modulators[0].get(M8AHDParam.ATTACK),
            original.modulators[0].get(M8AHDParam.ATTACK)
        )
        self.assertEqual(
            restored.modulators[0].get(M8AHDParam.DECAY),
            original.modulators[0].get(M8AHDParam.DECAY)
        )

    def test_sampler_to_dict_default_enum_mode(self):
        """Test sampler to_dict() with default enum_mode='value' returns integer values."""
        sampler = M8Sampler(name="EnumTest", sample_path="/test.wav")
        sampler.set(M8SamplerParam.PLAY_MODE, M8PlayMode.FWDLOOP)
        sampler.set(M8SamplerParam.FILTER_TYPE, M8FilterType.LOWPASS)
        sampler.set(M8SamplerParam.LIMIT, M8LimiterType.SIN)

        # Export with default enum_mode
        result = sampler.to_dict()

        # Verify enum values are integers (backward compatibility)
        self.assertEqual(result['params']['PLAY_MODE'], M8PlayMode.FWDLOOP.value)
        self.assertEqual(result['params']['FILTER_TYPE'], M8FilterType.LOWPASS.value)
        self.assertEqual(result['params']['LIMIT'], M8LimiterType.SIN.value)
        self.assertIsInstance(result['params']['PLAY_MODE'], int)
        self.assertIsInstance(result['params']['FILTER_TYPE'], int)
        self.assertIsInstance(result['params']['LIMIT'], int)

    def test_sampler_to_dict_enum_mode_name(self):
        """Test sampler to_dict() with enum_mode='name' returns human-readable enum names."""
        sampler = M8Sampler(name="EnumTest", sample_path="/test.wav")
        sampler.set(M8SamplerParam.PLAY_MODE, M8PlayMode.FWDLOOP)
        sampler.set(M8SamplerParam.FILTER_TYPE, M8FilterType.LOWPASS)
        sampler.set(M8SamplerParam.LIMIT, M8LimiterType.SIN)

        # Export with enum_mode='name'
        result = sampler.to_dict(enum_mode='name')

        # Verify enum values are human-readable strings
        self.assertEqual(result['params']['PLAY_MODE'], 'FWDLOOP')
        self.assertEqual(result['params']['FILTER_TYPE'], 'LOWPASS')
        self.assertEqual(result['params']['LIMIT'], 'SIN')
        self.assertIsInstance(result['params']['PLAY_MODE'], str)
        self.assertIsInstance(result['params']['FILTER_TYPE'], str)
        self.assertIsInstance(result['params']['LIMIT'], str)

    def test_sampler_from_dict_with_integer_values(self):
        """Test sampler from_dict() accepts integer enum values (backward compatibility)."""
        params = {
            'name': 'IntTest',
            'sample_path': '/test.wav',
            'params': {
                'PLAY_MODE': M8PlayMode.OSC.value,
                'FILTER_TYPE': M8FilterType.HIGHPASS.value,
                'LIMIT': M8LimiterType.CLIP.value,
                'CUTOFF': 0x40,
            },
            'modulators': []
        }

        sampler = M8Sampler.from_dict(params)

        # Verify values were set correctly
        self.assertEqual(sampler.name, 'IntTest')
        self.assertEqual(sampler.get(M8SamplerParam.PLAY_MODE), M8PlayMode.OSC.value)
        self.assertEqual(sampler.get(M8SamplerParam.FILTER_TYPE), M8FilterType.HIGHPASS.value)
        self.assertEqual(sampler.get(M8SamplerParam.LIMIT), M8LimiterType.CLIP.value)
        self.assertEqual(sampler.get(M8SamplerParam.CUTOFF), 0x40)

    def test_sampler_from_dict_with_string_enum_names(self):
        """Test sampler from_dict() accepts string enum names (human-readable YAML)."""
        params = {
            'name': 'StringTest',
            'sample_path': '/test.wav',
            'params': {
                'PLAY_MODE': 'OSC',
                'FILTER_TYPE': 'HIGHPASS',
                'LIMIT': 'CLIP',
                'CUTOFF': 0x40,
            },
            'modulators': []
        }

        sampler = M8Sampler.from_dict(params)

        # Verify values were set correctly
        self.assertEqual(sampler.name, 'StringTest')
        self.assertEqual(sampler.get(M8SamplerParam.PLAY_MODE), M8PlayMode.OSC.value)
        self.assertEqual(sampler.get(M8SamplerParam.FILTER_TYPE), M8FilterType.HIGHPASS.value)
        self.assertEqual(sampler.get(M8SamplerParam.LIMIT), M8LimiterType.CLIP.value)
        self.assertEqual(sampler.get(M8SamplerParam.CUTOFF), 0x40)

    def test_sampler_round_trip_serialization_with_enum_names(self):
        """Test sampler round-trip: to_dict(enum_mode='name') -> from_dict() -> to_dict()."""
        # Create original sampler
        original = M8Sampler(name="RoundTrip", sample_path="/test.wav")
        original.set(M8SamplerParam.PLAY_MODE, M8PlayMode.REV_PP)
        original.set(M8SamplerParam.FILTER_TYPE, M8FilterType.BANDPASS)
        original.set(M8SamplerParam.LIMIT, M8LimiterType.FOLD)
        original.set(M8SamplerParam.CUTOFF, 0x60)
        original.set(M8SamplerParam.RESONANCE, 0xA0)

        # Export with enum_mode='name'
        dict_with_names = original.to_dict(enum_mode='name')

        # Verify enum names are strings
        self.assertEqual(dict_with_names['params']['PLAY_MODE'], 'REV_PP')
        self.assertEqual(dict_with_names['params']['FILTER_TYPE'], 'BANDPASS')
        self.assertEqual(dict_with_names['params']['LIMIT'], 'FOLD')

        # Import from dict
        restored = M8Sampler.from_dict(dict_with_names)

        # Verify all values match
        self.assertEqual(restored.name, original.name)
        self.assertEqual(restored.sample_path, original.sample_path)
        self.assertEqual(restored.get(M8SamplerParam.PLAY_MODE), original.get(M8SamplerParam.PLAY_MODE))
        self.assertEqual(restored.get(M8SamplerParam.FILTER_TYPE), original.get(M8SamplerParam.FILTER_TYPE))
        self.assertEqual(restored.get(M8SamplerParam.LIMIT), original.get(M8SamplerParam.LIMIT))
        self.assertEqual(restored.get(M8SamplerParam.CUTOFF), original.get(M8SamplerParam.CUTOFF))
        self.assertEqual(restored.get(M8SamplerParam.RESONANCE), original.get(M8SamplerParam.RESONANCE))

        # Export again with enum_mode='name'
        dict_restored = restored.to_dict(enum_mode='name')

        # Verify enum names are preserved
        self.assertEqual(dict_restored['params']['PLAY_MODE'], 'REV_PP')
        self.assertEqual(dict_restored['params']['FILTER_TYPE'], 'BANDPASS')
        self.assertEqual(dict_restored['params']['LIMIT'], 'FOLD')


if __name__ == '__main__':
    unittest.main()
