import unittest
import os
from m8 import M8ValidationError, NULL
from m8.project import M8Project
from m8.instruments.macrosynth import M8MacroSynth
from m8.modulators import M8AHDEnvelope
from m8.phrases import M8Phrase, M8PhraseStep, M8FXTuple
from m8.chains import M8Chain, M8ChainStep
from m8.enums.fx import M8FXEnum

class TestM8ProjectMemoryCycle(unittest.TestCase):
    """Test the serialization/deserialization cycle of M8Project without file I/O."""
    
    def setUp(self):
        """Set up test environment and load template file."""
        template_path = "templates/DEFAULT-4-0-1.m8s"
        self.assertTrue(os.path.exists(template_path), f"Template file not found: {template_path}")
        self.original_project = M8Project.read_from_file(template_path)
    
    def test_memory_cycle(self):
        """Test that a project can be serialized and deserialized correctly."""
        # Configure the project
        self._configure_project()
        
        # Validate the original project
        try:
            self.original_project.validate()
        except M8ValidationError as e:
            self.fail(f"Original project validation failed: {str(e)}")
        
        # Serialize and deserialize
        project_bytes = self.original_project.write()
        self.new_project = M8Project.read(project_bytes)
        
        # Validate the reloaded project
        try:
            self.new_project.validate()
        except M8ValidationError as e:
            self.fail(f"Reloaded project validation failed: {str(e)}")
        
        # Compare the projects
        self._compare_metadata()
        self._compare_instruments()
        self._compare_modulators()
        self._compare_phrases()
        self._compare_chains()
        self._compare_song()
    
    def _configure_project(self):
        """Configure the test project with instruments, phrases, chains, and song data."""
        # Set metadata
        self.original_project.metadata.directory = "/Songs/test/"
        self.original_project.metadata.name = "MEMORY_TEST"
        
        # Configure instrument
        self._create_instrument()
        
        # Configure phrase
        self._create_phrase()
        
        # Configure chain
        self._create_chain()
        
        # Configure song
        self._configure_song()
    
    def _create_instrument(self):
        """Create and assign a MacroSynth instrument with a modulator."""
        # Create the synth
        macro_synth = M8MacroSynth(
            mixer_delay=0xA0,
            mixer_reverb=0x40
        )
        self.original_project.instruments[0] = macro_synth
        
        # Add an envelope modulator
        modulator = M8AHDEnvelope(
            destination=0x01,  # Pitch
            amount=0x60,
            attack=0x20,
            hold=0x10,
            decay=0x40
        )
        macro_synth.modulators[0] = modulator
    
    def _create_phrase(self):
        """Create a test phrase with notes and effects."""
        phrase = M8Phrase()
        for i in range(4):
            step = M8PhraseStep(
                note=0x40 + i,  # Incrementing notes
                velocity=0x60,
                instrument=0    # Use our macro synth
            )
            
            # Add an effect to each step
            fx = M8FXTuple(key=M8FXEnum.VDE, value=0x80 - (i * 0x10))
            step.fx[0] = fx
            
            phrase[i*4] = step  # Place a note every 4 steps
        
        self.original_project.phrases[0] = phrase
    
    def _create_chain(self):
        """Create a chain that references the phrase."""
        chain = M8Chain()
        chain_step = M8ChainStep(phrase=0, transpose=0)
        chain[0] = chain_step
        self.original_project.chains[0] = chain
    
    def _configure_song(self):
        """Configure the song to use the chain."""
        self.original_project.song[0][0] = 0  # Assign chain 0 to first track, first row
    
    def _compare_metadata(self):
        """Compare metadata between original and reloaded projects."""
        self.assertEqual(
            self.original_project.metadata.name, 
            self.new_project.metadata.name,
            "Project name mismatch"
        )
        
        self.assertEqual(
            self.original_project.metadata.directory, 
            self.new_project.metadata.directory,
            "Project directory mismatch"
        )
    
    def _compare_instruments(self):
        """Compare instruments between original and reloaded projects."""
        orig_synth = self.original_project.instruments[0]
        new_synth = self.new_project.instruments[0]
        
        self.assertEqual(
            orig_synth.synth_params.mixer_delay,
            new_synth.synth_params.mixer_delay,
            "Instrument mixer_delay mismatch"
        )
        
        self.assertEqual(
            orig_synth.synth_params.mixer_reverb,
            new_synth.synth_params.mixer_reverb,
            "Instrument mixer_reverb mismatch"
        )
    
    def _compare_modulators(self):
        """Compare modulators between original and reloaded projects."""
        orig_mod = self.original_project.instruments[0].modulators[0]
        new_mod = self.new_project.instruments[0].modulators[0]
        
        self.assertEqual(
            orig_mod.destination,
            new_mod.destination,
            "Modulator destination mismatch"
        )
        
        self.assertEqual(
            orig_mod.amount,
            new_mod.amount,
            "Modulator amount mismatch"
        )
        
        self.assertEqual(
            orig_mod.attack,
            new_mod.attack,
            "Modulator attack mismatch"
        )
        
        self.assertEqual(
            orig_mod.hold,
            new_mod.hold,
            "Modulator hold mismatch"
        )
        
        self.assertEqual(
            orig_mod.decay,
            new_mod.decay,
            "Modulator decay mismatch"
        )
    
    def _compare_phrases(self):
        """Compare phrases between original and reloaded projects."""
        orig_phrase = self.original_project.phrases[0]
        new_phrase = self.new_project.phrases[0]
        
        for i in range(4):
            idx = i * 4
            orig_step = orig_phrase[idx]
            new_step = new_phrase[idx]
            
            self.assertEqual(
                orig_step.note,
                new_step.note,
                f"Note mismatch at step {idx}"
            )
            
            self.assertEqual(
                orig_step.velocity,
                new_step.velocity,
                f"Velocity mismatch at step {idx}"
            )
            
            self.assertEqual(
                orig_step.instrument,
                new_step.instrument,
                f"Instrument reference mismatch at step {idx}"
            )
            
            self.assertEqual(
                orig_step.fx[0].key,
                new_step.fx[0].key,
                f"FX key mismatch at step {idx}"
            )
            
            self.assertEqual(
                orig_step.fx[0].value,
                new_step.fx[0].value,
                f"FX value mismatch at step {idx}"
            )
    
    def _compare_chains(self):
        """Compare chains between original and reloaded projects."""
        self.assertEqual(
            self.original_project.chains[0][0].phrase,
            self.new_project.chains[0][0].phrase,
            "Chain phrase reference mismatch"
        )
        
        self.assertEqual(
            self.original_project.chains[0][0].transpose,
            self.new_project.chains[0][0].transpose,
            "Chain transpose value mismatch"
        )
    
    def _compare_song(self):
        """Compare song structure between original and reloaded projects."""
        self.assertEqual(
            self.original_project.song[0][0],
            self.new_project.song[0][0],
            "Song chain reference mismatch"
        )

if __name__ == "__main__":
    unittest.main()
