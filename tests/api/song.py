import unittest
from m8.api.song import M8SongRow, M8SongMatrix, COL_COUNT, ROW_COUNT
from m8.api import M8ValidationError

class TestM8SongRow(unittest.TestCase):
    def test_read_from_binary(self):
        # Test case 1: Reading a row with some chain references
        test_data = bytes([1, 2, 3, 4, M8SongRow.EMPTY_CHAIN, 6, 7, 8])
        row = M8SongRow.read(test_data)
        
        self.assertEqual(row[0], 1)
        self.assertEqual(row[1], 2)
        self.assertEqual(row[2], 3)
        self.assertEqual(row[3], 4)
        self.assertEqual(row[4], M8SongRow.EMPTY_CHAIN)
        self.assertEqual(row[5], 6)
        self.assertEqual(row[6], 7)
        self.assertEqual(row[7], 8)
        
        # Test case 2: Reading an empty row
        test_data = bytes([M8SongRow.EMPTY_CHAIN] * COL_COUNT)
        row = M8SongRow.read(test_data)
        self.assertTrue(row.is_empty())
        
        # Test case 3: Reading data that's too short (should be padded)
        test_data = bytes([1, 2, 3])  # Only 3 bytes
        row = M8SongRow.read(test_data)
        # Should read first 3 bytes and leave rest as defaults
        self.assertEqual(row[0], 1)
        self.assertEqual(row[1], 2)
        self.assertEqual(row[2], 3)
    
    def test_write_to_binary(self):
        # Test case 1: Writing a row with some chain references
        row = M8SongRow()
        row[0] = 10
        row[3] = 20
        row[7] = 30
        
        binary = row.write()
        expected = bytes([10, M8SongRow.EMPTY_CHAIN, M8SongRow.EMPTY_CHAIN, 20, 
                         M8SongRow.EMPTY_CHAIN, M8SongRow.EMPTY_CHAIN, M8SongRow.EMPTY_CHAIN, 30])
        self.assertEqual(binary, expected)
        
        # Test case 2: Writing an empty row
        row = M8SongRow()
        binary = row.write()
        expected = bytes([M8SongRow.EMPTY_CHAIN] * COL_COUNT)
        self.assertEqual(binary, expected)
    
    def test_read_write_consistency(self):
        # Test binary serialization/deserialization consistency
        test_cases = [
            # Test case 1: Empty row
            bytes([M8SongRow.EMPTY_CHAIN] * COL_COUNT),
            # Test case 2: Row with all positions filled
            bytes(range(COL_COUNT)),
            # Test case 3: Row with some positions filled
            bytes([1, M8SongRow.EMPTY_CHAIN, 3, M8SongRow.EMPTY_CHAIN, 5, M8SongRow.EMPTY_CHAIN, 7, M8SongRow.EMPTY_CHAIN])
        ]
        
        for test_data in test_cases:
            # Read from binary
            original = M8SongRow.read(test_data)
            
            # Write to binary
            binary = original.write()
            
            # Read again from binary
            deserialized = M8SongRow.read(binary)
            
            # Compare the two row objects
            for i in range(COL_COUNT):
                self.assertEqual(deserialized[i], original[i])
    
    def test_constructor_and_kwargs(self):
        # Test default constructor
        row = M8SongRow()
        for i in range(COL_COUNT):
            self.assertEqual(row[i], M8SongRow.EMPTY_CHAIN)
        
        # Test constructor with kwargs
        row = M8SongRow(col0=10, col3=20, col7=30)
        self.assertEqual(row[0], 10)
        self.assertEqual(row[1], M8SongRow.EMPTY_CHAIN)
        self.assertEqual(row[2], M8SongRow.EMPTY_CHAIN)
        self.assertEqual(row[3], 20)
        self.assertEqual(row[4], M8SongRow.EMPTY_CHAIN)
        self.assertEqual(row[5], M8SongRow.EMPTY_CHAIN)
        self.assertEqual(row[6], M8SongRow.EMPTY_CHAIN)
        self.assertEqual(row[7], 30)
        
        # Test with invalid kwargs
        row = M8SongRow(col9=40, invalid=50)  # Should ignore these
        for i in range(COL_COUNT):
            self.assertEqual(row[i], M8SongRow.EMPTY_CHAIN)
    
    def test_getitem_setitem(self):
        row = M8SongRow()
        
        # Test __setitem__
        row[0] = 10
        row[7] = 20
        
        # Test __getitem__
        self.assertEqual(row[0], 10)
        self.assertEqual(row[7], 20)
        
        # Test out of bounds access
        with self.assertRaises(IndexError):
            _ = row[-1]
        
        with self.assertRaises(IndexError):
            _ = row[COL_COUNT]
        
        with self.assertRaises(IndexError):
            row[-1] = 30
        
        with self.assertRaises(IndexError):
            row[COL_COUNT] = 30
    
    def test_is_empty(self):
        # Test is_empty method
        row = M8SongRow()
        self.assertTrue(row.is_empty())
        
        row[0] = 10
        self.assertFalse(row.is_empty())
        
        row[0] = M8SongRow.EMPTY_CHAIN
        self.assertTrue(row.is_empty())
    
    def test_clone(self):
        # Test clone method
        original = M8SongRow()
        original[0] = 10
        original[3] = 20
        
        clone = original.clone()
        
        # Verify clone has the same values
        for i in range(COL_COUNT):
            self.assertEqual(clone[i], original[i])
        
        # Verify clone is a different object
        self.assertIsNot(clone, original)
        
        # Modify clone and verify original remains unchanged
        clone[0] = 30
        self.assertEqual(original[0], 10)
    
    def test_validate_chains(self):
        # Mock chains list for validation
        mock_chains = [
            type('MockChain', (), {'is_empty': lambda: False}),  # Chain 0 (not empty)
            type('MockChain', (), {'is_empty': lambda: False}),  # Chain 1 (not empty)
            type('MockChain', (), {'is_empty': lambda: True}),   # Chain 2 (empty)
        ]
        
        # Test case 1: Valid row
        row = M8SongRow()
        row[0] = 0  # References valid chain 0
        row[1] = 1  # References valid chain 1
        row.validate_chains(mock_chains)  # Should not raise exception
        
        # Test case 2: Reference to non-existent chain
        row = M8SongRow()
        row[0] = 5  # References chain 5, which doesn't exist
        with self.assertRaises(M8ValidationError):
            row.validate_chains(mock_chains)
        
        # Test case 3: Reference to empty chain
        row = M8SongRow()
        row[0] = 2  # References chain 2, which is empty
        with self.assertRaises(M8ValidationError):
            row.validate_chains(mock_chains)
        
        # Test case 4: Empty row should always be valid
        row = M8SongRow()
        row.validate_chains([])  # Should not raise exception even with empty chains list
    
    def test_as_dict(self):
        # Test as_dict method
        row = M8SongRow()
        row[1] = 10
        row[3] = 20
        row[5] = 30
        
        result = row.as_dict()
        
        # Should contain only non-empty chain references
        expected = {
            "chains": [
                {"col": 1, "chain": 10},
                {"col": 3, "chain": 20},
                {"col": 5, "chain": 30}
            ]
        }
        
        # Compare dictionaries (order of chains array may vary)
        self.assertEqual(len(result["chains"]), len(expected["chains"]))
        for chain_entry in expected["chains"]:
            self.assertIn(chain_entry, result["chains"])
        
        # Test empty row
        row = M8SongRow()
        result = row.as_dict()
        self.assertEqual(result, {"chains": []})
    
    def test_from_dict(self):
        # Test from_dict method
        data = {
            "chains": [
                {"col": 0, "chain": 10},
                {"col": 4, "chain": 20},
                {"col": 7, "chain": 30}
            ]
        }
        
        row = M8SongRow.from_dict(data)
        
        self.assertEqual(row[0], 10)
        self.assertEqual(row[4], 20)
        self.assertEqual(row[7], 30)
        self.assertEqual(row[1], M8SongRow.EMPTY_CHAIN)  # Not specified in dict
        
        # Test with invalid column index
        data = {
            "chains": [
                {"col": 9, "chain": 40}  # Out of range
            ]
        }
        
        row = M8SongRow.from_dict(data)
        for i in range(COL_COUNT):
            self.assertEqual(row[i], M8SongRow.EMPTY_CHAIN)


class TestM8SongMatrix(unittest.TestCase):
    def test_read_from_binary(self):
        # Create test binary data (simplified for testing)
        # Just 2 rows for simplicity
        test_data = bytearray()
        
        # Row 0: [1, 2, 3, 4, EMPTY, 6, 7, 8]
        test_data.extend([1, 2, 3, 4, M8SongRow.EMPTY_CHAIN, 6, 7, 8])
        
        # Row 1: [EMPTY, EMPTY, 9, EMPTY, EMPTY, EMPTY, EMPTY, 10]
        test_data.extend([M8SongRow.EMPTY_CHAIN, M8SongRow.EMPTY_CHAIN, 9, 
                         M8SongRow.EMPTY_CHAIN, M8SongRow.EMPTY_CHAIN, 
                         M8SongRow.EMPTY_CHAIN, M8SongRow.EMPTY_CHAIN, 10])
        
        # Fill the rest with empty rows
        test_data.extend([M8SongRow.EMPTY_CHAIN] * (ROW_COUNT - 2) * COL_COUNT)
        
        # Read from binary
        matrix = M8SongMatrix.read(test_data)
        
        # Test row 0
        self.assertEqual(matrix[0][0], 1)
        self.assertEqual(matrix[0][1], 2)
        self.assertEqual(matrix[0][2], 3)
        self.assertEqual(matrix[0][3], 4)
        self.assertEqual(matrix[0][4], M8SongRow.EMPTY_CHAIN)
        self.assertEqual(matrix[0][5], 6)
        self.assertEqual(matrix[0][6], 7)
        self.assertEqual(matrix[0][7], 8)
        
        # Test row 1
        self.assertEqual(matrix[1][0], M8SongRow.EMPTY_CHAIN)
        self.assertEqual(matrix[1][1], M8SongRow.EMPTY_CHAIN)
        self.assertEqual(matrix[1][2], 9)
        self.assertEqual(matrix[1][3], M8SongRow.EMPTY_CHAIN)
        self.assertEqual(matrix[1][4], M8SongRow.EMPTY_CHAIN)
        self.assertEqual(matrix[1][5], M8SongRow.EMPTY_CHAIN)
        self.assertEqual(matrix[1][6], M8SongRow.EMPTY_CHAIN)
        self.assertEqual(matrix[1][7], 10)
        
        # Verify all other rows are empty
        for i in range(2, ROW_COUNT):
            self.assertTrue(matrix[i].is_empty())
    
    def test_write_to_binary(self):
        # Create a matrix with some data
        matrix = M8SongMatrix()
        
        # Set up row 0
        matrix[0][0] = 1
        matrix[0][1] = 2
        
        # Set up row 2 (skipping row 1)
        matrix[2][3] = 3
        matrix[2][4] = 4
        
        # Write to binary
        binary = matrix.write()
        
        # Verify size
        self.assertEqual(len(binary), ROW_COUNT * COL_COUNT)
        
        # Verify row 0
        self.assertEqual(binary[0], 1)
        self.assertEqual(binary[1], 2)
        self.assertEqual(binary[2], M8SongRow.EMPTY_CHAIN)
        
        # Verify row 1 (empty)
        for i in range(COL_COUNT):
            self.assertEqual(binary[COL_COUNT + i], M8SongRow.EMPTY_CHAIN)
        
        # Verify row 2
        self.assertEqual(binary[2 * COL_COUNT + 3], 3)
        self.assertEqual(binary[2 * COL_COUNT + 4], 4)
    
    def test_read_write_consistency(self):
        # Create a matrix with some data
        matrix = M8SongMatrix()
        
        # Modify some rows
        matrix[0][0] = 1
        matrix[0][1] = 2
        matrix[5][3] = 10
        matrix[5][4] = 20
        matrix[10][7] = 30
        
        # Write to binary
        binary = matrix.write()
        
        # Read back from binary
        deserialized = M8SongMatrix.read(binary)
        
        # Verify consistency for all rows and columns
        for row_idx in range(ROW_COUNT):
            for col_idx in range(COL_COUNT):
                self.assertEqual(deserialized[row_idx][col_idx], matrix[row_idx][col_idx])
    
    def test_constructor(self):
        # Test default constructor
        matrix = M8SongMatrix()
        
        # Should have ROW_COUNT rows
        self.assertEqual(len(matrix), ROW_COUNT)
        
        # All rows should be empty
        for row in matrix:
            self.assertTrue(row.is_empty())
    
    def test_is_empty(self):
        # Test is_empty method
        matrix = M8SongMatrix()
        self.assertTrue(matrix.is_empty())
        
        # Modify one cell
        matrix[0][0] = 1
        self.assertFalse(matrix.is_empty())
        
        # Reset to empty
        matrix[0][0] = M8SongRow.EMPTY_CHAIN
        self.assertTrue(matrix.is_empty())
    
    def test_clone(self):
        # Test clone method
        original = M8SongMatrix()
        original[0][0] = 1
        original[5][3] = 2
        
        clone = original.clone()
        
        # Verify clone has the same values
        for row_idx in range(ROW_COUNT):
            for col_idx in range(COL_COUNT):
                self.assertEqual(clone[row_idx][col_idx], original[row_idx][col_idx])
        
        # Verify clone is a different object
        self.assertIsNot(clone, original)
        
        # Modify clone and verify original remains unchanged
        clone[0][0] = 10
        self.assertEqual(original[0][0], 1)
    
    def test_validate_chains(self):
        # Mock chains list for validation
        mock_chains = [
            type('MockChain', (), {'is_empty': lambda: False}),  # Chain 0 (not empty)
            type('MockChain', (), {'is_empty': lambda: False}),  # Chain 1 (not empty)
            type('MockChain', (), {'is_empty': lambda: True}),   # Chain 2 (empty)
        ]
        
        # Test case 1: Valid matrix
        matrix = M8SongMatrix()
        matrix[0][0] = 0  # References valid chain 0
        matrix[1][0] = 1  # References valid chain 1
        matrix.validate_chains(mock_chains)  # Should not raise exception
        
        # Test case 2: Reference to non-existent chain
        matrix = M8SongMatrix()
        matrix[0][0] = 5  # References chain 5, which doesn't exist
        with self.assertRaises(M8ValidationError):
            matrix.validate_chains(mock_chains)
        
        # Test case 3: Reference to empty chain
        matrix = M8SongMatrix()
        matrix[0][0] = 2  # References chain 2, which is empty
        with self.assertRaises(M8ValidationError):
            matrix.validate_chains(mock_chains)
        
        # Test case 4: Empty matrix should always be valid
        matrix = M8SongMatrix()
        matrix.validate_chains([])  # Should not raise exception even with empty chains list
    
    def test_as_list(self):
        # Test as_list method
        matrix = M8SongMatrix()
        
        # Add some data
        matrix[0][0] = 1
        matrix[0][1] = 2
        
        matrix[5][3] = 10
        matrix[5][4] = 20
        
        result = matrix.as_list()
        
        # Should contain only non-empty rows
        self.assertEqual(len(result), 2)  # Only 2 rows are non-empty
        
        # Verify row 0
        row0 = next(r for r in result if r["index"] == 0)
        self.assertEqual(len(row0["chains"]), 2)
        self.assertIn({"col": 0, "chain": 1}, row0["chains"])
        self.assertIn({"col": 1, "chain": 2}, row0["chains"])
        
        # Verify row 5
        row5 = next(r for r in result if r["index"] == 5)
        self.assertEqual(len(row5["chains"]), 2)
        self.assertIn({"col": 3, "chain": 10}, row5["chains"])
        self.assertIn({"col": 4, "chain": 20}, row5["chains"])
        
        # Test empty matrix
        matrix = M8SongMatrix()
        result = matrix.as_list()
        self.assertEqual(result, [])
    
    def test_from_list(self):
        # Test from_list method
        data = [
            {
                "index": 0,
                "chains": [
                    {"col": 0, "chain": 1},
                    {"col": 1, "chain": 2}
                ]
            },
            {
                "index": 5,
                "chains": [
                    {"col": 3, "chain": 10},
                    {"col": 4, "chain": 20}
                ]
            }
        ]
        
        matrix = M8SongMatrix.from_list(data)
        
        # Verify row 0
        self.assertEqual(matrix[0][0], 1)
        self.assertEqual(matrix[0][1], 2)
        self.assertEqual(matrix[0][2], M8SongRow.EMPTY_CHAIN)
        
        # Verify row 5
        self.assertEqual(matrix[5][3], 10)
        self.assertEqual(matrix[5][4], 20)
        self.assertEqual(matrix[5][0], M8SongRow.EMPTY_CHAIN)
        
        # Verify other rows are empty
        for row_idx in range(ROW_COUNT):
            if row_idx not in (0, 5):
                self.assertTrue(matrix[row_idx].is_empty())
        
        # Test with invalid row index
        data = [
            {
                "index": 300,  # Out of range
                "chains": [
                    {"col": 0, "chain": 1}
                ]
            }
        ]
        
        matrix = M8SongMatrix.from_list(data)
        self.assertTrue(matrix.is_empty())
        
        # Test with empty list
        matrix = M8SongMatrix.from_list([])
        self.assertTrue(matrix.is_empty())

if __name__ == '__main__':
    unittest.main()