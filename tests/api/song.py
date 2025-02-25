import unittest
from unittest.mock import MagicMock, patch

from m8 import NULL
from m8.api import M8ValidationError, BLANK
from m8.api.song import M8SongRow, M8SongMatrix
from m8.api.chains import M8Chain


class TestM8Song(unittest.TestCase):
    def setUp(self):
        # Create a mock chain list for validation tests
        self.mock_chains = []
        for i in range(5):
            chain = MagicMock(spec=M8Chain)
            # Only chains 0, 2, and 4 are "filled"
            chain.is_empty.return_value = (i % 2 != 0)
            self.mock_chains.append(chain)

    def test_song_row_validation(self):
        """Test validation of chains in a song row"""
        row = M8SongRow()
        
        # Insert valid chain references
        row[0] = 0  # Valid chain index
        row[3] = 2  # Valid chain index
        row[7] = 4  # Valid chain index
        
        # Validation should pass
        row.validate_chains(self.mock_chains)
        
        # Insert reference to empty chain
        row[1] = 1  # This is an empty chain
        with self.assertRaises(M8ValidationError) as context:
            row.validate_chains(self.mock_chains)
        self.assertIn("empty chain", str(context.exception))
        
        # Reset and test out-of-range chain reference
        row[1] = BLANK  # Reset to default
        row[5] = 10  # Out of range
        with self.assertRaises(M8ValidationError) as context:
            row.validate_chains(self.mock_chains)
        self.assertIn("non-existent", str(context.exception))

    def test_song_matrix_validation(self):
        """Test validation of chains across a song matrix"""
        matrix = M8SongMatrix()
        
        # Set up a few rows with valid references
        matrix[0][0] = 0
        matrix[0][7] = 4
        matrix[5][3] = 2
        
        # Validation should pass
        matrix.validate_chains(self.mock_chains)
        
        # Add an invalid chain reference
        matrix[10][2] = 7  # Out of range
        
        # Validation should fail with a specific error message
        with self.assertRaises(M8ValidationError) as context:
            matrix.validate_chains(self.mock_chains)
        # Check that the row number is included in the error
        self.assertIn("Row 10", str(context.exception))
        
        # Add an empty chain reference
        matrix[10][2] = BLANK  # Reset to valid
        matrix[20][4] = 1  # Empty chain
        
        # Validation should fail
        with self.assertRaises(M8ValidationError) as context:
            matrix.validate_chains(self.mock_chains)
        # Check that the row number is included in the error
        self.assertIn("Row 20", str(context.exception))

    def test_matrix_row_isolation(self):
        """Test that changes to one row don't affect other rows"""
        matrix = M8SongMatrix()
        
        # Modify one row
        matrix[5][2] = 42
        
        # Check that other rows are unchanged
        for i in range(255):
            if i != 5:
                row = matrix[i]
                self.assertTrue(all(cell == BLANK for cell in row))
                
        # Specifically check neighboring rows
        self.assertEqual(matrix[4][2], BLANK)
        self.assertEqual(matrix[6][2], BLANK)
        
        # Verify the changed row
        self.assertEqual(matrix[5][2], 42)

    def test_row_independence(self):
        """Test that rows are independent objects"""
        matrix = M8SongMatrix()
        
        # Get two row references
        row1 = matrix[10]
        row2 = matrix[20]
        
        # Modify row1
        row1[3] = 42
        
        # row2 should be unaffected
        self.assertEqual(row2[3], BLANK)
        
        # Matrix access should reflect the change
        self.assertEqual(matrix[10][3], 42)
        self.assertEqual(matrix[20][3], BLANK)
        
        # Try modifying through the matrix
        matrix[10][5] = 99
        
        # row1 reference should reflect the change
        self.assertEqual(row1[5], 99)

    @patch('m8.api.song.M8SongRowBase.write')
    def test_row_serialization(self, mock_write):
        """Test that song rows are properly serialized"""
        # Setup mock return value for write
        mock_write.return_value = b'\xFF\x01\x02\x03\x04\x05\x06\x07'
        
        row = M8SongRow()
        
        # Call write and verify it delegates to parent class
        result = row.write()
        mock_write.assert_called_once()
        self.assertEqual(result, b'\xFF\x01\x02\x03\x04\x05\x06\x07')

    @patch('m8.api.song.M8SongMatrixBase.write')
    def test_matrix_serialization(self, mock_write):
        """Test that song matrices are properly serialized"""
        # Setup mock return value for write
        mock_data = bytes([0xFF] * 2040)  # 8 bytes per row * 255 rows
        mock_write.return_value = mock_data
        
        matrix = M8SongMatrix()
        
        # Call write and verify it delegates to parent class
        result = matrix.write()
        mock_write.assert_called_once()
        self.assertEqual(result, mock_data)
        self.assertEqual(len(result), 8 * 255)  # Correct size


if __name__ == '__main__':
    unittest.main()
