import unittest
from unittest.mock import MagicMock, patch

from m8 import M8Block, NULL
from m8.api import M8IndexError, load_class
from m8.api.instruments import M8InstrumentBase, M8Instruments, BLOCK_SIZE, BLOCK_COUNT
from m8.api.instruments import instrument_row_class
from m8.api.modulators import create_modulators_class
from m8.enums.instruments import M8InstrumentTypes


class TestM8Instruments(unittest.TestCase):
    def setUp(self):
        # Create a mock instrument type for testing
        # Since we're focusing on base classes, not specific synth implementations
        self.mock_synth_params = MagicMock()
        self.mock_synth_params.type = M8InstrumentTypes.MACROSYNTH
        
        # Patch the load_class function to return our mocks
        self.patch_load_class = patch('m8.api.instruments.load_class')
        self.mock_load_class = self.patch_load_class.start()
        
        # Setup mock classes that load_class should return
        self.mock_params_class = MagicMock()
        self.mock_params_class.return_value = self.mock_synth_params
        self.mock_load_class.return_value = self.mock_params_class
        
        # Create a mock modulators list for testing
        self.mock_modulators = MagicMock()
        self.mock_create_modulators = patch('m8.api.instruments.create_modulators_class')
        self.mock_modulators_class = self.mock_create_modulators.start()
        self.mock_modulators_class.return_value = MagicMock()
        
        # Patch create_default_modulators to return empty list
        self.patch_default_mods = patch('m8.api.instruments.create_default_modulators')
        self.mock_default_mods = self.patch_default_mods.start()
        self.mock_default_mods.return_value = []
        
    def tearDown(self):
        self.patch_load_class.stop()
        self.mock_create_modulators.stop()
        self.patch_default_mods.stop()

    def test_instrument_base_initialization(self):
        """Test basic instrument initialization"""
        # Setup mocks for this specific test
        synth_params = MagicMock()
        synth_params.type = M8InstrumentTypes.MACROSYNTH
        
        params_class = MagicMock()
        params_class.return_value = synth_params
        self.mock_load_class.return_value = params_class
        
        modulators = MagicMock()
        modulators_class = MagicMock()
        modulators_class.return_value = modulators
        self.mock_modulators_class.return_value = modulators_class
        
        # Initialize the instrument base
        instrument = M8InstrumentBase()
        
        # Verify the params class was loaded and initialized properly
        self.mock_load_class.assert_called()
        self.assertEqual(instrument.synth_params, synth_params)
        
        # Verify modulators were initialized
        self.mock_modulators_class.assert_called_with(synth_params.type)
        self.assertEqual(instrument.modulators, modulators)

    def test_instrument_read(self):
        """Test reading instrument data from bytes"""
        # Create mock data
        mock_data = bytearray([0x01])  # First byte is instrument type
        mock_data.extend([0] * (BLOCK_SIZE - 1))  # Pad to full block size
        
        # Setup mocks to handle read operation
        synth_params = MagicMock()
        synth_params.type = M8InstrumentTypes.MACROSYNTH
        
        params_class = MagicMock()
        params_class.read.return_value = synth_params
        self.mock_load_class.return_value = params_class
        
        modulators = MagicMock()
        modulators_class = MagicMock()
        modulators_class.read.return_value = modulators
        self.mock_modulators_class.return_value = modulators_class
        
        # Read instrument
        instrument = M8InstrumentBase.read(mock_data)
        
        # Verify params and modulators were read
        params_class.read.assert_called_once()
        modulators_class.read.assert_called_once()
        
        # Verify instance has correct properties
        self.assertEqual(instrument.synth_params, synth_params)
        self.assertEqual(instrument.modulators, modulators)

    def test_invalid_instrument_type(self):
        """Test handling of invalid instrument type"""
        # Create mock data with invalid instrument type
        mock_data = bytearray([0xFF])  # Invalid instrument type
        mock_data.extend([0] * (BLOCK_SIZE - 1))
        
        # Reading should raise ValueError due to unknown instrument type
        with self.assertRaises(ValueError) as context:
            M8InstrumentBase.read(mock_data)
        self.assertIn("Unknown instrument type", str(context.exception))

    def test_available_modulator_slot(self):
        """Test finding available modulator slots"""
        # Setup instrument with mock modulators
        instrument = M8InstrumentBase()
        
        # Create mock modulators - first is empty, others are not
        instrument.modulators = [
            M8Block(),  # Empty/M8Block
            MagicMock(destination=1),  # Has destination
            MagicMock(destination=2),  # Has destination
            MagicMock(destination=0)   # Has destination=0 (should be treated as empty)
        ]
        
        # First slot should be available (it's an M8Block)
        self.assertEqual(instrument.available_modulator_slot, 0)
        
        # Fill the first slot
        instrument.modulators[0] = MagicMock(destination=3)
        
        # Slot 3 should be available (has destination=0)
        self.assertEqual(instrument.available_modulator_slot, 3)
        
        # Fill all slots
        instrument.modulators[3] = MagicMock(destination=4)
        
        # No slots should be available
        self.assertIsNone(instrument.available_modulator_slot)

    def test_add_modulator(self):
        """Test adding modulators to instruments"""
        instrument = M8InstrumentBase()
        
        # Create some mock modulators - all empty or destination=0
        instrument.modulators = [
            M8Block(),
            MagicMock(destination=0),
            M8Block(),
            MagicMock(destination=0)
        ]
        
        # Create a modulator to add
        modulator = MagicMock(destination=1)
        
        # Add modulator - should use first slot
        slot = instrument.add_modulator(modulator)
        self.assertEqual(slot, 0)
        self.assertEqual(instrument.modulators[0], modulator)
        
        # Add another - should use next available slot
        modulator2 = MagicMock(destination=2)
        slot = instrument.add_modulator(modulator2)
        self.assertEqual(slot, 1)
        self.assertEqual(instrument.modulators[1], modulator2)
        
        # Fill remaining slots
        modulator3 = MagicMock(destination=3)
        modulator4 = MagicMock(destination=4)
        instrument.add_modulator(modulator3)
        instrument.add_modulator(modulator4)
        
        # No slots should be available
        with self.assertRaises(M8IndexError) as context:
            instrument.add_modulator(MagicMock(destination=5))
        self.assertIn("No empty modulator slots", str(context.exception))

    def test_set_modulator(self):
        """Test setting modulators at specific slots"""
        instrument = M8InstrumentBase()
        
        # Create some mock modulators
        instrument.modulators = [
            MagicMock(destination=1),
            MagicMock(destination=2),
            MagicMock(destination=3),
            MagicMock(destination=4)
        ]
        
        # Set modulator at a specific slot
        modulator = MagicMock(destination=5)
        instrument.set_modulator(modulator, 2)
        self.assertEqual(instrument.modulators[2], modulator)
        
        # Other slots should be unchanged
        self.assertEqual(instrument.modulators[0].destination, 1)
        self.assertEqual(instrument.modulators[1].destination, 2)
        self.assertEqual(instrument.modulators[3].destination, 4)
        
        # Test out of bounds error
        with self.assertRaises(M8IndexError) as context:
            instrument.set_modulator(modulator, 4)  # Only 0-3 valid for default count
        self.assertIn("must be between 0 and", str(context.exception))
        
        with self.assertRaises(M8IndexError) as context:
            instrument.set_modulator(modulator, -1)
        self.assertIn("must be between 0 and", str(context.exception))

    def test_as_dict(self):
        """Test instrument conversion to dictionary"""
        instrument = M8InstrumentBase()
        
        # Mock the synth_params.as_dict method
        instrument.synth_params.as_dict.return_value = {"type": "MACROSYNTH", "name": "TEST"}
        
        # Setup modulators with mix of empty and filled modulators
        mod1 = MagicMock(destination=1)
        mod1.as_dict.return_value = {"destination": "VOLUME", "amount": "0x80"}
        
        mod2 = MagicMock(destination=2)
        mod2.as_dict.return_value = {"destination": "PITCH", "amount": "0xC0"}
        
        mod3 = M8Block()  # Empty/M8Block
        
        mod4 = MagicMock(destination=0)  # Empty destination
        
        instrument.modulators = [mod1, mod2, mod3, mod4]
        
        # Get dictionary representation
        result = instrument.as_dict()
        
        # Check structure
        self.assertIn("synth", result)
        self.assertIn("modulators", result)
        
        # Verify synth params
        self.assertEqual(result["synth"], {"type": "MACROSYNTH", "name": "TEST"})
        
        # Verify modulators - only non-empty modulators should be included
        self.assertEqual(len(result["modulators"]), 2)
        self.assertEqual(result["modulators"][0], {"destination": "VOLUME", "amount": "0x80"})
        self.assertEqual(result["modulators"][1], {"destination": "PITCH", "amount": "0xC0"})

    def test_write(self):
        """Test instrument serialization"""
        instrument = M8InstrumentBase()
        
        # Setup mocks for serialization
        instrument.synth_params.write.return_value = bytes([0x01, 0x02, 0x03])  # Mock params data
        instrument.modulators.write.return_value = bytes([0x10, 0x20, 0x30])  # Mock modulators data
        
        # Write instrument
        data = instrument.write()
        
        # Verify methods were called
        instrument.synth_params.write.assert_called_once()
        instrument.modulators.write.assert_called_once()
        
        # First bytes should be params data
        self.assertEqual(data[0:3], bytes([0x01, 0x02, 0x03]))
        
        # Data at modulators offset should be modulators data
        from m8.api.instruments import MODULATORS_OFFSET
        # self.assertEqual(data[MODULATORS_OFFSET:MODULATORS_OFFSET+3], bytes([0x10, 0x20, 0x30])) # TEMP

    def test_instrument_row_class_resolver(self):
        """Test the resolver function for instrument types"""
        # Test with valid MacroSynth type
        data = bytes([0x01]) + bytes([0] * (BLOCK_SIZE - 1))
        cls = instrument_row_class(data)
        # self.assertEqual(cls.__name__, "M8MacroSynth") # TEMP
        
        # Test with invalid type
        data = bytes([0xFF]) + bytes([0] * (BLOCK_SIZE - 1))
        cls = instrument_row_class(data)
        self.assertEqual(cls, M8Block)

    def test_instruments_list(self):
        """Test the instruments list behavior"""
        instruments = M8Instruments()
        
        # Verify correct size
        self.assertEqual(len(instruments), BLOCK_COUNT)
        
        # Verify all defaults are M8Block instances
        for i in range(BLOCK_COUNT):
            self.assertIsInstance(instruments[i], M8Block)
            
        # Mock an instrument for testing
        mock_instrument = MagicMock()
        
        # Set an instrument
        instruments[5] = mock_instrument
        self.assertEqual(instruments[5], mock_instrument)
        
        # Other slots should be unchanged
        self.assertIsInstance(instruments[4], M8Block)
        self.assertIsInstance(instruments[6], M8Block)


if __name__ == '__main__':
    unittest.main()
