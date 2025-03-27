import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from m8.api import M8ValidationResult
from m8.api.project import M8Project
from m8.api.instruments import M8Instrument
from m8.api.chains import M8Chain, M8ChainStep
from m8.api.phrases import M8Phrase
from m8.tools.bake_chains import ChainBaker, main


class TestBakeChains(unittest.TestCase):
    def setUp(self):
        """Set up temporary directory and test project."""
        # Create temp dir in project root
        tmp_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tmp")
        os.makedirs(tmp_root, exist_ok=True)
        self.temp_dir = os.path.join(tmp_root, f"test_bake_chains_{os.getpid()}")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.input_file = os.path.join(self.temp_dir, "test_project.m8s")
        self.output_file = os.path.join(self.temp_dir, "test_project-baked.m8s")
        
        # Create test project with a square block of chains
        self.project = self.create_test_project()
        self.project.write_to_file(self.input_file)
    
    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)
    
    def create_test_project(self):
        """Create a test project with a square matrix of chains in the song."""
        project = M8Project.initialise()
        
        # Add an instrument
        instrument = M8Instrument(instrument_type="WAVSYNTH", name="TestInst")
        inst_idx = project.add_instrument(instrument)
        
        # Create phrases (each with one note)
        # Create a 3x3 matrix of phrases and chains
        for i in range(9):
            phrase = M8Phrase()
            phrase[0].note = 60 + i  # C4 through G#4
            phrase[0].instrument = inst_idx
            
            phrase_idx = i
            project.set_phrase(phrase, phrase_idx)
            
            # Create matching chain (one-to-one pattern)
            chain = M8Chain()
            chain[0].phrase = phrase_idx
            project.set_chain(chain, phrase_idx)
        
        # Add chains to song matrix in a 3x3 pattern
        # A1 B1 C1
        # A2 B2 C2
        # A3 B3 C3
        matrix = [
            [(0, 0), (1, 1), (2, 2)],  # Row 0: chains 0, 1, 2
            [(0, 3), (1, 4), (2, 5)],  # Row 1: chains 3, 4, 5
            [(0, 6), (1, 7), (2, 8)]   # Row 2: chains 6, 7, 8
        ]
        
        for row_idx, row in enumerate(matrix):
            for col_idx, chain_id in row:
                project.song[row_idx][col_idx] = chain_id
        
        # Add a second block with a gap in between
        for row_idx in range(5, 7):
            for col_idx in range(0, 2):
                chain_id = (row_idx-5)*2 + col_idx
                project.song[row_idx][col_idx] = chain_id
        
        return project
    
    def test_identify_chain_blocks(self):
        """Test identify_chain_blocks method."""
        chain_baker = ChainBaker()
        blocks = chain_baker.identify_chain_blocks(self.project.song)
        self.assertEqual(len(blocks), 2, "Should identify two blocks")
        
        # First block should be 3x3 starting at row 0
        start_row, block = blocks[0]
        self.assertEqual(start_row, 0, "First block should start at row 0")
        self.assertEqual(len(block), 3, "First block should have 3 rows")
        for row in block:
            self.assertEqual(len(row), 3, "Each row should have 3 chains")
        
        # Second block should be 2x2 starting at row 5
        start_row, block = blocks[1]
        self.assertEqual(start_row, 5, "Second block should start at row 5")
        self.assertEqual(len(block), 2, "Second block should have 2 rows")
        for row in block:
            self.assertEqual(len(row), 2, "Each row should have 2 chains")
    
    def test_validate_block_is_square(self):
        """Test validate_block_is_square method."""
        chain_baker = ChainBaker()
        
        # Empty block
        dims = chain_baker.validate_block_is_square([])
        self.assertEqual(dims, (0, 0), "Empty block should return (0, 0)")
        
        # Valid square block 3x3
        valid_block = [
            [(0, 0), (1, 1), (2, 2)],
            [(0, 3), (1, 4), (2, 5)],
            [(0, 6), (1, 7), (2, 8)]
        ]
        dims = chain_baker.validate_block_is_square(valid_block)
        self.assertEqual(dims, (3, 3), "Should correctly identify 3x3 block")
        
        # Non-rectangular block
        non_rectangular = [
            [(0, 0), (1, 1), (2, 2)],
            [(0, 3), (1, 4)],
            [(0, 6), (1, 7), (2, 8)]
        ]
        with self.assertRaises(ValueError):
            chain_baker.validate_block_is_square(non_rectangular)
        
        # Rectangular but not square
        rectangular = [
            [(0, 0), (1, 1), (2, 2)],
            [(0, 3), (1, 4), (2, 5)]
        ]
        with self.assertRaises(ValueError):
            chain_baker.validate_block_is_square(rectangular)
    
    @patch('builtins.input')
    def test_prompt_for_blocks(self, mock_input):
        """Test prompt_for_blocks method."""
        chain_baker = ChainBaker()
        chain_baker.project = self.project
        chain_baker.blocks = chain_baker.identify_chain_blocks(self.project.song)
        
        # User selects all blocks
        mock_input.side_effect = ['y', 'y']
        selected = chain_baker.prompt_for_blocks()
        self.assertEqual(len(selected), 2)
        
        # User selects no blocks
        mock_input.side_effect = ['n', 'n']
        selected = chain_baker.prompt_for_blocks()
        self.assertEqual(len(selected), 0)
        
        # User quits - this behavior may be different than expected
        # When the user quits, the implementation returns an empty list
        mock_input.side_effect = ['y', 'q']
        selected = chain_baker.prompt_for_blocks()
        self.assertEqual(len(selected), 0)
    
    def test_calculate_new_id(self):
        """Test calculate_new_id method."""
        chain_baker = ChainBaker()
        self.assertEqual(chain_baker.calculate_new_id(0, 0), 0)
        self.assertEqual(chain_baker.calculate_new_id(5, 1), 15)
        self.assertEqual(chain_baker.calculate_new_id(3, 2), 23)
    
    def test_bake_chain_block(self):
        """Test bake_chain_block method."""
        chain_baker = ChainBaker()
        chain_baker.project = self.project
        chain_baker.blocks = chain_baker.identify_chain_blocks(self.project.song)
        start_row, block = chain_baker.blocks[0]  # Use the first 3x3 block
        
        # Count original non-empty chains
        original_non_empty = sum(1 for chain in self.project.chains if not chain.is_empty())
        
        # Bake the chains
        target_row = 10
        new_chain_ids = chain_baker.bake_chain_block((start_row, block), target_row)
        
        # Verify new chains were created
        self.assertEqual(len(new_chain_ids), 3, "Should create 3 new chains")
        
        # Check original chains are still there (they're not deleted)
        current_non_empty = sum(1 for chain in self.project.chains if not chain.is_empty())
        self.assertEqual(current_non_empty, original_non_empty + 3, 
                         "Should have 3 more non-empty chains")
        
        # Check original block is blanked out in song matrix
        for row_idx in range(3):
            for col_idx in range(3):
                self.assertEqual(self.project.song[row_idx][col_idx], M8ChainStep.EMPTY_PHRASE,
                               f"Cell {row_idx},{col_idx} should be empty")
        
        # Check new chains are placed in the correct row
        for col_idx in range(3):
            self.assertEqual(self.project.song[target_row][col_idx], new_chain_ids[col_idx],
                           f"New chain should be at row {target_row}, column {col_idx}")
    
    @patch('builtins.input')
    def test_bake_chains(self, mock_input):
        """Test bake_chains method."""
        # User selects all blocks
        mock_input.side_effect = ['y', 'y']
        
        # Count original non-empty chains
        original_non_empty = sum(1 for chain in self.project.chains if not chain.is_empty())
        
        # Create chain baker and setup for baking
        chain_baker = ChainBaker()
        chain_baker.project = self.project
        chain_baker.identify_chain_blocks(self.project.song)
        
        # The mock input will cause all blocks to be selected
        # Bake the chains
        output_project = chain_baker.bake_chains()
        
        # Verify output project is valid
        output_project.validate_references()
        
        # Check new chains were created
        current_non_empty = sum(1 for chain in output_project.chains if not chain.is_empty())
        self.assertGreater(current_non_empty, original_non_empty, 
                          "Should have more non-empty chains")
        
        # Check original blocks are blanked out
        for row_idx in range(3):
            for col_idx in range(3):
                self.assertEqual(output_project.song[row_idx][col_idx], M8ChainStep.EMPTY_PHRASE,
                               f"Cell {row_idx},{col_idx} in first block should be empty")
                
        for row_idx in range(5, 7):
            for col_idx in range(2):
                self.assertEqual(output_project.song[row_idx][col_idx], M8ChainStep.EMPTY_PHRASE,
                               f"Cell {row_idx},{col_idx} in second block should be empty")
        
        # Check that we have the correct number of new rows with chains
        # New rows should be at positions 0 and 1 since we have 2 blocks
        new_rows_with_chains = 0
        for row_idx in range(255):  # ROW_COUNT is 255 in m8.api.song
            if row_idx not in [0, 1, 2, 5, 6] and not output_project.song[row_idx].is_empty():
                new_rows_with_chains += 1
        
        self.assertEqual(new_rows_with_chains, len(chain_baker.blocks),
                        f"Should create {len(chain_baker.blocks)} new rows with chains")
    
    @patch('m8.tools.bake_chains.ChainBaker.prompt_for_blocks')
    def test_main_function(self, mock_prompt):
        """Test the main function."""
        # Mock blocks selection
        mock_prompt.return_value = [(0, [[(0, 0), (1, 1), (2, 2)], [(0, 3), (1, 4), (2, 5)], [(0, 6), (1, 7), (2, 8)]]), 
                                   (5, [[(0, 0), (1, 1)], [(0, 3), (1, 4)]])]
        
        # Run main with arguments
        with patch('sys.argv', ['bake_chains.py', self.input_file]):
            # Should complete successfully
            self.assertEqual(main(), 0)
            
            # Check output file was created
            output_file = f"{os.path.splitext(self.input_file)[0]}-baked.m8s"
            self.assertTrue(os.path.exists(output_file))
            
            # Load output file and validate
            output_project = M8Project.read_from_file(output_file)
            # After baking chains, the one-to-one relationship won't be preserved
            # because we're creating multi-phrase chains
            # Instead, we'll just validate references which checks for valid pointers
            output_project.validate_references()  # This doesn't return a value, just validates
            
            # Check that the number of new song rows with chains matches the number of blocks
            # Original rows with chains: 0, 1, 2, 5, 6
            # New rows should be created for the 2 blocks selected
            new_rows_with_chains = 0
            for row_idx in range(255):  # ROW_COUNT is 255 in m8.api.song
                if row_idx not in [0, 1, 2, 5, 6] and not output_project.song[row_idx].is_empty():
                    new_rows_with_chains += 1
            
            self.assertEqual(new_rows_with_chains, 2,
                            "Should create 2 new rows with chains")
    
    @patch('m8.tools.bake_chains.ChainBaker.prompt_for_blocks')
    def test_main_nonexistent_file(self, mock_prompt):
        """Test main with non-existent file."""
        with patch('sys.argv', ['bake_chains.py', os.path.join(self.temp_dir, "nonexistent.m8s")]):
            self.assertEqual(main(), 1)
    
    @patch('m8.tools.bake_chains.ChainBaker.prompt_for_blocks')
    def test_main_no_blocks(self, mock_prompt):
        """Test main with no blocks selected."""
        mock_prompt.return_value = []
        
        with patch('sys.argv', ['bake_chains.py', self.input_file]):
            self.assertEqual(main(), 0)  # Should still succeed, just not modify anything


if __name__ == '__main__':
    unittest.main()