import unittest
from unittest.mock import MagicMock, patch
from m8.api.utils.context import M8InstrumentContext, _InstrumentContextBlock

class TestM8InstrumentContext(unittest.TestCase):
    """Test the M8InstrumentContext singleton class."""
    
    def setUp(self):
        """Set up a fresh context instance before each test."""
        # Clear the singleton instance
        M8InstrumentContext._instance = None
        self.context = M8InstrumentContext.get_instance()
        
    def tearDown(self):
        """Clean up after each test."""
        self.context.clear()
        
    def test_singleton_pattern(self):
        """Test that multiple calls to get_instance return the same instance."""
        instance1 = M8InstrumentContext.get_instance()
        instance2 = M8InstrumentContext.get_instance()
        self.assertIs(instance1, instance2)
        
    def test_project_context(self):
        """Test setting and getting project context."""
        mock_project = MagicMock()
        self.context.set_project(mock_project)
        self.assertEqual(self.context.project, mock_project)
        
    def test_get_instrument_type_id_with_explicit_id(self):
        """Test getting instrument type ID using an explicit ID."""
        # Set up a mock project with instruments
        mock_project = MagicMock()
        mock_instrument = MagicMock()
        
        # Set up a better mock
        mock_instrument.configure_mock(**{
            'type.value': 1,
            'instrument_type_id': 1
        })
        
        mock_project.instruments = [mock_instrument]
                
        self.context.set_project(mock_project)
        
        # Test with valid ID
        self.assertEqual(self.context.get_instrument_type_id(0), 1)
        
        # Test with invalid ID
        self.assertIsNone(self.context.get_instrument_type_id(1))
        
    def test_get_instrument_type_id_from_current_context(self):
        """Test getting instrument type ID from current context."""
        # Set current instrument type ID directly
        self.context.current_instrument_type_id = 1  # MACROSYNTH ID
        self.assertEqual(self.context.get_instrument_type_id(), 1)
        
    def test_get_instrument_type(self):
        """Test the get_instrument_type bridge method."""
        # Mock the get_instrument_types config function
        with patch('m8.config.get_instrument_types') as mock_get_types:
            mock_get_types.return_value = {0: "WAVSYNTH", 1: "MACROSYNTH", 2: "SAMPLER"}
            
            # Test with type ID set
            self.context.current_instrument_type_id = 1
            self.assertEqual(self.context.get_instrument_type(), "MACROSYNTH")
            
            # Test with no type ID set
            self.context.current_instrument_type_id = None
            self.assertIsNone(self.context.get_instrument_type())
        
    def test_with_instrument_context_manager(self):
        """Test the with_instrument context manager."""
        # Initial state
        self.assertIsNone(self.context.current_instrument_id)
        self.assertIsNone(self.context.current_instrument_type_id)
        
        # Enter context with ID
        with self.context.with_instrument(instrument_id=42):
            self.assertEqual(self.context.current_instrument_id, 42)
            self.assertIsNone(self.context.current_instrument_type_id)
            
        # Context should be restored after block
        self.assertIsNone(self.context.current_instrument_id)
        self.assertIsNone(self.context.current_instrument_type_id)
        
        # Enter context with type ID
        with self.context.with_instrument(instrument_type_id=1):
            self.assertIsNone(self.context.current_instrument_id)
            self.assertEqual(self.context.current_instrument_type_id, 1)
            
        # Context should be restored
        self.assertIsNone(self.context.current_instrument_id)
        self.assertIsNone(self.context.current_instrument_type_id)
        
    def test_nested_context_blocks(self):
        """Test that nested context blocks work correctly."""
        # Set up initial context
        self.context.current_instrument_id = 1
        self.context.current_instrument_type_id = 0  # WAVSYNTH ID
        
        # First nested block - only set instrument_id
        with self.context.with_instrument(instrument_id=2):
            self.assertEqual(self.context.current_instrument_id, 2)
            # The current_instrument_type_id should be preserved
            self.assertEqual(self.context.current_instrument_type_id, 0)
            
            # Second nested block - only set instrument_type_id
            with self.context.with_instrument(instrument_type_id=1):
                self.assertEqual(self.context.current_instrument_id, 2)
                self.assertEqual(self.context.current_instrument_type_id, 1)
                
            # Back to first block
            self.assertEqual(self.context.current_instrument_id, 2)
            self.assertEqual(self.context.current_instrument_type_id, 0)
            
        # Back to original context
        self.assertEqual(self.context.current_instrument_id, 1)
        self.assertEqual(self.context.current_instrument_type_id, 0)
        
    def test_clear_context(self):
        """Test clearing the context."""
        self.context.current_instrument_id = 5
        self.context.current_instrument_type_id = 2  # SAMPLER ID
        self.context.project = MagicMock()
        
        self.context.clear()
        
        self.assertIsNone(self.context.current_instrument_id)
        self.assertIsNone(self.context.current_instrument_type_id)
        self.assertIsNone(self.context.project)

class TestInstrumentContextBlock(unittest.TestCase):
    """Test the _InstrumentContextBlock private class."""
    
    def setUp(self):
        """Set up a fresh context block for testing."""
        self.context_manager = MagicMock()
        self.context_manager.current_instrument_id = None
        self.context_manager.current_instrument_type_id = None
        
    def test_enter_exit(self):
        """Test entering and exiting the context block."""
        # Set up initial state
        self.context_manager.current_instrument_id = 1
        self.context_manager.current_instrument_type_id = 0  # WAVSYNTH ID
        
        # Create block with direct ID values
        block = _InstrumentContextBlock(
            self.context_manager, 
            instrument_id=2, 
            instrument_type_id=1
        )
        
        # Enter the block
        result = block.__enter__()
        
        # Check context was updated
        self.assertEqual(self.context_manager.current_instrument_id, 2)
        self.assertEqual(self.context_manager.current_instrument_type_id, 1)
        self.assertEqual(result, self.context_manager)
        
        # Exit the block
        block.__exit__(None, None, None)
        
        # Check context was restored
        self.assertEqual(self.context_manager.current_instrument_id, 1)
        self.assertEqual(self.context_manager.current_instrument_type_id, 0)


if __name__ == '__main__':
    unittest.main()