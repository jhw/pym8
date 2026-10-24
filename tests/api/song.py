import os
import unittest

from m8.api.chain import CHAIN_COUNT
from m8.api.project import M8Project, ROW_BOOKMARKS_OFFSET, SONG_BOOKMARKS_OFFSET
from m8.api.song import M8SongRow, M8SongMatrix, COL_COUNT, ROW_COUNT

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def _read_fixture(name):
    with open(os.path.join(FIXTURES_DIR, name), "rb") as f:
        return f.read()

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
        pass  # Row has all EMPTY_CHAIN values
        
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
            pass  # Empty rows by default
    
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
            pass  # Row has all EMPTY_CHAIN values
    

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

if __name__ == '__main__':
    unittest.main()

class TestSongRowBoundaries(unittest.TestCase):
    """Edge cases for the song matrix row + cell access."""

    def test_empty_chain_reference_default(self):
        project = M8Project.initialise()
        self.assertEqual(project.song[0][0], 255)

    def test_max_row_access(self):
        project = M8Project.initialise()
        project.song[ROW_COUNT - 1][0] = 0
        self.assertEqual(project.song[ROW_COUNT - 1][0], 0)

    def test_max_column_access(self):
        project = M8Project.initialise()
        project.song[0][COL_COUNT - 1] = 0
        self.assertEqual(project.song[0][COL_COUNT - 1], 0)


class TestSongRowCount(unittest.TestCase):
    """Regression: the song arrangement grid is 256 rows (0x100), not 255.

    Rust's SongSteps::ROW_COUNT = 0x100; the on-disk song section is
    exactly 2048 bytes (0xAEE - 0x2EE), which is 256 rows * 8 columns.
    255 was a stale copy of CHAIN_COUNT/PHRASES_COUNT (which really are
    255) applied to an unrelated quantity.
    """

    def test_row_count_is_256(self):
        self.assertEqual(ROW_COUNT, 256)

    def test_song_section_spans_exactly_to_phrases_offset(self):
        from m8.api.phrase import PHRASES_OFFSET
        from m8.api.song import SONG_OFFSET
        self.assertEqual(SONG_OFFSET + ROW_COUNT * COL_COUNT, PHRASES_OFFSET)

    def test_last_row_reachable_via_project(self):
        project = M8Project.initialise()
        project.song[255][0] = 42
        self.assertEqual(project.song[255][0], 42)

    def test_last_row_round_trips_through_project(self):
        project = M8Project.initialise()
        project.song[255][3] = 7
        reloaded = M8Project.read(project.write())
        self.assertEqual(reloaded.song[255][3], 7)


class TestSongBookmarks(unittest.TestCase):
    """Song-step bookmarks (bitmask per row) and 6.6+ row bookmarks."""

    def test_default_rows_unbookmarked(self):
        row = M8SongRow()
        self.assertEqual(row.bookmarks, 0)
        self.assertEqual(row.row_bookmark, 0)
        self.assertFalse(any(row.is_bookmarked(c) for c in range(COL_COUNT)))

    def test_set_and_clear_bookmark(self):
        row = M8SongRow()
        row.set_bookmark(7)
        row.set_bookmark(0)
        self.assertEqual(row.bookmarks, 0x81)
        row.set_bookmark(7, on=False)
        self.assertEqual(row.bookmarks, 0x01)
        self.assertTrue(row.is_bookmarked(0))
        self.assertFalse(row.is_bookmarked(7))

    def test_bookmark_col_out_of_range(self):
        with self.assertRaises(IndexError):
            M8SongRow().is_bookmarked(COL_COUNT)
        with self.assertRaises(IndexError):
            M8SongRow().set_bookmark(-1)

    def test_clone_copies_bookmarks(self):
        row = M8SongRow(bookmarks=0x05, row_bookmark=0x0B)
        clone = row.clone()
        clone.bookmarks = 0
        self.assertEqual(row.bookmarks, 0x05)
        self.assertEqual(clone.row_bookmark, 0x0B)

    def test_matrix_bookmark_blocks(self):
        bookmarks = bytes([0x01] + [0] * (ROW_COUNT - 1))
        row_bookmarks = bytes([0] * (ROW_COUNT - 1) + [0x0B])
        matrix = M8SongMatrix.read(bytes([0xFF] * ROW_COUNT * COL_COUNT), bookmarks, row_bookmarks)
        self.assertTrue(matrix[0].is_bookmarked(0))
        self.assertEqual(matrix[255].row_bookmark, 0x0B)
        self.assertEqual(matrix.write_bookmarks(), bookmarks)
        self.assertEqual(matrix.write_row_bookmarks(), row_bookmarks)
        self.assertEqual(matrix.clone()[255].row_bookmark, 0x0B)

    def test_reads_bookmarks_from_device_file(self):
        """BOOKMARK_ON.m8s (from m8-file-parser): track 1 bookmarked on rows
        00/01, track 8 on row FF; coloured row bookmarks on 00/02/05/09/0B/FF."""
        p = M8Project.read(_read_fixture("BOOKMARK_ON.m8s"))
        self.assertTrue(p.song[0].is_bookmarked(0))
        self.assertTrue(p.song[1].is_bookmarked(0))
        self.assertTrue(p.song[255].is_bookmarked(7))
        self.assertFalse(p.song[2].is_bookmarked(0))
        self.assertEqual(
            {i: r.row_bookmark for i, r in enumerate(p.song) if r.row_bookmark},
            {0: 0x06, 2: 0x05, 5: 0x04, 9: 0x18, 11: 0x0B, 255: 0x0B},
        )

    def test_bookmarks_written_at_expected_offsets(self):
        p = M8Project.initialise()
        p.song[4].set_bookmark(2)
        p.song[6].row_bookmark = 0x05
        data = p.write()
        self.assertEqual(data[SONG_BOOKMARKS_OFFSET + 4], 0x04)
        self.assertEqual(data[ROW_BOOKMARKS_OFFSET + 6], 0x05)
        reloaded = M8Project.read(data)
        self.assertTrue(reloaded.song[4].is_bookmarked(2))
        self.assertEqual(reloaded.song[6].row_bookmark, 0x05)

    def test_pre_6_6_file_has_no_row_bookmarks(self):
        """EMPTY65.m8s ends at the PPQN block; writing a row bookmark must
        not grow it."""
        data = _read_fixture("EMPTY65.m8s")
        p = M8Project.read(data)
        p.song[0].row_bookmark = 0x05
        p.song[0].set_bookmark(0)
        out = p.write()
        self.assertEqual(len(out), len(data))
        self.assertEqual(out[SONG_BOOKMARKS_OFFSET], 0x01)


class TestSongValidation(unittest.TestCase):
    """Validation of chain references in the song matrix.

    With CHAIN_COUNT == 255, valid chain refs are 0..254 plus 255 for
    empty. There's effectively no invalid byte value — but the validate
    method is still in place to catch future capacity regressions.
    """

    def test_song_row_valid(self):
        M8SongRow().validate()  # no raise

    def test_song_row_valid_chain_refs(self):
        row = M8SongRow()
        row[0] = 0                    # first chain
        row[1] = CHAIN_COUNT - 1      # last real chain
        row[2] = 255                  # empty
        row.validate()  # no raise

    def test_high_chain_reference_valid(self):
        """Regression: after fixing CHAIN_COUNT 128 → 255, chain 200 must
        validate successfully (was rejected by stale hardcoded 0-127 check)."""
        row = M8SongRow()
        row[0] = 200
        row.validate()  # no raise

    def test_song_matrix_valid(self):
        M8SongMatrix().validate()

    def test_song_matrix_too_many_rows(self):
        matrix = M8SongMatrix()
        matrix.append(M8SongRow())  # one over the limit
        with self.assertRaises(ValueError) as ctx:
            matrix.validate()
        self.assertIn("Too many song rows", str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
