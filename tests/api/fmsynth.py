import unittest
from m8.api.instruments.fmsynth import (
    M8FMSynth, DEFAULT_PARAMETERS, M8FMSynthParam,
    M8FMAlgo, M8FMWave, M8FMSynthModDest
)
from m8.api.instrument import MODULATORS_OFFSET, M8FilterType, M8LimiterType
from m8.api.modulator import M8Modulators, M8ModulatorType


class TestM8FMSynth(unittest.TestCase):
    def setUp(self):
        # Define FM synth-specific test parameters
        self.test_name = "TestFM"

    def test_constructor_and_defaults(self):
        """Test default constructor and default parameter values."""
        fmsynth = M8FMSynth()

        # Check type is set correctly
        self.assertEqual(fmsynth.get(M8FMSynthParam.TYPE), 0x04)  # FMSYNTH type_id is 4

        # Check default parameters
        self.assertEqual(fmsynth.name, "")

        # Check non-zero defaults using generic get
        self.assertEqual(fmsynth.get(M8FMSynthParam.FINE_TUNE), 0x80)  # FINE_TUNE centered
        self.assertEqual(fmsynth.get(M8FMSynthParam.CUTOFF), 0xFF)     # CUTOFF fully open
        self.assertEqual(fmsynth.get(M8FMSynthParam.PAN), 0x80)        # PAN centered
        self.assertEqual(fmsynth.get(M8FMSynthParam.DRY), 0xC0)        # DRY default

    def test_constructor_with_name(self):
        """Test constructor with name parameter."""
        fmsynth = M8FMSynth(name=self.test_name)

        # Check parameters
        self.assertEqual(fmsynth.name, self.test_name)
        self.assertEqual(fmsynth.get(M8FMSynthParam.TYPE), 0x04)

    def test_set_and_get_parameters(self):
        """Test setting and getting FM synth parameters."""
        fmsynth = M8FMSynth(name=self.test_name)

        # Test algorithm
        fmsynth.set(M8FMSynthParam.ALGO, M8FMAlgo.A_PLUS_B_PLUS_C_PLUS_D)
        self.assertEqual(fmsynth.get(M8FMSynthParam.ALGO), M8FMAlgo.A_PLUS_B_PLUS_C_PLUS_D)
        self.assertEqual(fmsynth.get(M8FMSynthParam.ALGO), 0x0B)

        # Test operator shapes
        fmsynth.set(M8FMSynthParam.OP_A_SHAPE, M8FMWave.SIN)
        fmsynth.set(M8FMSynthParam.OP_B_SHAPE, M8FMWave.SW2)
        fmsynth.set(M8FMSynthParam.OP_C_SHAPE, M8FMWave.SW3)
        fmsynth.set(M8FMSynthParam.OP_D_SHAPE, M8FMWave.SW4)

        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_A_SHAPE), M8FMWave.SIN)
        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_B_SHAPE), M8FMWave.SW2)
        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_C_SHAPE), M8FMWave.SW3)
        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_D_SHAPE), M8FMWave.SW4)

        # Test operator ratios
        fmsynth.set(M8FMSynthParam.OP_A_RATIO, 25)  # 25 decimal
        fmsynth.set(M8FMSynthParam.OP_B_RATIO, 50)
        fmsynth.set(M8FMSynthParam.OP_C_RATIO, 75)
        fmsynth.set(M8FMSynthParam.OP_D_RATIO, 0)

        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_A_RATIO), 25)
        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_B_RATIO), 50)
        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_C_RATIO), 75)
        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_D_RATIO), 0)

        # Test operator levels and feedback
        fmsynth.set(M8FMSynthParam.OP_A_LEVEL, 0x10)
        fmsynth.set(M8FMSynthParam.OP_A_FEEDBACK, 0x20)
        fmsynth.set(M8FMSynthParam.OP_B_LEVEL, 0x30)
        fmsynth.set(M8FMSynthParam.OP_B_FEEDBACK, 0x40)

        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_A_LEVEL), 0x10)
        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_A_FEEDBACK), 0x20)
        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_B_LEVEL), 0x30)
        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_B_FEEDBACK), 0x40)

        # Test filter parameters
        fmsynth.set(M8FMSynthParam.FILTER_TYPE, M8FilterType.LOWPASS)
        fmsynth.set(M8FMSynthParam.CUTOFF, 0xB0)
        fmsynth.set(M8FMSynthParam.RESONANCE, 0xC0)

        self.assertEqual(fmsynth.get(M8FMSynthParam.FILTER_TYPE), M8FilterType.LOWPASS)
        self.assertEqual(fmsynth.get(M8FMSynthParam.CUTOFF), 0xB0)
        self.assertEqual(fmsynth.get(M8FMSynthParam.RESONANCE), 0xC0)

        # Test mixer parameters
        fmsynth.set(M8FMSynthParam.AMP, 0x10)
        fmsynth.set(M8FMSynthParam.LIMIT, M8LimiterType.SIN)
        fmsynth.set(M8FMSynthParam.PAN, 0x80)
        fmsynth.set(M8FMSynthParam.DRY, 0xC0)
        fmsynth.set(M8FMSynthParam.CHORUS_SEND, 0x90)
        fmsynth.set(M8FMSynthParam.DELAY_SEND, 0x40)
        fmsynth.set(M8FMSynthParam.REVERB_SEND, 0xB0)

        self.assertEqual(fmsynth.get(M8FMSynthParam.AMP), 0x10)
        self.assertEqual(fmsynth.get(M8FMSynthParam.LIMIT), M8LimiterType.SIN)
        self.assertEqual(fmsynth.get(M8FMSynthParam.PAN), 0x80)
        self.assertEqual(fmsynth.get(M8FMSynthParam.DRY), 0xC0)
        self.assertEqual(fmsynth.get(M8FMSynthParam.CHORUS_SEND), 0x90)
        self.assertEqual(fmsynth.get(M8FMSynthParam.DELAY_SEND), 0x40)
        self.assertEqual(fmsynth.get(M8FMSynthParam.REVERB_SEND), 0xB0)

    def test_binary_serialization(self):
        """Test write/read round-trip preserves all parameters."""
        # Create FM synth with custom parameters
        fmsynth = M8FMSynth(name="ACIDFM")
        fmsynth.set(M8FMSynthParam.ALGO, M8FMAlgo.A_B_C_D)
        fmsynth.set(M8FMSynthParam.OP_A_SHAPE, M8FMWave.SAW)
        fmsynth.set(M8FMSynthParam.OP_B_SHAPE, M8FMWave.SQR)
        fmsynth.set(M8FMSynthParam.OP_A_RATIO, 100)
        fmsynth.set(M8FMSynthParam.OP_B_RATIO, 200)
        fmsynth.set(M8FMSynthParam.CUTOFF, 0x20)
        fmsynth.set(M8FMSynthParam.RESONANCE, 0xC0)
        fmsynth.set(M8FMSynthParam.CHORUS_SEND, 0x80)

        # Write to binary
        binary = fmsynth.write()

        # Read it back
        read_fmsynth = M8FMSynth.read(binary)

        # Check all parameters were preserved
        self.assertEqual(read_fmsynth.name, "ACIDFM")
        self.assertEqual(read_fmsynth.get(M8FMSynthParam.ALGO), M8FMAlgo.A_B_C_D)
        self.assertEqual(read_fmsynth.get(M8FMSynthParam.OP_A_SHAPE), M8FMWave.SAW)
        self.assertEqual(read_fmsynth.get(M8FMSynthParam.OP_B_SHAPE), M8FMWave.SQR)
        self.assertEqual(read_fmsynth.get(M8FMSynthParam.OP_A_RATIO), 100)
        self.assertEqual(read_fmsynth.get(M8FMSynthParam.OP_B_RATIO), 200)
        self.assertEqual(read_fmsynth.get(M8FMSynthParam.CUTOFF), 0x20)
        self.assertEqual(read_fmsynth.get(M8FMSynthParam.RESONANCE), 0xC0)
        self.assertEqual(read_fmsynth.get(M8FMSynthParam.CHORUS_SEND), 0x80)

    def test_clone(self):
        """Test cloning creates independent copy."""
        # Create FM synth with custom parameters
        original = M8FMSynth(name=self.test_name)
        original.set(M8FMSynthParam.ALGO, M8FMAlgo.A_PLUS_B_PLUS_C_PLUS_D)
        original.set(M8FMSynthParam.OP_A_SHAPE, M8FMWave.SIN)
        original.set(M8FMSynthParam.OP_A_RATIO, 32)
        original.set(M8FMSynthParam.CUTOFF, 0x20)
        original.set(M8FMSynthParam.RESONANCE, 0xC0)

        # Clone it
        cloned = original.clone()

        # Check they are different objects
        self.assertIsNot(cloned, original)

        # Check all values match
        self.assertEqual(cloned.name, original.name)
        self.assertEqual(cloned.get(M8FMSynthParam.ALGO), original.get(M8FMSynthParam.ALGO))
        self.assertEqual(cloned.get(M8FMSynthParam.OP_A_SHAPE), original.get(M8FMSynthParam.OP_A_SHAPE))
        self.assertEqual(cloned.get(M8FMSynthParam.OP_A_RATIO), original.get(M8FMSynthParam.OP_A_RATIO))
        self.assertEqual(cloned.get(M8FMSynthParam.CUTOFF), original.get(M8FMSynthParam.CUTOFF))
        self.assertEqual(cloned.get(M8FMSynthParam.RESONANCE), original.get(M8FMSynthParam.RESONANCE))

        # Modify clone and ensure original unchanged
        cloned.set(M8FMSynthParam.CUTOFF, 0xFF)
        self.assertEqual(cloned.get(M8FMSynthParam.CUTOFF), 0xFF)
        self.assertEqual(original.get(M8FMSynthParam.CUTOFF), 0x20)

    def test_modulators_initialized(self):
        """Test that modulators are initialized with defaults."""
        fmsynth = M8FMSynth()

        # Check modulators exist
        self.assertIsInstance(fmsynth.modulators, M8Modulators)

        # Check 4 modulators
        self.assertEqual(len(fmsynth.modulators), 4)

        # Check all modulators are initialized (not None)
        for i in range(4):
            self.assertIsNotNone(fmsynth.modulators[i])

    def test_modulator_destinations(self):
        """Test FM synth specific modulation destinations."""
        fmsynth = M8FMSynth()

        # Test setting modulator destinations
        fmsynth.modulators[0].destination = M8FMSynthModDest.VOLUME
        fmsynth.modulators[1].destination = M8FMSynthModDest.PITCH
        fmsynth.modulators[2].destination = M8FMSynthModDest.CUTOFF
        fmsynth.modulators[3].destination = M8FMSynthModDest.MOD1

        self.assertEqual(fmsynth.modulators[0].destination, M8FMSynthModDest.VOLUME)
        self.assertEqual(fmsynth.modulators[1].destination, M8FMSynthModDest.PITCH)
        self.assertEqual(fmsynth.modulators[2].destination, M8FMSynthModDest.CUTOFF)
        self.assertEqual(fmsynth.modulators[3].destination, M8FMSynthModDest.MOD1)

    def test_fm_algo_enum(self):
        """Test FM algorithm enum values."""
        # Test basic algorithm values
        self.assertEqual(M8FMAlgo.A_B_C_D, 0)
        self.assertEqual(M8FMAlgo.AB_C_D, 1)
        self.assertEqual(M8FMAlgo.A_PLUS_B_PLUS_C_PLUS_D, 11)

        # Test all 12 algorithms exist
        for i in range(12):
            # Should not raise
            algo = M8FMAlgo(i)
            self.assertIsInstance(algo, M8FMAlgo)

    def test_fm_wave_enum(self):
        """Test FM wave shape enum values."""
        # Test basic waveforms
        self.assertEqual(M8FMWave.SIN, 0)
        self.assertEqual(M8FMWave.SW2, 1)
        self.assertEqual(M8FMWave.SW3, 2)
        self.assertEqual(M8FMWave.SW4, 3)
        self.assertEqual(M8FMWave.TRI, 6)
        self.assertEqual(M8FMWave.SAW, 7)
        self.assertEqual(M8FMWave.SQR, 8)

        # Test noise variants
        self.assertEqual(M8FMWave.NOI, 11)
        self.assertEqual(M8FMWave.NLP, 12)
        self.assertEqual(M8FMWave.NHP, 13)
        self.assertEqual(M8FMWave.NBP, 14)

        # Test extended waveforms exist
        self.assertEqual(M8FMWave.W09, 16)
        self.assertEqual(M8FMWave.W45, 76)

    def test_fm_modulation_destinations(self):
        """Test FM synth modulation destination enum."""
        # Test standard destinations
        self.assertEqual(M8FMSynthModDest.OFF, 0x00)
        self.assertEqual(M8FMSynthModDest.VOLUME, 0x01)
        self.assertEqual(M8FMSynthModDest.PITCH, 0x02)
        self.assertEqual(M8FMSynthModDest.CUTOFF, 0x07)
        self.assertEqual(M8FMSynthModDest.RES, 0x08)
        self.assertEqual(M8FMSynthModDest.AMP, 0x09)
        self.assertEqual(M8FMSynthModDest.PAN, 0x0A)

        # Test FM-specific mod destinations
        self.assertEqual(M8FMSynthModDest.MOD1, 0x03)
        self.assertEqual(M8FMSynthModDest.MOD2, 0x04)
        self.assertEqual(M8FMSynthModDest.MOD3, 0x05)
        self.assertEqual(M8FMSynthModDest.MOD4, 0x06)

        # Test extended destinations
        self.assertEqual(M8FMSynthModDest.MOD_AMT, 0x0B)
        self.assertEqual(M8FMSynthModDest.MOD_RATE, 0x0C)
        self.assertEqual(M8FMSynthModDest.MOD_BOTH, 0x0D)
        self.assertEqual(M8FMSynthModDest.MOD_BINV, 0x0E)

    def test_to_dict_value_mode(self):
        """Test dictionary serialization with numeric values."""
        fmsynth = M8FMSynth(name="DICT-TEST")
        fmsynth.set(M8FMSynthParam.ALGO, M8FMAlgo.A_PLUS_B_PLUS_C_PLUS_D)
        fmsynth.set(M8FMSynthParam.OP_A_SHAPE, M8FMWave.SIN)
        fmsynth.set(M8FMSynthParam.OP_B_SHAPE, M8FMWave.SAW)

        result = fmsynth.to_dict(enum_mode='value')

        self.assertEqual(result['name'], "DICT-TEST")
        self.assertEqual(result['params']['ALGO'], 11)  # A_PLUS_B_PLUS_C_PLUS_D
        self.assertEqual(result['params']['OP_A_SHAPE'], 0)  # SIN
        self.assertEqual(result['params']['OP_B_SHAPE'], 7)  # SAW

    def test_to_dict_name_mode(self):
        """Test dictionary serialization with enum names."""
        fmsynth = M8FMSynth(name="ENUM-TEST")
        fmsynth.set(M8FMSynthParam.ALGO, M8FMAlgo.A_B_C_D)
        fmsynth.set(M8FMSynthParam.OP_A_SHAPE, M8FMWave.SIN)
        fmsynth.set(M8FMSynthParam.FILTER_TYPE, M8FilterType.LOWPASS)

        result = fmsynth.to_dict(enum_mode='name')

        self.assertEqual(result['name'], "ENUM-TEST")
        self.assertEqual(result['params']['ALGO'], 'A_B_C_D')
        self.assertEqual(result['params']['OP_A_SHAPE'], 'SIN')
        self.assertEqual(result['params']['FILTER_TYPE'], 'LOWPASS')

    def test_from_dict_numeric_values(self):
        """Test creating FM synth from dictionary with numeric values."""
        params_dict = {
            'name': 'FROM-DICT',
            'params': {
                'ALGO': 11,
                'OP_A_SHAPE': 0,
                'OP_B_SHAPE': 7,
                'OP_A_RATIO': 25,
                'OP_B_RATIO': 50,
                'CUTOFF': 0xB0,
                'RESONANCE': 0xC0,
            },
            'modulators': []
        }

        fmsynth = M8FMSynth.from_dict(params_dict)

        self.assertEqual(fmsynth.name, "FROM-DICT")
        self.assertEqual(fmsynth.get(M8FMSynthParam.ALGO), 11)
        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_A_SHAPE), 0)
        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_B_SHAPE), 7)
        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_A_RATIO), 25)
        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_B_RATIO), 50)

    def test_from_dict_enum_names(self):
        """Test creating FM synth from dictionary with enum names."""
        params_dict = {
            'name': 'FROM-ENUM',
            'params': {
                'ALGO': 'A_PLUS_B_PLUS_C_PLUS_D',
                'OP_A_SHAPE': 'SIN',
                'OP_B_SHAPE': 'SAW',
                'FILTER_TYPE': 'LOWPASS',
                'LIMIT': 'SIN',
            },
            'modulators': []
        }

        fmsynth = M8FMSynth.from_dict(params_dict)

        self.assertEqual(fmsynth.name, "FROM-ENUM")
        self.assertEqual(fmsynth.get(M8FMSynthParam.ALGO), M8FMAlgo.A_PLUS_B_PLUS_C_PLUS_D)
        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_A_SHAPE), M8FMWave.SIN)
        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_B_SHAPE), M8FMWave.SAW)
        self.assertEqual(fmsynth.get(M8FMSynthParam.FILTER_TYPE), M8FilterType.LOWPASS)

    def test_round_trip_dict_serialization(self):
        """Test to_dict() and from_dict() round-trip."""
        original = M8FMSynth(name="ROUND-TRIP")
        original.set(M8FMSynthParam.ALGO, M8FMAlgo.AB_C_D)
        original.set(M8FMSynthParam.OP_A_SHAPE, M8FMWave.TRI)
        original.set(M8FMSynthParam.OP_A_RATIO, 64)
        original.set(M8FMSynthParam.CUTOFF, 0x40)

        # Convert to dict and back
        params_dict = original.to_dict(enum_mode='name')
        restored = M8FMSynth.from_dict(params_dict)

        # Verify parameters match
        self.assertEqual(restored.name, original.name)
        self.assertEqual(
            restored.get(M8FMSynthParam.ALGO),
            original.get(M8FMSynthParam.ALGO)
        )
        self.assertEqual(
            restored.get(M8FMSynthParam.OP_A_SHAPE),
            original.get(M8FMSynthParam.OP_A_SHAPE)
        )
        self.assertEqual(
            restored.get(M8FMSynthParam.OP_A_RATIO),
            original.get(M8FMSynthParam.OP_A_RATIO)
        )
        self.assertEqual(
            restored.get(M8FMSynthParam.CUTOFF),
            original.get(M8FMSynthParam.CUTOFF)
        )


    def test_operator_mod_routing(self):
        """Test operator modulation routing (mod_a/mod_b)."""
        from m8.api.instruments.fmsynth import M8FMOperatorModDest

        fmsynth = M8FMSynth()

        # Set operator A mod_a to MOD1_LEV (1/LEV)
        fmsynth.set(M8FMSynthParam.OP_A_MOD_A, M8FMOperatorModDest.MOD1_LEV)
        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_A_MOD_A), M8FMOperatorModDest.MOD1_LEV)

        # Set operator B mod_a to MOD2_RAT (2/RAT)
        fmsynth.set(M8FMSynthParam.OP_B_MOD_A, M8FMOperatorModDest.MOD2_RAT)
        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_B_MOD_A), M8FMOperatorModDest.MOD2_RAT)

        # Set operator C mod_a to MOD3_PIT (3/PIT)
        fmsynth.set(M8FMSynthParam.OP_C_MOD_A, M8FMOperatorModDest.MOD3_PIT)
        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_C_MOD_A), M8FMOperatorModDest.MOD3_PIT)

        # Set operator D mod_a to MOD4_FBK (4/FBK)
        fmsynth.set(M8FMSynthParam.OP_D_MOD_A, M8FMOperatorModDest.MOD4_FBK)
        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_D_MOD_A), M8FMOperatorModDest.MOD4_FBK)

        # Test mod_b parameters
        fmsynth.set(M8FMSynthParam.OP_A_MOD_B, M8FMOperatorModDest.MOD1_RAT)
        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_A_MOD_B), M8FMOperatorModDest.MOD1_RAT)

        # Test OFF value
        fmsynth.set(M8FMSynthParam.OP_B_MOD_B, M8FMOperatorModDest.OFF)
        self.assertEqual(fmsynth.get(M8FMSynthParam.OP_B_MOD_B), M8FMOperatorModDest.OFF)

    def test_operator_mod_routing_binary(self):
        """Test operator modulation routing binary serialization."""
        from m8.api.instruments.fmsynth import M8FMOperatorModDest

        fmsynth = M8FMSynth()

        # Set distinctive mod_a values
        fmsynth.set(M8FMSynthParam.OP_A_MOD_A, M8FMOperatorModDest.MOD1_LEV)  # 0x01
        fmsynth.set(M8FMSynthParam.OP_B_MOD_A, M8FMOperatorModDest.MOD2_RAT)  # 0x06
        fmsynth.set(M8FMSynthParam.OP_C_MOD_A, M8FMOperatorModDest.MOD3_PIT)  # 0x0B
        fmsynth.set(M8FMSynthParam.OP_D_MOD_A, M8FMOperatorModDest.MOD4_FBK)  # 0x10

        # Serialize to binary
        binary = fmsynth.write()

        # Check mod_a bytes at offsets 0x27-0x2A (39-42)
        self.assertEqual(binary[39], 0x01)  # OP_A_MOD_A
        self.assertEqual(binary[40], 0x06)  # OP_B_MOD_A
        self.assertEqual(binary[41], 0x0B)  # OP_C_MOD_A
        self.assertEqual(binary[42], 0x10)  # OP_D_MOD_A

        # Check mod_b bytes at offsets 0x2B-0x2E (43-46) - should be default (0x00)
        self.assertEqual(binary[43], 0x00)  # OP_A_MOD_B
        self.assertEqual(binary[44], 0x00)  # OP_B_MOD_B
        self.assertEqual(binary[45], 0x00)  # OP_C_MOD_B
        self.assertEqual(binary[46], 0x00)  # OP_D_MOD_B


if __name__ == '__main__':
    unittest.main()
