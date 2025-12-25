import unittest
from m8.api.modulator import (
    M8Modulator, M8Modulators,
    M8ModulatorType, M8LFOShape, M8LFOTriggerMode,
    BLOCK_SIZE, BLOCK_COUNT,
    DEFAULT_AMOUNT, DEFAULT_DESTINATION, DEFAULT_AHD_DECAY, DEFAULT_LFO_FREQUENCY,
    AHD_ATTACK_OFFSET, AHD_HOLD_OFFSET, AHD_DECAY_OFFSET,
    LFO_OSCILLATOR_OFFSET, LFO_TRIGGER_OFFSET, LFO_FREQUENCY_OFFSET
)


class TestM8Modulator(unittest.TestCase):
    """Tests for M8Modulator class."""

    def test_constructor_ahd_envelope(self):
        """Test default constructor creates AHD envelope with correct defaults."""
        mod = M8Modulator(mod_type=0)  # AHD

        # Check type and destination
        self.assertEqual(mod.mod_type, 0)
        self.assertEqual(mod.destination, DEFAULT_DESTINATION)

        # Check amount
        self.assertEqual(mod.amount, DEFAULT_AMOUNT)

        # Check AHD-specific defaults
        self.assertEqual(mod.get(AHD_DECAY_OFFSET), DEFAULT_AHD_DECAY)

    def test_constructor_lfo(self):
        """Test constructor creates LFO with correct defaults."""
        mod = M8Modulator(mod_type=3)  # LFO

        # Check type and destination
        self.assertEqual(mod.mod_type, 3)
        self.assertEqual(mod.destination, DEFAULT_DESTINATION)

        # Check amount
        self.assertEqual(mod.amount, DEFAULT_AMOUNT)

        # Check LFO-specific defaults
        self.assertEqual(mod.get(LFO_FREQUENCY_OFFSET), DEFAULT_LFO_FREQUENCY)

    def test_type_destination_nibbles(self):
        """Test that type and destination are stored in nibbles correctly."""
        mod = M8Modulator(mod_type=3)  # LFO

        # Set destination
        mod.destination = 5

        # Check byte 0 contains both nibbles
        self.assertEqual(mod.get(0), 0x35)  # 3 in high nibble, 5 in low nibble
        self.assertEqual(mod.mod_type, 3)
        self.assertEqual(mod.destination, 5)

        # Change type
        mod.mod_type = 0  # AHD

        # Check destination is preserved
        self.assertEqual(mod.get(0), 0x05)
        self.assertEqual(mod.mod_type, 0)
        self.assertEqual(mod.destination, 5)

    def test_amount_property(self):
        """Test amount property getter and setter."""
        mod = M8Modulator()

        # Default amount
        self.assertEqual(mod.amount, DEFAULT_AMOUNT)

        # Set amount
        mod.amount = 0x80
        self.assertEqual(mod.amount, 0x80)
        self.assertEqual(mod.get(1), 0x80)

    def test_get_set_parameters(self):
        """Test generic get/set for all parameters."""
        mod = M8Modulator(mod_type=0)  # AHD

        # Set AHD parameters
        mod.set(AHD_ATTACK_OFFSET, 0x40)
        mod.set(AHD_HOLD_OFFSET, 0x50)
        mod.set(AHD_DECAY_OFFSET, 0x60)

        # Verify
        self.assertEqual(mod.get(AHD_ATTACK_OFFSET), 0x40)
        self.assertEqual(mod.get(AHD_HOLD_OFFSET), 0x50)
        self.assertEqual(mod.get(AHD_DECAY_OFFSET), 0x60)

    def test_write(self):
        """Test binary serialization."""
        mod = M8Modulator(mod_type=3)  # LFO
        mod.destination = 5
        mod.amount = 0x80
        mod.set(LFO_OSCILLATOR_OFFSET, 0x01)
        mod.set(LFO_TRIGGER_OFFSET, 0x02)
        mod.set(LFO_FREQUENCY_OFFSET, 0x30)

        binary = mod.write()

        # Check length
        self.assertEqual(len(binary), BLOCK_SIZE)

        # Check values
        self.assertEqual(binary[0], 0x35)  # Type 3, dest 5
        self.assertEqual(binary[1], 0x80)  # Amount
        self.assertEqual(binary[2], 0x01)  # Oscillator
        self.assertEqual(binary[3], 0x02)  # Trigger
        self.assertEqual(binary[4], 0x30)  # Frequency

    def test_read(self):
        """Test binary deserialization."""
        # Create test data
        test_data = bytearray([
            0x35,  # Type 3 (LFO), destination 5
            0x80,  # Amount
            0x01,  # Oscillator
            0x02,  # Trigger
            0x30,  # Frequency
            0x00   # Padding
        ])

        mod = M8Modulator.read(test_data)

        # Verify
        self.assertEqual(mod.mod_type, 3)
        self.assertEqual(mod.destination, 5)
        self.assertEqual(mod.amount, 0x80)
        self.assertEqual(mod.get(LFO_OSCILLATOR_OFFSET), 0x01)
        self.assertEqual(mod.get(LFO_TRIGGER_OFFSET), 0x02)
        self.assertEqual(mod.get(LFO_FREQUENCY_OFFSET), 0x30)

    def test_clone(self):
        """Test cloning creates independent copy."""
        original = M8Modulator(mod_type=3)
        original.destination = 5
        original.amount = 0x80
        original.set(LFO_FREQUENCY_OFFSET, 0x30)

        cloned = original.clone()

        # Check they are different objects
        self.assertIsNot(cloned, original)

        # Check values match
        self.assertEqual(cloned.mod_type, original.mod_type)
        self.assertEqual(cloned.destination, original.destination)
        self.assertEqual(cloned.amount, original.amount)
        self.assertEqual(cloned.get(LFO_FREQUENCY_OFFSET), original.get(LFO_FREQUENCY_OFFSET))

        # Modify clone
        cloned.destination = 7
        cloned.set(LFO_FREQUENCY_OFFSET, 0x40)

        # Check original unchanged
        self.assertEqual(original.destination, 5)
        self.assertEqual(original.get(LFO_FREQUENCY_OFFSET), 0x30)

    def test_read_write_consistency(self):
        """Test round-trip read/write consistency."""
        original = M8Modulator(mod_type=0)  # AHD
        original.destination = 3
        original.amount = 0x90
        original.set(AHD_ATTACK_OFFSET, 0x20)
        original.set(AHD_HOLD_OFFSET, 0x30)
        original.set(AHD_DECAY_OFFSET, 0x40)

        # Write and read back
        binary = original.write()
        deserialized = M8Modulator.read(binary)

        # Verify all values preserved
        self.assertEqual(deserialized.mod_type, original.mod_type)
        self.assertEqual(deserialized.destination, original.destination)
        self.assertEqual(deserialized.amount, original.amount)
        self.assertEqual(deserialized.get(AHD_ATTACK_OFFSET), original.get(AHD_ATTACK_OFFSET))
        self.assertEqual(deserialized.get(AHD_HOLD_OFFSET), original.get(AHD_HOLD_OFFSET))
        self.assertEqual(deserialized.get(AHD_DECAY_OFFSET), original.get(AHD_DECAY_OFFSET))


class TestM8Modulators(unittest.TestCase):
    """Tests for M8Modulators collection class."""

    def test_constructor(self):
        """Test constructor creates 4 modulators with correct types."""
        modulators = M8Modulators()

        # Check count
        self.assertEqual(len(modulators), BLOCK_COUNT)
        self.assertEqual(len(modulators), 4)

        # Check default types: 0, 0, 3, 3 (2 AHD, 2 LFO)
        self.assertEqual(modulators[0].mod_type, 0)  # AHD
        self.assertEqual(modulators[1].mod_type, 0)  # AHD
        self.assertEqual(modulators[2].mod_type, 3)  # LFO
        self.assertEqual(modulators[3].mod_type, 3)  # LFO

        # Check all have default amount
        for mod in modulators:
            self.assertEqual(mod.amount, DEFAULT_AMOUNT)

        # Check type-specific defaults
        self.assertEqual(modulators[0].get(AHD_DECAY_OFFSET), DEFAULT_AHD_DECAY)
        self.assertEqual(modulators[1].get(AHD_DECAY_OFFSET), DEFAULT_AHD_DECAY)
        self.assertEqual(modulators[2].get(LFO_FREQUENCY_OFFSET), DEFAULT_LFO_FREQUENCY)
        self.assertEqual(modulators[3].get(LFO_FREQUENCY_OFFSET), DEFAULT_LFO_FREQUENCY)

    def test_write(self):
        """Test writing modulators collection to binary."""
        modulators = M8Modulators()

        # Customize first modulator
        modulators[0].destination = 1
        modulators[0].amount = 0x80
        modulators[0].set(AHD_ATTACK_OFFSET, 0x20)

        binary = modulators.write()

        # Check total size
        self.assertEqual(len(binary), BLOCK_COUNT * BLOCK_SIZE)
        self.assertEqual(len(binary), 24)  # 4 * 6

        # Check first modulator data
        self.assertEqual(binary[0], 0x01)  # Type 0, dest 1
        self.assertEqual(binary[1], 0x80)  # Amount
        self.assertEqual(binary[2], 0x20)  # Attack

    def test_read(self):
        """Test reading modulators collection from binary."""
        # Create test data for 4 modulators
        test_data = bytearray()

        # Modulator 0: AHD with custom params
        test_data.extend([0x01, 0xFF, 0x20, 0x30, 0x80, 0x00])

        # Modulator 1: AHD default
        test_data.extend([0x00, 0xFF, 0x00, 0x00, 0x80, 0x00])

        # Modulator 2: LFO with custom params
        test_data.extend([0x35, 0xFF, 0x01, 0x02, 0x10, 0x00])

        # Modulator 3: LFO default
        test_data.extend([0x30, 0xFF, 0x00, 0x00, 0x10, 0x00])

        modulators = M8Modulators.read(test_data)

        # Check count
        self.assertEqual(len(modulators), 4)

        # Check modulator 0
        self.assertEqual(modulators[0].mod_type, 0)
        self.assertEqual(modulators[0].destination, 1)
        self.assertEqual(modulators[0].amount, 0xFF)
        self.assertEqual(modulators[0].get(AHD_ATTACK_OFFSET), 0x20)

        # Check modulator 2
        self.assertEqual(modulators[2].mod_type, 3)
        self.assertEqual(modulators[2].destination, 5)
        self.assertEqual(modulators[2].get(LFO_OSCILLATOR_OFFSET), 0x01)

    def test_clone(self):
        """Test cloning modulators collection."""
        original = M8Modulators()
        original[0].destination = 1
        original[0].set(AHD_ATTACK_OFFSET, 0x20)

        cloned = original.clone()

        # Check different objects
        self.assertIsNot(cloned, original)
        self.assertIsNot(cloned[0], original[0])

        # Check values match
        self.assertEqual(cloned[0].destination, original[0].destination)
        self.assertEqual(cloned[0].get(AHD_ATTACK_OFFSET), original[0].get(AHD_ATTACK_OFFSET))

        # Modify clone
        cloned[0].destination = 2
        cloned[0].set(AHD_ATTACK_OFFSET, 0x30)

        # Check original unchanged
        self.assertEqual(original[0].destination, 1)
        self.assertEqual(original[0].get(AHD_ATTACK_OFFSET), 0x20)

    def test_read_write_consistency(self):
        """Test round-trip read/write consistency."""
        original = M8Modulators()

        # Customize modulators
        original[0].destination = 1
        original[0].set(AHD_ATTACK_OFFSET, 0x20)
        original[0].set(AHD_HOLD_OFFSET, 0x30)

        original[2].destination = 5
        original[2].set(LFO_OSCILLATOR_OFFSET, 0x01)
        original[2].set(LFO_FREQUENCY_OFFSET, 0x25)

        # Write and read back
        binary = original.write()
        deserialized = M8Modulators.read(binary)

        # Verify modulator 0
        self.assertEqual(deserialized[0].mod_type, original[0].mod_type)
        self.assertEqual(deserialized[0].destination, original[0].destination)
        self.assertEqual(deserialized[0].get(AHD_ATTACK_OFFSET), original[0].get(AHD_ATTACK_OFFSET))
        self.assertEqual(deserialized[0].get(AHD_HOLD_OFFSET), original[0].get(AHD_HOLD_OFFSET))

        # Verify modulator 2
        self.assertEqual(deserialized[2].mod_type, original[2].mod_type)
        self.assertEqual(deserialized[2].destination, original[2].destination)
        self.assertEqual(deserialized[2].get(LFO_OSCILLATOR_OFFSET), original[2].get(LFO_OSCILLATOR_OFFSET))
        self.assertEqual(deserialized[2].get(LFO_FREQUENCY_OFFSET), original[2].get(LFO_FREQUENCY_OFFSET))


class TestModulatorEnums(unittest.TestCase):
    """Tests for modulator enum classes."""

    def test_m8_modulator_type_values(self):
        """Test M8ModulatorType enum has correct values."""
        self.assertEqual(M8ModulatorType.AHD_ENVELOPE, 0)
        self.assertEqual(M8ModulatorType.ADSR_ENVELOPE, 1)
        self.assertEqual(M8ModulatorType.DRUM_ENVELOPE, 2)
        self.assertEqual(M8ModulatorType.LFO, 3)
        self.assertEqual(M8ModulatorType.TRIG_ENVELOPE, 4)
        self.assertEqual(M8ModulatorType.TRACKING_ENVELOPE, 5)

    def test_m8_modulator_type_with_modulator(self):
        """Test M8ModulatorType enum works with M8Modulator."""
        # Test with AHD
        mod_ahd = M8Modulator(mod_type=M8ModulatorType.AHD_ENVELOPE)
        self.assertEqual(mod_ahd.mod_type, 0)
        self.assertEqual(mod_ahd.mod_type, M8ModulatorType.AHD_ENVELOPE)

        # Test with LFO
        mod_lfo = M8Modulator(mod_type=M8ModulatorType.LFO)
        self.assertEqual(mod_lfo.mod_type, 3)
        self.assertEqual(mod_lfo.mod_type, M8ModulatorType.LFO)

        # Test with ADSR
        mod_adsr = M8Modulator(mod_type=M8ModulatorType.ADSR_ENVELOPE)
        self.assertEqual(mod_adsr.mod_type, 1)
        self.assertEqual(mod_adsr.mod_type, M8ModulatorType.ADSR_ENVELOPE)

    def test_m8_lfo_shape_values(self):
        """Test M8LFOShape enum has correct values."""
        # Basic shapes (0-9)
        self.assertEqual(M8LFOShape.TRI, 0)
        self.assertEqual(M8LFOShape.SIN, 1)
        self.assertEqual(M8LFOShape.RAMP_DOWN, 2)
        self.assertEqual(M8LFOShape.RAMP_UP, 3)
        self.assertEqual(M8LFOShape.EXP_DN, 4)
        self.assertEqual(M8LFOShape.EXP_UP, 5)
        self.assertEqual(M8LFOShape.SQR_DN, 6)
        self.assertEqual(M8LFOShape.SQR_UP, 7)
        self.assertEqual(M8LFOShape.RANDOM, 8)
        self.assertEqual(M8LFOShape.DRUNK, 9)

        # Triggered shapes (10-19)
        self.assertEqual(M8LFOShape.TRI_T, 10)
        self.assertEqual(M8LFOShape.SIN_T, 11)
        self.assertEqual(M8LFOShape.RAMPD_T, 12)
        self.assertEqual(M8LFOShape.RAMPU_T, 13)
        self.assertEqual(M8LFOShape.EXPD_T, 14)
        self.assertEqual(M8LFOShape.EXPU_T, 15)
        self.assertEqual(M8LFOShape.SQ_D_T, 16)
        self.assertEqual(M8LFOShape.SQ_U_T, 17)
        self.assertEqual(M8LFOShape.RAND_T, 18)
        self.assertEqual(M8LFOShape.DRNK_T, 19)

    def test_m8_lfo_shape_range(self):
        """Test M8LFOShape enum covers full range 0-19."""
        # Check we have all 20 shapes
        all_values = [shape.value for shape in M8LFOShape]
        self.assertEqual(len(all_values), 20)
        self.assertEqual(min(all_values), 0)
        self.assertEqual(max(all_values), 19)

    def test_m8_lfo_trigger_mode_values(self):
        """Test M8LFOTriggerMode enum has correct values."""
        self.assertEqual(M8LFOTriggerMode.FREE, 0)
        self.assertEqual(M8LFOTriggerMode.RETRIG, 1)
        self.assertEqual(M8LFOTriggerMode.HOLD, 2)
        self.assertEqual(M8LFOTriggerMode.ONCE, 3)

    def test_enums_with_modulator_lfo_params(self):
        """Test that enums can be used to set LFO parameters."""
        mod = M8Modulator(mod_type=M8ModulatorType.LFO)

        # Set LFO shape using enum
        mod.set(LFO_OSCILLATOR_OFFSET, M8LFOShape.SIN)
        self.assertEqual(mod.get(LFO_OSCILLATOR_OFFSET), 1)
        self.assertEqual(mod.get(LFO_OSCILLATOR_OFFSET), M8LFOShape.SIN)

        # Set LFO trigger mode using enum
        mod.set(LFO_TRIGGER_OFFSET, M8LFOTriggerMode.RETRIG)
        self.assertEqual(mod.get(LFO_TRIGGER_OFFSET), 1)
        self.assertEqual(mod.get(LFO_TRIGGER_OFFSET), M8LFOTriggerMode.RETRIG)


if __name__ == '__main__':
    unittest.main()
