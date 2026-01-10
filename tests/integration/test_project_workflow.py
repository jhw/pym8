# tests/integration/test_project_workflow.py
"""Integration tests for complete M8 project workflows."""

import unittest
import os
import tempfile
from m8.api.project import M8Project
from m8.api.instruments.sampler import M8Sampler, M8SamplerParam, M8PlayMode
from m8.api.instruments.wavsynth import M8Wavsynth, M8WavsynthParam
from m8.api.instruments.macrosynth import M8Macrosynth, M8MacrosynthParam
from m8.api.instruments.fmsynth import M8FMSynth, M8FMSynthParam
from m8.api.instruments.external import M8External, M8ExternalParam
from m8.api.phrase import M8Phrase, M8PhraseStep, M8Note
from m8.api.chain import M8Chain, M8ChainStep
from m8.api.fx import M8FXTuple, M8SequenceFX, M8SamplerFX


class TestProjectCreationWorkflow(unittest.TestCase):
    """Test creating a new project from scratch."""

    def test_create_empty_project(self):
        """Test creating and saving an empty project."""
        project = M8Project.initialise()
        project.metadata.name = "EMPTY"
        project.metadata.tempo = 120.0

        self.assertEqual(project.metadata.name, "EMPTY")
        self.assertEqual(project.metadata.tempo, 120.0)

    def test_create_project_with_sampler(self):
        """Test creating project with a sampler instrument."""
        project = M8Project.initialise()
        project.metadata.name = "SAMPLER"

        # Add sampler
        sampler = M8Sampler(name="KICK", sample_path="/Samples/kick.wav")
        sampler.set(M8SamplerParam.VOLUME, 0xFF)
        sampler.set(M8SamplerParam.PLAY_MODE, M8PlayMode.FWD)
        project.instruments[0] = sampler

        # Verify
        self.assertIsInstance(project.instruments[0], M8Sampler)
        self.assertEqual(project.instruments[0].name, "KICK")
        self.assertEqual(project.instruments[0].sample_path, "/Samples/kick.wav")

    def test_create_project_with_multiple_instrument_types(self):
        """Test project with all instrument types."""
        project = M8Project.initialise()
        project.metadata.name = "MULTI"

        # Add different instrument types
        project.instruments[0] = M8Sampler(name="SAMPLER")
        project.instruments[1] = M8Wavsynth(name="WAVSYNTH")
        project.instruments[2] = M8Macrosynth(name="MACRO")
        project.instruments[3] = M8FMSynth(name="FM")
        project.instruments[4] = M8External(name="EXTERNAL")

        # Verify types
        self.assertIsInstance(project.instruments[0], M8Sampler)
        self.assertIsInstance(project.instruments[1], M8Wavsynth)
        self.assertIsInstance(project.instruments[2], M8Macrosynth)
        self.assertIsInstance(project.instruments[3], M8FMSynth)
        self.assertIsInstance(project.instruments[4], M8External)


class TestProjectPhraseWorkflow(unittest.TestCase):
    """Test creating phrases with notes and FX."""

    def test_create_phrase_with_notes(self):
        """Test creating a phrase with notes."""
        project = M8Project.initialise()

        # Create instrument
        project.instruments[0] = M8Sampler(name="KICK")

        # Create phrase
        phrase = M8Phrase()
        phrase[0] = M8PhraseStep(note=M8Note.C_4, velocity=0xFF, instrument=0x00)
        phrase[4] = M8PhraseStep(note=M8Note.C_4, velocity=0xFF, instrument=0x00)
        phrase[8] = M8PhraseStep(note=M8Note.C_4, velocity=0xFF, instrument=0x00)
        phrase[12] = M8PhraseStep(note=M8Note.C_4, velocity=0xFF, instrument=0x00)
        project.phrases[0] = phrase

        # Verify
        self.assertEqual(project.phrases[0][0].note, M8Note.C_4)
        self.assertEqual(project.phrases[0][0].velocity, 0xFF)
        self.assertEqual(project.phrases[0][0].instrument, 0x00)
        self.assertEqual(project.phrases[0][4].note, M8Note.C_4)

    def test_create_phrase_with_fx(self):
        """Test creating a phrase with FX commands."""
        project = M8Project.initialise()
        project.instruments[0] = M8Sampler(name="SNARE")

        phrase = M8Phrase()
        step = M8PhraseStep(note=M8Note.D_4, velocity=0xFF, instrument=0x00)
        step.fx[0] = M8FXTuple(key=M8SequenceFX.RET, value=0x03)  # Retrigger
        step.fx[1] = M8FXTuple(key=M8SamplerFX.VOL, value=0x80)   # Volume
        phrase[0] = step
        project.phrases[0] = phrase

        # Verify FX
        self.assertEqual(project.phrases[0][0].fx[0].key, M8SequenceFX.RET)
        self.assertEqual(project.phrases[0][0].fx[0].value, 0x03)
        self.assertEqual(project.phrases[0][0].fx[1].key, M8SamplerFX.VOL)


class TestProjectChainWorkflow(unittest.TestCase):
    """Test creating chains that reference phrases."""

    def test_create_chain_with_phrases(self):
        """Test creating a chain with phrase references."""
        project = M8Project.initialise()

        # Create phrases
        phrase0 = M8Phrase()
        phrase0[0] = M8PhraseStep(note=M8Note.C_4, velocity=0xFF, instrument=0x00)
        project.phrases[0] = phrase0

        phrase1 = M8Phrase()
        phrase1[0] = M8PhraseStep(note=M8Note.E_4, velocity=0xFF, instrument=0x00)
        project.phrases[1] = phrase1

        # Create chain
        chain = M8Chain()
        chain[0] = M8ChainStep(phrase=0x00, transpose=0x00)
        chain[1] = M8ChainStep(phrase=0x01, transpose=0x00)
        chain[2] = M8ChainStep(phrase=0x00, transpose=0x0C)  # Up octave
        project.chains[0] = chain

        # Verify
        self.assertEqual(project.chains[0][0].phrase, 0x00)
        self.assertEqual(project.chains[0][1].phrase, 0x01)
        self.assertEqual(project.chains[0][2].transpose, 0x0C)

    def test_chain_transpose_values(self):
        """Test chain transpose with positive and negative values."""
        project = M8Project.initialise()

        chain = M8Chain()
        chain[0] = M8ChainStep(phrase=0x00, transpose=0x00)   # No transpose
        chain[1] = M8ChainStep(phrase=0x00, transpose=0x0C)   # +12 semitones
        chain[2] = M8ChainStep(phrase=0x00, transpose=0xF4)   # -12 semitones (two's complement)
        project.chains[0] = chain

        self.assertEqual(project.chains[0][0].transpose, 0x00)
        self.assertEqual(project.chains[0][1].transpose, 0x0C)
        self.assertEqual(project.chains[0][2].transpose, 0xF4)


class TestProjectSongWorkflow(unittest.TestCase):
    """Test arranging chains in the song matrix."""

    def test_add_chains_to_song(self):
        """Test adding chains to song matrix."""
        project = M8Project.initialise()

        # Set up chains in song
        project.song[0][0] = 0x00  # Chain 0 on track 0, row 0
        project.song[0][1] = 0x01  # Chain 1 on track 1, row 0
        project.song[1][0] = 0x00  # Chain 0 on track 0, row 1

        # Verify
        self.assertEqual(project.song[0][0], 0x00)
        self.assertEqual(project.song[0][1], 0x01)
        self.assertEqual(project.song[1][0], 0x00)

    def test_full_song_structure(self):
        """Test complete song structure: instruments -> phrases -> chains -> song."""
        project = M8Project.initialise()
        project.metadata.name = "FULLSONG"
        project.metadata.tempo = 140.0

        # Instruments
        project.instruments[0] = M8Sampler(name="KICK")
        project.instruments[1] = M8Sampler(name="SNARE")

        # Phrases
        kick_phrase = M8Phrase()
        for i in [0, 4, 8, 12]:
            kick_phrase[i] = M8PhraseStep(note=M8Note.C_4, velocity=0xFF, instrument=0x00)
        project.phrases[0] = kick_phrase

        snare_phrase = M8Phrase()
        for i in [4, 12]:
            snare_phrase[i] = M8PhraseStep(note=M8Note.D_4, velocity=0xFF, instrument=0x01)
        project.phrases[1] = snare_phrase

        # Chains
        kick_chain = M8Chain()
        kick_chain[0] = M8ChainStep(phrase=0x00, transpose=0x00)
        project.chains[0] = kick_chain

        snare_chain = M8Chain()
        snare_chain[0] = M8ChainStep(phrase=0x01, transpose=0x00)
        project.chains[1] = snare_chain

        # Song arrangement
        for row in range(4):
            project.song[row][0] = 0x00  # Kick chain
            project.song[row][1] = 0x01  # Snare chain

        # Verify complete structure
        self.assertEqual(project.metadata.name, "FULLSONG")
        self.assertEqual(project.instruments[0].name, "KICK")
        self.assertEqual(project.phrases[0][0].note, M8Note.C_4)
        self.assertEqual(project.chains[0][0].phrase, 0x00)
        self.assertEqual(project.song[0][0], 0x00)


class TestProjectFileIO(unittest.TestCase):
    """Test reading and writing project files."""

    def test_write_and_read_project(self):
        """Test writing project to file and reading it back."""
        project = M8Project.initialise()
        project.metadata.name = "FILETEST"
        project.metadata.tempo = 128.0

        # Add content
        project.instruments[0] = M8Sampler(name="TEST", sample_path="/test.wav")
        phrase = M8Phrase()
        phrase[0] = M8PhraseStep(note=M8Note.C_4, velocity=0xFF, instrument=0x00)
        project.phrases[0] = phrase

        chain = M8Chain()
        chain[0] = M8ChainStep(phrase=0x00, transpose=0x00)
        project.chains[0] = chain

        project.song[0][0] = 0x00

        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix='.m8s', delete=False) as f:
            temp_path = f.name

        try:
            project.write_to_file(temp_path)

            # Read back
            loaded = M8Project.read_from_file(temp_path)

            # Verify all components
            self.assertEqual(loaded.metadata.name, "FILETEST")
            self.assertEqual(loaded.metadata.tempo, 128.0)
            self.assertIsInstance(loaded.instruments[0], M8Sampler)
            self.assertEqual(loaded.instruments[0].name, "TEST")
            self.assertEqual(loaded.phrases[0][0].note, M8Note.C_4)
            self.assertEqual(loaded.chains[0][0].phrase, 0x00)
            self.assertEqual(loaded.song[0][0], 0x00)
        finally:
            os.unlink(temp_path)

    def test_clone_preserves_all_components(self):
        """Test that clone preserves all project components."""
        original = M8Project.initialise()
        original.metadata.name = "ORIGINAL"
        original.instruments[0] = M8Sampler(name="SAMPLER")
        original.phrases[0][0] = M8PhraseStep(note=M8Note.C_4, velocity=0xFF, instrument=0x00)
        original.chains[0][0] = M8ChainStep(phrase=0x00, transpose=0x00)
        original.song[0][0] = 0x00

        clone = original.clone()

        # Verify values match
        self.assertEqual(clone.metadata.name, original.metadata.name)
        self.assertEqual(clone.instruments[0].name, original.instruments[0].name)
        self.assertEqual(clone.phrases[0][0].note, original.phrases[0][0].note)
        self.assertEqual(clone.chains[0][0].phrase, original.chains[0][0].phrase)
        self.assertEqual(clone.song[0][0], original.song[0][0])

        # Verify independence
        clone.metadata.name = "CLONE"
        self.assertEqual(original.metadata.name, "ORIGINAL")


class TestProjectNavigationWorkflow(unittest.TestCase):
    """Test navigating from song to instruments."""

    def test_navigate_song_to_instrument(self):
        """Test navigating from song position to instrument."""
        project = M8Project.initialise()

        # Set up structure
        project.instruments[5] = M8Sampler(name="BASS")

        phrase = M8Phrase()
        phrase[0] = M8PhraseStep(note=M8Note.E_2, velocity=0xFF, instrument=0x05)
        project.phrases[10] = phrase

        chain = M8Chain()
        chain[0] = M8ChainStep(phrase=10, transpose=0x00)
        project.chains[20] = chain

        project.song[0][3] = 20  # Chain 20 on track 3

        # Navigate: song[0][3] -> chain 20 -> phrase 10 -> instrument 5
        chain_ref = project.song[0][3]
        self.assertEqual(chain_ref, 20)

        phrase_ref = project.chains[chain_ref][0].phrase
        self.assertEqual(phrase_ref, 10)

        instr_ref = project.phrases[phrase_ref][0].instrument
        self.assertEqual(instr_ref, 5)

        instrument = project.instruments[instr_ref]
        self.assertEqual(instrument.name, "BASS")


if __name__ == '__main__':
    unittest.main()
