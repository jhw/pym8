import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from m8.api import M8Block
from m8.api.project import M8Project
from m8.api.instruments import M8Instrument, M8Instruments
from m8.api.chains import M8Chain, M8Chains
from m8.api.phrases import M8Phrase, M8Phrases
from m8.tools.concat_phrases import get_m8s_files, prompt_for_files, calculate_new_id, concat_projects, main


class TestConcatPhrases(unittest.TestCase):
    def setUp(self):
        """Set up temporary directory and test projects."""
        # Create temp dir
        self.temp_dir = tempfile.mkdtemp()
        self.out_file = os.path.join(self.temp_dir, "output.m8s")
        
        # Create test projects directory
        self.test_projects_dir = os.path.join(self.temp_dir, "test_projects")
        os.makedirs(self.test_projects_dir)
        
        # Create test projects
        self.project_paths = []
        for i in range(3):
            project = self.create_test_project(i)
            path = os.path.join(self.test_projects_dir, f"project_{i}.m8s")
            project.write_to_file(path)
            self.project_paths.append(path)
    
    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)
    
    def create_test_project(self, project_num):
        """Create a test project with one-to-one chain structure."""
        project = M8Project.initialise()
        
        # Add an instrument
        instrument = M8Instrument(instrument_type="wavsynth", name=f"TestInst{project_num}")
        inst_idx = project.add_instrument(instrument)
        
        # Create 3 phrases with one-to-one chains
        for i in range(3):
            phrase = M8Phrase()
            # Add a note that uses our instrument
            phrase[0].note = 60 + i  # C4, C#4, D4
            phrase[0].instrument = inst_idx
            
            phrase_idx = i
            project.set_phrase(phrase, phrase_idx)
            
            # Create matching chain
            chain = M8Chain()
            chain[0].phrase = phrase_idx
            project.set_chain(chain, phrase_idx)
            
            # Add to song matrix
            project.song[i][0] = phrase_idx
        
        return project
    
    def test_get_m8s_files(self):
        """Test get_m8s_files function."""
        # Test with existing directory
        files = get_m8s_files(self.test_projects_dir)
        self.assertEqual(len(files), 3)
        
        # Test with pattern
        files = get_m8s_files(self.test_projects_dir, "_1")
        self.assertEqual(len(files), 1)
        
        # Test with non-existent directory
        with self.assertRaises(FileNotFoundError):
            get_m8s_files(os.path.join(self.temp_dir, "nonexistent"))
        
        # Test with file instead of directory
        with self.assertRaises(NotADirectoryError):
            get_m8s_files(self.project_paths[0])
    
    @patch('builtins.input')
    def test_prompt_for_files(self, mock_input):
        """Test prompt_for_files function."""
        # User selects all files
        mock_input.side_effect = ['y', 'y', 'y']
        selected = prompt_for_files(self.project_paths)
        self.assertEqual(len(selected), 3)
        
        # User selects no files
        mock_input.side_effect = ['n', 'n', 'n']
        selected = prompt_for_files(self.project_paths)
        self.assertEqual(len(selected), 0)
        
        # User quits
        mock_input.side_effect = ['y', 'q']
        selected = prompt_for_files(self.project_paths)
        self.assertEqual(len(selected), 0)
    
    def test_calculate_new_id(self):
        """Test calculate_new_id function."""
        self.assertEqual(calculate_new_id(0, 0, 0), 0)
        self.assertEqual(calculate_new_id(5, 5, 1), 15)
        self.assertEqual(calculate_new_id(23, 3, 2), 23)
    
    def test_concat_projects(self):
        """Test concat_projects function."""
        # Load the test projects
        projects = [M8Project.read_from_file(path) for path in self.project_paths]
        
        # Collect input data for validation
        input_instrument_names = []
        input_phrase_notes = []
        
        for project in projects:
            # Collect instrument info
            for instrument in project.instruments:
                if not isinstance(instrument, M8Block):
                    input_instrument_names.append(instrument.name)
            
            # Collect phrase info (first note value of each phrase as identifier)
            for phrase in project.phrases:
                if not phrase.is_empty():
                    for step in phrase:
                        if step.note != 0xFF:  # Found a note
                            input_phrase_notes.append(step.note)
                            break
        
        # Concatenate projects
        output_project = concat_projects(projects)
        
        # Validate the output project - this checks references 
        output_project.validate_references()
        
        # 1. Check all input instruments are in output (no instrument data loss)
        output_instrument_names = []
        for instrument in output_project.instruments:
            if not isinstance(instrument, M8Block):
                output_instrument_names.append(instrument.name)
                
        self.assertEqual(len(input_instrument_names), len(output_instrument_names),
                        "Number of instruments should match")
        for name in input_instrument_names:
            self.assertIn(name, output_instrument_names, 
                         f"Instrument '{name}' not found in output project")
        
        # 2. Check all input phrase data is present (no phrase data loss)
        output_phrase_notes = []
        for phrase in output_project.phrases:
            if not phrase.is_empty():
                for step in phrase:
                    if step.note != 0xFF:  # Found a note
                        output_phrase_notes.append(step.note)
                        break
        
        self.assertEqual(len(input_phrase_notes), len(output_phrase_notes),
                        "Number of phrases with notes should match")
        for note in input_phrase_notes:
            self.assertIn(note, output_phrase_notes,
                         f"Phrase with note {note} not found in output project")
        
        # 3. Check for ID collisions by verifying one-to-one pattern is maintained
        # (This pattern requires unique chain/phrase pairs)
        self.assertTrue(output_project.validate_one_to_one_chains(),
                       "One-to-one chain-phrase relationship should be maintained")
        
        # 4. Check chains and song matrix reference proper phrases
        used_chain_ids = set()
        used_phrase_ids = set()
        
        # Check chains reference unique phrases
        for chain_idx, chain in enumerate(output_project.chains):
            if not chain.is_empty():
                phrase_id = chain[0].phrase
                self.assertNotIn(phrase_id, used_phrase_ids, 
                               f"Phrase ID {phrase_id} is referenced by multiple chains")
                used_phrase_ids.add(phrase_id)
                used_chain_ids.add(chain_idx)
        
        # Check song matrix references chains and verify vertical arrangement
        used_rows = []
        used_columns = set()
        
        # Collect used rows and columns
        for row_idx, row in enumerate(output_project.song):
            if not row.is_empty():
                used_rows.append(row_idx)
                # M8SongRow has 8 fixed columns
                for col_idx in range(8):  # COL_COUNT = 8 from m8.api.song
                    chain_id = row[col_idx]
                    if chain_id != 0xFF:  # Not empty
                        self.assertIn(chain_id, used_chain_ids,
                                    f"Song matrix references non-existent chain {chain_id}")
                        used_columns.add(col_idx)
        
        # Verify vertical arrangement (no gaps between used rows)
        used_rows.sort()
        if used_rows:
            self.assertEqual(used_rows, list(range(min(used_rows), max(used_rows) + 1)),
                           "Song matrix should have no gaps between rows")
            
            # Check column usage - should use columns 0, 1, 2 for the three projects
            expected_columns = set(range(len(projects)))
            self.assertEqual(used_columns, expected_columns,
                           f"Projects should be arranged in columns {expected_columns}")
    
    @patch('m8.tools.concat_phrases.prompt_for_files')
    def test_main_function(self, mock_prompt):
        """Test the main function."""
        # Set up mock to return all test files
        mock_prompt.return_value = self.project_paths
        
        # Run main with arguments
        with patch('sys.argv', ['concat_phrases.py', self.test_projects_dir, self.out_file]):
            # Should complete successfully
            self.assertEqual(main(), 0)
            
            # Check output file was created
            self.assertTrue(os.path.exists(self.out_file))
            
            # Load output file and validate
            output_project = M8Project.read_from_file(self.out_file)
            self.assertTrue(output_project.validate_one_to_one_chains())
            output_project.validate_references()  # This doesn't return a value, just validates
    
    @patch('m8.tools.concat_phrases.prompt_for_files')
    def test_main_nonexistent_dir(self, mock_prompt):
        """Test main with non-existent directory."""
        with patch('sys.argv', ['concat_phrases.py', os.path.join(self.temp_dir, "nonexistent"), self.out_file]):
            self.assertEqual(main(), 1)
    
    @patch('m8.tools.concat_phrases.prompt_for_files')
    def test_main_no_files(self, mock_prompt):
        """Test main with no files selected."""
        mock_prompt.return_value = []
        
        with patch('sys.argv', ['concat_phrases.py', self.test_projects_dir, self.out_file]):
            self.assertEqual(main(), 1)
    
    @patch('m8.tools.concat_phrases.prompt_for_files')
    def test_main_creates_output_dir(self, mock_prompt):
        """Test main creates output directory if it doesn't exist."""
        mock_prompt.return_value = self.project_paths
        
        output_file = os.path.join(self.temp_dir, "new_dir", "output.m8s")
        with patch('sys.argv', ['concat_phrases.py', self.test_projects_dir, output_file]):
            self.assertEqual(main(), 0)
            self.assertTrue(os.path.exists(os.path.dirname(output_file)))


if __name__ == '__main__':
    unittest.main()