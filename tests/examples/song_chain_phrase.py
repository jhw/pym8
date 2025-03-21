import unittest
from m8.api.project import M8Project


class TestSongChainPhraseRelationships(unittest.TestCase):
    """
    Test the relationships between song, chains, phrases, and instruments
    in an M8 project file.
    """
    
    def setUp(self):
        # Load the M8S file with the structure we want to test
        self.project = M8Project.read_from_file("tests/examples/fixtures/WAVSYNTH.m8s")
        
    def test_instrument_referenced_by_phrase(self):
        """Verify instrument 00 is referenced by phrase 00"""
        # Get the first phrase
        phrase = self.project.phrases[0]
        
        # Get all steps that reference instrument 00
        inst_0_steps = [i for i, step in enumerate(phrase) 
                        if step.note != 0xFF and step.instrument == 0]
        
        self.assertTrue(len(inst_0_steps) > 0, 
                        "Instrument 00 should be referenced by at least one step in phrase 00")
                         
    def test_single_phrase(self):
        """Verify there is a single phrase with ID 00"""
        # Get all non-empty phrases
        non_empty_phrases = [i for i, phrase in enumerate(self.project.phrases) 
                             if not phrase.is_empty()]
        
        self.assertEqual(len(non_empty_phrases), 1, 
                         "Should have exactly one non-empty phrase")
        self.assertEqual(non_empty_phrases[0], 0, 
                         "The only non-empty phrase should have ID 00")
                         
    def test_single_chain(self):
        """Verify there is a single chain with ID 00"""
        # Get all non-empty chains
        non_empty_chains = [i for i, chain in enumerate(self.project.chains) 
                            if not chain.is_empty()]
        
        self.assertEqual(len(non_empty_chains), 1, 
                         "Should have exactly one non-empty chain")
        self.assertEqual(non_empty_chains[0], 0, 
                         "The only non-empty chain should have ID 00")
    
    def test_song_references_chain(self):
        """Verify the song has only one entry referencing chain 00 in row 0, col 0"""
        # Convert song to list to examine its structure
        song_list = self.project.song.as_list()
        
        # There should be only one non-empty row
        self.assertEqual(len(song_list), 1, 
                         "Song should have exactly one non-empty row")
        
        # That row should be at index 0
        self.assertEqual(song_list[0]['index'], 0, 
                         "The only non-empty row should be at index 0")
        
        # That row should have exactly one chain reference
        self.assertEqual(len(song_list[0]['chains']), 1, 
                         "Row 0 should have exactly one chain reference")
        
        # The chain reference should be at column 0 and point to chain 00
        chain_ref = song_list[0]['chains'][0]
        self.assertEqual(chain_ref['col'], 0, 
                         "The chain reference should be in column 0")
        self.assertEqual(chain_ref['chain'], 0, 
                         "The chain reference should point to chain 00")
    
    def test_chain_references_phrase(self):
        """Verify chain 00 contains exactly one reference to phrase 00"""
        # Get the first chain (ID 00)
        chain = self.project.chains[0]
        
        # Convert chain to dict to examine its structure
        chain_dict = chain.as_dict()
        
        # There should be exactly one step in the chain
        self.assertEqual(len(chain_dict['steps']), 1, 
                         "Chain 00 should have exactly one step")
        
        # That step should reference phrase 00
        step = chain_dict['steps'][0]
        self.assertEqual(step['phrase'], 0, 
                         "The step in chain 00 should reference phrase 00")
    
    def test_phrase_has_notes_at_specific_positions(self):
        """Verify phrase 00 has notes at positions 0, 4, 8, 12 referencing instrument 00"""
        # Get the first phrase (ID 00)
        phrase = self.project.phrases[0]
        
        # Convert phrase to dict to examine its structure
        phrase_dict = phrase.as_dict()
        
        # Get all steps that have notes
        note_steps = [step for step in phrase_dict['steps'] 
                      if step['note'] != 0xFF]  # 0xFF is the empty note value
        
        # The notes should be at positions 0, 4, 8, 12
        expected_positions = [0, 4, 8, 12]
        positions_with_notes = sorted([step['index'] for step in note_steps])
        
        # Check if expected positions are a subset of the positions with notes
        for pos in expected_positions:
            self.assertIn(pos, positions_with_notes,
                          f"Expected a note at position {pos}")
        
        # Check that notes at positions 0, 4, 8, 12 reference instrument 00
        for pos in expected_positions:
            matching_steps = [step for step in note_steps if step['index'] == pos]
            if matching_steps:
                self.assertEqual(matching_steps[0]['instrument'], 0,
                                f"Note at position {pos} should reference instrument 00")


if __name__ == '__main__':
    unittest.main()