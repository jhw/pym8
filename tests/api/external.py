import unittest
from m8.api.instruments.external import (
    M8External, DEFAULT_PARAMETERS, M8ExternalParam,
    M8ExternalInput, M8ExternalPort, M8ExternalModDest
)
from m8.api.instrument import MODULATORS_OFFSET, M8FilterType, M8LimiterType, M8InstrumentType
from m8.api.modulator import M8Modulators


class TestM8External(unittest.TestCase):
    def setUp(self):
        # Define External-specific parameters
        self.test_name = "TestExternal"

    def test_constructor_and_defaults(self):
        """Test default constructor and default parameter values."""
        external = M8External()

        # Check type is set correctly
        self.assertEqual(external.get(M8ExternalParam.TYPE), M8InstrumentType.EXTERNAL)

        # Check default parameters
        self.assertEqual(external.name, "")

        # Check non-zero defaults using generic get
        self.assertEqual(external.get(M8ExternalParam.FINE_TUNE), 0x80)  # FINETUNE
        self.assertEqual(external.get(M8ExternalParam.CUTOFF), 0xFF)     # CUTOFF
        self.assertEqual(external.get(M8ExternalParam.PAN), 0x80)        # PAN
        self.assertEqual(external.get(M8ExternalParam.DRY), 0xC0)        # DRY

    def test_constructor_with_name(self):
        """Test constructor with name parameter."""
        external = M8External(name=self.test_name)

        # Check name was set
        self.assertEqual(external.name, self.test_name)

        # Check type is still correct
        self.assertEqual(external.get(M8ExternalParam.TYPE), M8InstrumentType.EXTERNAL)

    def test_midi_parameters(self):
        """Test External-specific MIDI parameters (INPUT, PORT, CHANNEL, BANK, PROGRAM)."""
        external = M8External()

        # Test INPUT
        external.set(M8ExternalParam.INPUT, M8ExternalInput.USB)
        self.assertEqual(external.get(M8ExternalParam.INPUT), M8ExternalInput.USB)

        # Test PORT
        external.set(M8ExternalParam.PORT, M8ExternalPort.MIDI)
        self.assertEqual(external.get(M8ExternalParam.PORT), M8ExternalPort.MIDI)

        # Test CHANNEL (0-15)
        external.set(M8ExternalParam.CHANNEL, 0x05)
        self.assertEqual(external.get(M8ExternalParam.CHANNEL), 0x05)

        # Test BANK (0-127)
        external.set(M8ExternalParam.BANK, 0x40)
        self.assertEqual(external.get(M8ExternalParam.BANK), 0x40)

        # Test PROGRAM (0-127)
        external.set(M8ExternalParam.PROGRAM, 0x7F)
        self.assertEqual(external.get(M8ExternalParam.PROGRAM), 0x7F)

    def test_cc_parameters(self):
        """Test CC (Control Change) number and value parameters."""
        external = M8External()

        # Test CCA
        external.set(M8ExternalParam.CCA_NUM, 0x01)
        external.set(M8ExternalParam.CCA_VAL, 0x7F)
        self.assertEqual(external.get(M8ExternalParam.CCA_NUM), 0x01)
        self.assertEqual(external.get(M8ExternalParam.CCA_VAL), 0x7F)

        # Test CCB
        external.set(M8ExternalParam.CCB_NUM, 0x07)
        external.set(M8ExternalParam.CCB_VAL, 0x64)
        self.assertEqual(external.get(M8ExternalParam.CCB_NUM), 0x07)
        self.assertEqual(external.get(M8ExternalParam.CCB_VAL), 0x64)

        # Test CCC
        external.set(M8ExternalParam.CCC_NUM, 0x0A)
        external.set(M8ExternalParam.CCC_VAL, 0x40)
        self.assertEqual(external.get(M8ExternalParam.CCC_NUM), 0x0A)
        self.assertEqual(external.get(M8ExternalParam.CCC_VAL), 0x40)

        # Test CCD
        external.set(M8ExternalParam.CCD_NUM, 0x47)
        external.set(M8ExternalParam.CCD_VAL, 0x20)
        self.assertEqual(external.get(M8ExternalParam.CCD_NUM), 0x47)
        self.assertEqual(external.get(M8ExternalParam.CCD_VAL), 0x20)

    def test_filter_and_mixer_parameters(self):
        """Test filter and mixer parameters."""
        external = M8External()

        # Test FILTER_TYPE
        external.set(M8ExternalParam.FILTER_TYPE, M8FilterType.LOWPASS)
        self.assertEqual(external.get(M8ExternalParam.FILTER_TYPE), M8FilterType.LOWPASS)

        # Test CUTOFF
        external.set(M8ExternalParam.CUTOFF, 0xA0)
        self.assertEqual(external.get(M8ExternalParam.CUTOFF), 0xA0)

        # Test RESONANCE
        external.set(M8ExternalParam.RESONANCE, 0x40)
        self.assertEqual(external.get(M8ExternalParam.RESONANCE), 0x40)

        # Test AMP
        external.set(M8ExternalParam.AMP, 0x80)
        self.assertEqual(external.get(M8ExternalParam.AMP), 0x80)

        # Test LIMIT
        external.set(M8ExternalParam.LIMIT, M8LimiterType.FOLD)
        self.assertEqual(external.get(M8ExternalParam.LIMIT), M8LimiterType.FOLD)

        # Test PAN
        external.set(M8ExternalParam.PAN, 0x60)
        self.assertEqual(external.get(M8ExternalParam.PAN), 0x60)

        # Test DRY
        external.set(M8ExternalParam.DRY, 0xB0)
        self.assertEqual(external.get(M8ExternalParam.DRY), 0xB0)

        # Test sends
        external.set(M8ExternalParam.CHORUS_SEND, 0x30)
        external.set(M8ExternalParam.DELAY_SEND, 0x50)
        external.set(M8ExternalParam.REVERB_SEND, 0x70)
        self.assertEqual(external.get(M8ExternalParam.CHORUS_SEND), 0x30)
        self.assertEqual(external.get(M8ExternalParam.DELAY_SEND), 0x50)
        self.assertEqual(external.get(M8ExternalParam.REVERB_SEND), 0x70)

    def test_binary_serialization(self):
        """Test write/read round-trip preserves all parameters AND modulators."""
        # Create external with custom parameters
        external = M8External(name="TEST")
        external.set(M8ExternalParam.INPUT, M8ExternalInput.USB_MIDI)
        external.set(M8ExternalParam.PORT, M8ExternalPort.USB)
        external.set(M8ExternalParam.CHANNEL, 0x0F)
        external.set(M8ExternalParam.BANK, 0x40)
        external.set(M8ExternalParam.PROGRAM, 0x20)
        external.set(M8ExternalParam.CCA_NUM, 0x01)
        external.set(M8ExternalParam.CCA_VAL, 0x64)
        external.set(M8ExternalParam.CUTOFF, 0xA0)
        external.set(M8ExternalParam.RESONANCE, 0x50)

        # Customize modulators
        external.modulators[0].destination = M8ExternalModDest.VOLUME
        external.modulators[0].amount = 200
        external.modulators[0].set(2, 0x05)  # Attack
        external.modulators[0].set(4, 0x70)  # Decay

        external.modulators[2].destination = M8ExternalModDest.AMP
        external.modulators[2].amount = 120
        external.modulators[2].set(2, 0x02)  # LFO shape (RAMP_DOWN)

        # Write to binary
        binary = external.write()

        # Read it back
        read_external = M8External.read(binary)

        # Check all parameters were preserved
        self.assertEqual(read_external.name, "TEST")
        self.assertEqual(read_external.get(M8ExternalParam.INPUT), M8ExternalInput.USB_MIDI)
        self.assertEqual(read_external.get(M8ExternalParam.PORT), M8ExternalPort.USB)
        self.assertEqual(read_external.get(M8ExternalParam.CHANNEL), 0x0F)
        self.assertEqual(read_external.get(M8ExternalParam.BANK), 0x40)
        self.assertEqual(read_external.get(M8ExternalParam.PROGRAM), 0x20)
        self.assertEqual(read_external.get(M8ExternalParam.CCA_NUM), 0x01)
        self.assertEqual(read_external.get(M8ExternalParam.CCA_VAL), 0x64)
        self.assertEqual(read_external.get(M8ExternalParam.CUTOFF), 0xA0)
        self.assertEqual(read_external.get(M8ExternalParam.RESONANCE), 0x50)

        # Check modulators were preserved
        self.assertEqual(read_external.modulators[0].destination, M8ExternalModDest.VOLUME)
        self.assertEqual(read_external.modulators[0].amount, 200)
        self.assertEqual(read_external.modulators[0].get(2), 0x05)
        self.assertEqual(read_external.modulators[0].get(4), 0x70)

        self.assertEqual(read_external.modulators[2].destination, M8ExternalModDest.AMP)
        self.assertEqual(read_external.modulators[2].amount, 120)
        self.assertEqual(read_external.modulators[2].get(2), 0x02)

    def test_clone(self):
        """Test cloning creates independent copy."""
        # Create external with custom parameters
        original = M8External(name=self.test_name)
        original.set(M8ExternalParam.INPUT, M8ExternalInput.MIDI)
        original.set(M8ExternalParam.PORT, M8ExternalPort.USB_MIDI)
        original.set(M8ExternalParam.CHANNEL, 0x0A)
        original.set(M8ExternalParam.CCA_NUM, 0x40)
        original.set(M8ExternalParam.CCA_VAL, 0x7F)

        # Clone it
        cloned = original.clone()

        # Check they are different objects
        self.assertIsNot(cloned, original)

        # Check all values match
        self.assertEqual(cloned.name, original.name)
        self.assertEqual(cloned.get(M8ExternalParam.INPUT), original.get(M8ExternalParam.INPUT))
        self.assertEqual(cloned.get(M8ExternalParam.PORT), original.get(M8ExternalParam.PORT))
        self.assertEqual(cloned.get(M8ExternalParam.CHANNEL), original.get(M8ExternalParam.CHANNEL))
        self.assertEqual(cloned.get(M8ExternalParam.CCA_NUM), original.get(M8ExternalParam.CCA_NUM))
        self.assertEqual(cloned.get(M8ExternalParam.CCA_VAL), original.get(M8ExternalParam.CCA_VAL))

        # Modify clone and verify original unchanged
        cloned.set(M8ExternalParam.CCA_VAL, 0x00)
        self.assertEqual(original.get(M8ExternalParam.CCA_VAL), 0x7F)
        self.assertEqual(cloned.get(M8ExternalParam.CCA_VAL), 0x00)

    def test_modulators_initialized(self):
        """Test that modulators are initialized with defaults."""
        external = M8External()

        # Check modulators exist
        self.assertIsInstance(external.modulators, M8Modulators)

        # Check 4 modulators
        self.assertEqual(len(external.modulators), 4)

        # Check default types (2 AHD, 2 LFO)
        self.assertEqual(external.modulators[0].mod_type, 0)  # AHD
        self.assertEqual(external.modulators[1].mod_type, 0)  # AHD

    def test_modulators_read_write(self):
        """Test that modulators are read and written correctly."""
        # Create external with custom modulator
        original = M8External(name="TEST")
        original.modulators[0].destination = M8ExternalModDest.CCA
        original.modulators[0].set(2, 0x20)  # Attack

        # Write to binary
        binary = original.write()

        # Check length (should be standard block size)
        self.assertEqual(len(binary), 215)

        # Read back
        deserialized = M8External.read(binary)

        # Verify modulator preserved
        self.assertEqual(deserialized.modulators[0].destination, M8ExternalModDest.CCA)
        self.assertEqual(deserialized.modulators[0].get(2), 0x20)

    def test_modulators_clone(self):
        """Test that modulators are cloned correctly."""
        original = M8External(name="TEST")
        original.modulators[1].destination = M8ExternalModDest.CCB
        original.modulators[1].set(4, 0x40)  # Decay

        # Clone
        cloned = original.clone()

        # Check modulator values match
        self.assertEqual(cloned.modulators[1].destination, original.modulators[1].destination)
        self.assertEqual(cloned.modulators[1].get(4), original.modulators[1].get(4))

        # Modify clone
        cloned.modulators[1].destination = M8ExternalModDest.CCC

        # Check original unchanged
        self.assertEqual(original.modulators[1].destination, M8ExternalModDest.CCB)

    def test_external_input_enum(self):
        """Test ExternalInput enum values work correctly."""
        external = M8External()

        # Test all input values
        for input_val in M8ExternalInput:
            external.set(M8ExternalParam.INPUT, input_val)
            self.assertEqual(external.get(M8ExternalParam.INPUT), input_val)

    def test_external_port_enum(self):
        """Test ExternalPort enum values work correctly."""
        external = M8External()

        # Test all port values
        for port_val in M8ExternalPort:
            external.set(M8ExternalParam.PORT, port_val)
            self.assertEqual(external.get(M8ExternalParam.PORT), port_val)

    def test_modulation_destinations(self):
        """Test External-specific modulation destinations."""
        external = M8External()

        # Test setting CC destinations
        external.modulators[0].destination = M8ExternalModDest.CCA
        external.modulators[1].destination = M8ExternalModDest.CCB
        external.modulators[2].destination = M8ExternalModDest.CCC
        external.modulators[3].destination = M8ExternalModDest.CCD

        self.assertEqual(external.modulators[0].destination, M8ExternalModDest.CCA)
        self.assertEqual(external.modulators[1].destination, M8ExternalModDest.CCB)
        self.assertEqual(external.modulators[2].destination, M8ExternalModDest.CCC)
        self.assertEqual(external.modulators[3].destination, M8ExternalModDest.CCD)

    def test_to_dict_default_enum_mode(self):
        """Test to_dict() with default enum_mode='value' returns integer values."""
        external = M8External(name="EnumTest")
        external.set(M8ExternalParam.INPUT, M8ExternalInput.USB)
        external.set(M8ExternalParam.PORT, M8ExternalPort.MIDI)
        external.set(M8ExternalParam.FILTER_TYPE, M8FilterType.LOWPASS)
        external.set(M8ExternalParam.LIMIT, M8LimiterType.SIN)

        # Export with default enum_mode
        result = external.to_dict()

        # Verify enum values are integers
        self.assertEqual(result['params']['INPUT'], M8ExternalInput.USB.value)
        self.assertEqual(result['params']['PORT'], M8ExternalPort.MIDI.value)
        self.assertEqual(result['params']['FILTER_TYPE'], M8FilterType.LOWPASS.value)
        self.assertEqual(result['params']['LIMIT'], M8LimiterType.SIN.value)
        self.assertIsInstance(result['params']['INPUT'], int)
        self.assertIsInstance(result['params']['PORT'], int)

    def test_to_dict_enum_mode_name(self):
        """Test to_dict() with enum_mode='name' returns human-readable enum names."""
        external = M8External(name="EnumTest")
        external.set(M8ExternalParam.INPUT, M8ExternalInput.USB)
        external.set(M8ExternalParam.PORT, M8ExternalPort.MIDI)
        external.set(M8ExternalParam.FILTER_TYPE, M8FilterType.LOWPASS)
        external.set(M8ExternalParam.LIMIT, M8LimiterType.SIN)

        # Export with enum_mode='name'
        result = external.to_dict(enum_mode='name')

        # Verify enum values are human-readable strings
        self.assertEqual(result['params']['INPUT'], 'USB')
        self.assertEqual(result['params']['PORT'], 'MIDI')
        self.assertEqual(result['params']['FILTER_TYPE'], 'LOWPASS')
        self.assertEqual(result['params']['LIMIT'], 'SIN')

    def test_from_dict_with_integer_values(self):
        """Test from_dict() accepts integer enum values (backward compatibility)."""
        params = {
            'name': 'IntTest',
            'params': {
                'INPUT': M8ExternalInput.USB_MIDI.value,
                'PORT': M8ExternalPort.USB.value,
                'FILTER_TYPE': M8FilterType.HIGHPASS.value,
                'LIMIT': M8LimiterType.CLIP.value,
                'CUTOFF': 0x40,
                'CCA_NUM': 0x07,
                'CCA_VAL': 0x7F,
            },
            'modulators': []
        }

        external = M8External.from_dict(params)

        # Verify values were set correctly
        self.assertEqual(external.name, 'IntTest')
        self.assertEqual(external.get(M8ExternalParam.INPUT), M8ExternalInput.USB_MIDI.value)
        self.assertEqual(external.get(M8ExternalParam.PORT), M8ExternalPort.USB.value)
        self.assertEqual(external.get(M8ExternalParam.FILTER_TYPE), M8FilterType.HIGHPASS.value)
        self.assertEqual(external.get(M8ExternalParam.LIMIT), M8LimiterType.CLIP.value)
        self.assertEqual(external.get(M8ExternalParam.CUTOFF), 0x40)
        self.assertEqual(external.get(M8ExternalParam.CCA_NUM), 0x07)
        self.assertEqual(external.get(M8ExternalParam.CCA_VAL), 0x7F)

    def test_from_dict_with_string_enum_names(self):
        """Test from_dict() accepts string enum names (human-readable YAML)."""
        params = {
            'name': 'StringTest',
            'params': {
                'INPUT': 'USB_MIDI',
                'PORT': 'USB',
                'FILTER_TYPE': 'HIGHPASS',
                'LIMIT': 'CLIP',
                'CUTOFF': 0x40,
            },
            'modulators': []
        }

        external = M8External.from_dict(params)

        # Verify values were set correctly
        self.assertEqual(external.name, 'StringTest')
        self.assertEqual(external.get(M8ExternalParam.INPUT), M8ExternalInput.USB_MIDI.value)
        self.assertEqual(external.get(M8ExternalParam.PORT), M8ExternalPort.USB.value)
        self.assertEqual(external.get(M8ExternalParam.FILTER_TYPE), M8FilterType.HIGHPASS.value)
        self.assertEqual(external.get(M8ExternalParam.LIMIT), M8LimiterType.CLIP.value)
        self.assertEqual(external.get(M8ExternalParam.CUTOFF), 0x40)

    def test_round_trip_serialization_with_enum_names(self):
        """Test round-trip: to_dict(enum_mode='name') -> from_dict() -> to_dict()."""
        # Create original external
        original = M8External(name="RoundTrip")
        original.set(M8ExternalParam.INPUT, M8ExternalInput.MIDI)
        original.set(M8ExternalParam.PORT, M8ExternalPort.USB_MIDI)
        original.set(M8ExternalParam.FILTER_TYPE, M8FilterType.BANDPASS)
        original.set(M8ExternalParam.LIMIT, M8LimiterType.FOLD)
        original.set(M8ExternalParam.CUTOFF, 0x60)
        original.set(M8ExternalParam.RESONANCE, 0xA0)
        original.set(M8ExternalParam.CCA_NUM, 0x10)
        original.set(M8ExternalParam.CCA_VAL, 0x64)

        # Export with enum_mode='name'
        dict_with_names = original.to_dict(enum_mode='name')

        # Verify enum names are strings
        self.assertEqual(dict_with_names['params']['INPUT'], 'MIDI')
        self.assertEqual(dict_with_names['params']['PORT'], 'USB_MIDI')
        self.assertEqual(dict_with_names['params']['FILTER_TYPE'], 'BANDPASS')
        self.assertEqual(dict_with_names['params']['LIMIT'], 'FOLD')

        # Import from dict
        restored = M8External.from_dict(dict_with_names)

        # Verify all values match
        self.assertEqual(restored.name, original.name)
        self.assertEqual(restored.get(M8ExternalParam.INPUT), original.get(M8ExternalParam.INPUT))
        self.assertEqual(restored.get(M8ExternalParam.PORT), original.get(M8ExternalParam.PORT))
        self.assertEqual(restored.get(M8ExternalParam.FILTER_TYPE), original.get(M8ExternalParam.FILTER_TYPE))
        self.assertEqual(restored.get(M8ExternalParam.LIMIT), original.get(M8ExternalParam.LIMIT))
        self.assertEqual(restored.get(M8ExternalParam.CUTOFF), original.get(M8ExternalParam.CUTOFF))
        self.assertEqual(restored.get(M8ExternalParam.RESONANCE), original.get(M8ExternalParam.RESONANCE))
        self.assertEqual(restored.get(M8ExternalParam.CCA_NUM), original.get(M8ExternalParam.CCA_NUM))
        self.assertEqual(restored.get(M8ExternalParam.CCA_VAL), original.get(M8ExternalParam.CCA_VAL))


    def test_m8s_file_offset_verification(self):
        """Test that reading EXTERNAL.m8s fixture verifies correct parameter offsets.

        The fixture was created with known values to verify offset mapping:
        - Input: 0x01, Port: 0x02, Channel: 0x03
        - Bank: 0x04, Program: 0x05
        - CCA: num=0x01/val=0x06, CCB: num=0x02/val=0x07
        - CCC: num=0x03/val=0x08, CCD: num=0x04/val=0x09
        - Filter: 0x07, Cutoff: 0x0A, Resonance: 0x0B
        - Amp: 0x0C, Limit: 0x08, Pan: 0x0D
        - Dry: 0x0E, Chorus: 0x0F, Delay: 0x10, Reverb: 0x11
        """
        from pathlib import Path
        from m8.api.project import M8Project

        # Path to test M8s file
        test_file = Path(__file__).parent.parent / "fixtures/EXTERNAL.m8s"

        # Read project and get instrument 0
        project = M8Project.read_from_file(str(test_file))
        external = project.instruments[0]

        # Verify it's an External instrument
        self.assertIsInstance(external, M8External)
        self.assertEqual(external.get(M8ExternalParam.TYPE), M8InstrumentType.EXTERNAL)

        # Verify MIDI parameters
        self.assertEqual(external.get(M8ExternalParam.INPUT), 0x01)
        self.assertEqual(external.get(M8ExternalParam.PORT), 0x02)
        self.assertEqual(external.get(M8ExternalParam.CHANNEL), 0x03)
        self.assertEqual(external.get(M8ExternalParam.BANK), 0x04)
        self.assertEqual(external.get(M8ExternalParam.PROGRAM), 0x05)

        # Verify CC parameters
        self.assertEqual(external.get(M8ExternalParam.CCA_NUM), 0x01)
        self.assertEqual(external.get(M8ExternalParam.CCA_VAL), 0x06)
        self.assertEqual(external.get(M8ExternalParam.CCB_NUM), 0x02)
        self.assertEqual(external.get(M8ExternalParam.CCB_VAL), 0x07)
        self.assertEqual(external.get(M8ExternalParam.CCC_NUM), 0x03)
        self.assertEqual(external.get(M8ExternalParam.CCC_VAL), 0x08)
        self.assertEqual(external.get(M8ExternalParam.CCD_NUM), 0x04)
        self.assertEqual(external.get(M8ExternalParam.CCD_VAL), 0x09)

        # Verify filter/mixer parameters
        self.assertEqual(external.get(M8ExternalParam.FILTER_TYPE), 0x07)
        self.assertEqual(external.get(M8ExternalParam.CUTOFF), 0x0A)
        self.assertEqual(external.get(M8ExternalParam.RESONANCE), 0x0B)
        self.assertEqual(external.get(M8ExternalParam.AMP), 0x0C)
        self.assertEqual(external.get(M8ExternalParam.LIMIT), 0x08)
        self.assertEqual(external.get(M8ExternalParam.PAN), 0x0D)
        self.assertEqual(external.get(M8ExternalParam.DRY), 0x0E)
        self.assertEqual(external.get(M8ExternalParam.CHORUS_SEND), 0x0F)
        self.assertEqual(external.get(M8ExternalParam.DELAY_SEND), 0x10)
        self.assertEqual(external.get(M8ExternalParam.REVERB_SEND), 0x11)


if __name__ == '__main__':
    unittest.main()
