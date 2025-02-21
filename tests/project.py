import unittest
import os
from m8 import M8ValidationError, NULL
from m8.project import M8Project
from m8.instruments.macrosynth import M8MacroSynth
from m8.modulators import M8AHDEnvelope
from m8.phrases import M8Phrase, M8PhraseStep, M8FXTuple
from m8.chains import M8Chain, M8ChainStep

class TestM8ProjectMemoryCycle(unittest.TestCase):
    """Test the serialization/deserialization cycle of M8Project without file I/O."""
    
    def setUp(self):
        """Set up test environment and load template file."""
        template_path = "templates/DEFAULT401.m8s"
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
        
        # Configure instrument and add to project
        self._create_instrument()
        
        # Configure phrase and add to project
        phrase_idx = self._create_phrase()
        
        # Configure chain that references phrase and add to project
        chain_idx = self._create_chain(phrase_idx)
        
        # Configure song to use the chain
        self.original_project.song[0][0] = chain_idx
    
    def _create_instrument(self):
        """Create and assign a MacroSynth instrument with a modulator."""
        # Create the synth
        macro_synth = M8MacroSynth(
            mixer_delay=0xA0,
            mixer_reverb=0x40
        )
        
        # Add an envelope modulator
        modulator = M8AHDEnvelope(
            destination=0x01,  # Pitch
            amount=0x60,
            attack=0x20,
            hold=0x10,
            decay=0x40
        )
        
        # Add modulator to instrument
        macro_synth.add_modulator(modulator)
        
        # Add instrument to project
        return self.original_project.add_instrument(macro_synth)
    
    def _create_phrase(self):
        """Create a test phrase with notes and effects."""
        phrase = M8Phrase()
        
        for i in range(4):
            # Create step with incrementing notes
            step = M8PhraseStep(
                note=0x40 + i,
                velocity=0x60,
                instrument=0    # Use our macro synth
            )
            
            # Add an effect to the step
            step.add_fx(key=0x2B, value=0x80 - (i * 0x10))
            
            # Add step to phrase
            phrase.set_step(step, i*4)  # Place a note every 4 steps
        
        # Add phrase to project
        return self.original_project.add_phrase(phrase)
    
    def _create_chain(self, phrase_idx):
        """Create a chain that references the phrase."""
        chain = M8Chain()
        
        # Create chain step that references our phrase
        chain_step = M8ChainStep(
            phrase=phrase_idx, 
            transpose=0
        )
        
        # Add step to chain
        chain.add_step(chain_step)
        
        # Add chain to project
        return self.original_project.add_chain(chain)
    
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
