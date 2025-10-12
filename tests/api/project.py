import unittest
import os
import tempfile
from m8.api import M8Block
from m8.api.project import M8Project, OFFSETS
from m8.api.metadata import M8Metadata
from m8.api.song import M8SongMatrix, M8SongRow
from m8.api.chains import M8Chain, M8Chains
from m8.api.phrases import M8Phrase, M8Phrases
from m8.api.instruments import M8Instruments
from m8.api.sampler import M8Sampler as M8Instrument

class TestM8Project(unittest.TestCase):
    def setUp(self):
        """Set up a minimal project for testing."""
        self.project = M8Project()
        self.project.metadata = M8Metadata(name="Test Project")
        self.project.song = M8SongMatrix()
        self.project.chains = M8Chains()
        self.project.phrases = M8Phrases()
        self.project.instruments = M8Instruments()
        
        # Create some data that will be used for testing references
        # Add a simple instrument
        self.test_instrument = M8Instrument(name="TestSynth")
        self.instrument_slot = self.project.add_instrument(self.test_instrument)
        
        # Add a phrase using this instrument
        self.test_phrase = M8Phrase()
        self.test_phrase[0].instrument = self.instrument_slot  # M8Phrase uses __getitem__ syntax, not steps
        self.phrase_slot = self.project.add_phrase(self.test_phrase)
        
        # Add a chain using this phrase
        self.test_chain = M8Chain()
        self.test_chain[0].phrase = self.phrase_slot
        self.chain_slot = self.project.add_chain(self.test_chain)
        
        # Add a song row using this chain
        self.project.song[0][0] = self.chain_slot
    
    def test_add_get_instrument(self):
        # Test adding an instrument
        instrument = M8Instrument(name="NewInstrument")
        slot = self.project.add_instrument(instrument)
        
        # Check the instrument was added
        self.assertIs(self.project.instruments[slot], instrument)
        
        # Test setting an instrument explicitly
        instrument2 = M8Instrument(name="Instrument2")
        self.project.set_instrument(instrument2, 2)
        self.assertIs(self.project.instruments[2], instrument2)
        
        # Test error handling for invalid slot
        with self.assertRaises(IndexError):
            self.project.set_instrument(instrument, len(self.project.instruments))
        
        # Fill all slots and test overflow
        for i in range(len(self.project.instruments)):
            if isinstance(self.project.instruments[i], M8Block):
                self.project.instruments[i] = M8Instrument(name=f"Instr{i}")
        
        # Should be no available slots now
        self.assertIsNone(self.project.available_instrument_slot)
        
        # Adding another should raise error
        with self.assertRaises(IndexError):
            self.project.add_instrument(M8Instrument(name="Overflow"))
    
    def test_add_get_phrase(self):
        # Test adding a phrase
        phrase = M8Phrase()
        slot = self.project.add_phrase(phrase)
        
        # Check the phrase was added
        self.assertIs(self.project.phrases[slot], phrase)
        
        # Test setting a phrase explicitly
        phrase2 = M8Phrase()
        phrase2[0].note = 60  # C4
        self.project.set_phrase(phrase2, 2)
        self.assertIs(self.project.phrases[2], phrase2)
        
        # Test error handling for invalid slot
        with self.assertRaises(IndexError):
            self.project.set_phrase(phrase, len(self.project.phrases))
        
        # Fill all slots and test overflow
        for i in range(len(self.project.phrases)):
            if self.project.phrases[i].is_empty():
                new_phrase = M8Phrase()
                new_phrase[0].note = i % 12  # Different note for each phrase
                self.project.phrases[i] = new_phrase
        
        # Should be no available slots now
        self.assertIsNone(self.project.available_phrase_slot)
        
        # Adding another should raise error
        with self.assertRaises(IndexError):
            self.project.add_phrase(M8Phrase())
    
    def test_add_get_chain(self):
        # Test adding a chain
        chain = M8Chain()
        slot = self.project.add_chain(chain)
        
        # Check the chain was added
        self.assertIs(self.project.chains[slot], chain)
        
        # Test setting a chain explicitly
        chain2 = M8Chain()
        chain2[0].phrase = 1
        self.project.set_chain(chain2, 2)
        self.assertIs(self.project.chains[2], chain2)
        
        # Test error handling for invalid slot
        with self.assertRaises(IndexError):
            self.project.set_chain(chain, len(self.project.chains))
        
        # Fill all slots and test overflow
        for i in range(len(self.project.chains)):
            if self.project.chains[i].is_empty():
                new_chain = M8Chain()
                new_chain[0].phrase = i % 10  # Different phrase for each chain
                self.project.chains[i] = new_chain
        
        # Should be no available slots now
        self.assertIsNone(self.project.available_chain_slot)
        
        # Adding another should raise error
        with self.assertRaises(IndexError):
            self.project.add_chain(M8Chain())
    
    def test_write_read_file(self):
        # Skip this test if we don't have the template file
        try:
            # First create a proper project from template
            project = M8Project.initialise()
        except FileNotFoundError:
            self.skipTest("Template file not found - skipping file I/O test")
        
        # Write the project to a temporary file, read it back, and compare
        with tempfile.NamedTemporaryFile(suffix='.m8s', delete=False) as tmp:
            try:
                tmp_path = tmp.name
                project.write_to_file(tmp_path)
                
                # Read it back
                read_project = M8Project.read_from_file(tmp_path)
                
                # Compare basic attributes
                self.assertEqual(read_project.metadata.name, project.metadata.name)
                
                # Check that all the major components were preserved
                self.assertEqual(len(read_project.instruments), len(project.instruments))
                self.assertEqual(len(read_project.phrases), len(project.phrases))
                self.assertEqual(len(read_project.chains), len(project.chains))
                self.assertEqual(len(read_project.song), len(project.song))
            finally:
                # Clean up
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    def test_initialise(self):
        try:
            # Attempt to create a project from the default template
            project = M8Project.initialise()
            
            # Just perform some basic checks
            self.assertIsNotNone(project.metadata)
            self.assertIsNotNone(project.song)
            self.assertIsNotNone(project.chains)
            self.assertIsNotNone(project.phrases)
            self.assertIsNotNone(project.instruments)
        except FileNotFoundError:
            self.skipTest("Template file not found - skipping initialise test")
    
    def test_initialise_nonexistent_template(self):
        # Test with a non-existent template name
        with self.assertRaises(FileNotFoundError):
            M8Project.initialise("NONEXISTENT_TEMPLATE")
            
    def test_clone(self):
        # Clone the test project set up in setUp
        cloned_project = self.project.clone()
        
        # Verify they are separate instances
        self.assertIsNot(cloned_project, self.project)
        self.assertIsNot(cloned_project.metadata, self.project.metadata)
        self.assertIsNot(cloned_project.instruments, self.project.instruments)
        self.assertIsNot(cloned_project.phrases, self.project.phrases)
        self.assertIsNot(cloned_project.chains, self.project.chains)
        self.assertIsNot(cloned_project.song, self.project.song)
        
        # Verify the data was copied correctly
        self.assertEqual(cloned_project.metadata.name, self.project.metadata.name)
        
        # Check the instrument in the clone
        cloned_instrument = cloned_project.instruments[self.instrument_slot]
        self.assertEqual(cloned_instrument.name, self.test_instrument.name)
        self.assertIsNot(cloned_instrument, self.test_instrument)
        
        # Verify reference chain is maintained
        # Chain -> Phrase -> Instrument
        cloned_chain = cloned_project.chains[self.chain_slot]
        self.assertEqual(cloned_chain[0].phrase, self.phrase_slot)
        
        cloned_phrase = cloned_project.phrases[self.phrase_slot]
        self.assertEqual(cloned_phrase[0].instrument, self.instrument_slot)
        
        # Modify the clone and verify original is unchanged
        cloned_project.metadata.name = "Modified Clone"
        self.assertEqual(self.project.metadata.name, "Test Project")
        self.assertEqual(cloned_project.metadata.name, "Modified Clone")
        

if __name__ == '__main__':
    unittest.main()