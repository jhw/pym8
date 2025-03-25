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
        
    def test_get_instrument_type_with_explicit_id(self):
        """Test getting instrument type using an explicit ID."""
        # Set up a mock project with instruments
        mock_project = MagicMock()
        mock_instrument = MagicMock()
        mock_instrument.instrument_type = "MACROSYNTH"
        mock_project.instruments = [mock_instrument]
        
        self.context.set_project(mock_project)
        
        # Test with valid ID
        self.assertEqual(self.context.get_instrument_type(0), "MACROSYNTH")
        
        # Test with invalid ID
        self.assertIsNone(self.context.get_instrument_type(1))
        
    def test_get_instrument_type_from_current_context(self):
        """Test getting instrument type from current context."""
        # Set current instrument type directly
        self.context.current_instrument_type = "WAVSYNTH"
        self.assertEqual(self.context.get_instrument_type(), "WAVSYNTH")
        
        # Set current instrument ID
        self.context.current_instrument_type = None
        mock_project = MagicMock()
        mock_instrument = MagicMock()
        mock_instrument.instrument_type = "SAMPLER"
        mock_project.instruments = [mock_instrument]
        
        self.context.set_project(mock_project)
        self.context.current_instrument_id = 0
        
        self.assertEqual(self.context.get_instrument_type(), "SAMPLER")
        
    def test_with_instrument_context_manager(self):
        """Test the with_instrument context manager."""
        # Initial state
        self.assertIsNone(self.context.current_instrument_id)
        self.assertIsNone(self.context.current_instrument_type)
        
        # Enter context with ID
        with self.context.with_instrument(instrument_id=42):
            self.assertEqual(self.context.current_instrument_id, 42)
            self.assertIsNone(self.context.current_instrument_type)
            
        # Context should be restored after block
        self.assertIsNone(self.context.current_instrument_id)
        self.assertIsNone(self.context.current_instrument_type)
        
        # Enter context with type
        with self.context.with_instrument(instrument_type="MACROSYNTH"):
            self.assertIsNone(self.context.current_instrument_id)
            self.assertEqual(self.context.current_instrument_type, "MACROSYNTH")
            
        # Context should be restored
        self.assertIsNone(self.context.current_instrument_id)
        self.assertIsNone(self.context.current_instrument_type)
        
    def test_nested_context_blocks(self):
        """Test that nested context blocks work correctly."""
        # Set up initial context
        self.context.current_instrument_id = 1
        self.context.current_instrument_type = "WAVSYNTH"
        
        # First nested block - only set instrument_id
        with self.context.with_instrument(instrument_id=2):
            self.assertEqual(self.context.current_instrument_id, 2)
            # The current_instrument_type should be preserved in this case
            self.assertEqual(self.context.current_instrument_type, "WAVSYNTH")
            
            # Second nested block - only set instrument_type
            with self.context.with_instrument(instrument_type="MACROSYNTH"):
                self.assertEqual(self.context.current_instrument_id, 2)
                self.assertEqual(self.context.current_instrument_type, "MACROSYNTH")
                
            # Back to first block
            self.assertEqual(self.context.current_instrument_id, 2)
            self.assertEqual(self.context.current_instrument_type, "WAVSYNTH")
            
        # Back to original context
        self.assertEqual(self.context.current_instrument_id, 1)
        self.assertEqual(self.context.current_instrument_type, "WAVSYNTH")
        
    def test_clear_context(self):
        """Test clearing the context."""
        self.context.current_instrument_id = 5
        self.context.current_instrument_type = "SAMPLER"
        self.context.project = MagicMock()
        
        self.context.clear()
        
        self.assertIsNone(self.context.current_instrument_id)
        self.assertIsNone(self.context.current_instrument_type)
        self.assertIsNone(self.context.project)

class TestInstrumentContextBlock(unittest.TestCase):
    """Test the _InstrumentContextBlock private class."""
    
    def setUp(self):
        """Set up a fresh context block for testing."""
        self.context_manager = MagicMock()
        self.context_manager.current_instrument_id = None
        self.context_manager.current_instrument_type = None
        
    def test_enter_exit(self):
        """Test entering and exiting the context block."""
        # Set up initial state
        self.context_manager.current_instrument_id = 1
        self.context_manager.current_instrument_type = "WAVSYNTH"
        
        # Create block
        block = _InstrumentContextBlock(
            self.context_manager, 
            instrument_id=2, 
            instrument_type="MACROSYNTH"
        )
        
        # Enter the block
        result = block.__enter__()
        
        # Check context was updated
        self.assertEqual(self.context_manager.current_instrument_id, 2)
        self.assertEqual(self.context_manager.current_instrument_type, "MACROSYNTH")
        self.assertEqual(result, self.context_manager)
        
        # Exit the block
        block.__exit__(None, None, None)
        
        # Check context was restored
        self.assertEqual(self.context_manager.current_instrument_id, 1)
        self.assertEqual(self.context_manager.current_instrument_type, "WAVSYNTH")


if __name__ == '__main__':
    unittest.main()