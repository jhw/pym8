# tests/api/test_validation.py
"""Tests for validation methods across M8 API classes."""

import unittest
from m8.api.project import M8Project
from m8.api.chain import M8ChainStep, M8Chain, M8Chains, CHAIN_COUNT, STEP_COUNT
from m8.api.phrase import M8PhraseStep, M8Phrase, M8Phrases, PHRASE_COUNT, STEP_COUNT as PHRASE_STEP_COUNT
from m8.api.song import M8SongRow, M8SongMatrix, ROW_COUNT
from m8.api.instrument import M8Instruments, BLOCK_COUNT as INSTRUMENT_COUNT


class TestChainValidation(unittest.TestCase):
    """Tests for chain validation methods."""

    def test_chain_step_valid(self):
        """Test that valid chain steps pass validation."""
        step = M8ChainStep(phrase=0, transpose=0)
        step.validate()  # Should not raise

    def test_chain_step_empty_phrase(self):
        """Test that empty phrase (255) is valid."""
        step = M8ChainStep(phrase=255, transpose=0)
        step.validate()  # Should not raise

    def test_chain_step_max_phrase(self):
        """Test that max phrase (254) is valid."""
        step = M8ChainStep(phrase=254, transpose=0)
        step.validate()  # Should not raise

    def test_chain_valid(self):
        """Test that a valid chain passes validation."""
        chain = M8Chain()
        chain.validate()  # Should not raise

    def test_chain_wrong_step_count(self):
        """Test that chain with wrong step count fails validation."""
        chain = M8Chain()
        chain.append(M8ChainStep())  # Add extra step

        with self.assertRaises(ValueError) as ctx:
            chain.validate()
        self.assertIn("steps", str(ctx.exception))

    def test_chains_valid(self):
        """Test that valid chains collection passes validation."""
        chains = M8Chains()
        chains.validate()  # Should not raise

    def test_chains_too_many(self):
        """Test that too many chains fails validation."""
        chains = M8Chains()
        chains.append(M8Chain())  # Add extra chain beyond limit

        with self.assertRaises(ValueError) as ctx:
            chains.validate()
        self.assertIn("Too many chains", str(ctx.exception))


class TestPhraseValidation(unittest.TestCase):
    """Tests for phrase validation methods."""

    def test_phrase_step_valid(self):
        """Test that valid phrase steps pass validation."""
        step = M8PhraseStep(note=36, velocity=0xFF, instrument=0)
        step.validate()  # Should not raise

    def test_phrase_step_empty(self):
        """Test that empty phrase step (255) is valid."""
        step = M8PhraseStep()  # All 255
        step.validate()  # Should not raise

    def test_phrase_step_max_instrument(self):
        """Test that max instrument (127) is valid."""
        step = M8PhraseStep(note=36, velocity=0xFF, instrument=127)
        step.validate()  # Should not raise

    def test_phrase_step_invalid_instrument(self):
        """Test that invalid instrument (128-254) fails validation."""
        step = M8PhraseStep(note=36, velocity=0xFF, instrument=128)

        with self.assertRaises(ValueError) as ctx:
            step.validate()
        self.assertIn("instrument", str(ctx.exception).lower())

    def test_phrase_step_invalid_instrument_200(self):
        """Test that instrument 200 fails validation."""
        step = M8PhraseStep(note=36, velocity=0xFF, instrument=200)

        with self.assertRaises(ValueError) as ctx:
            step.validate()
        self.assertIn("instrument", str(ctx.exception).lower())

    def test_phrase_valid(self):
        """Test that a valid phrase passes validation."""
        phrase = M8Phrase()
        phrase.validate()  # Should not raise

    def test_phrase_wrong_step_count(self):
        """Test that phrase with wrong step count fails validation."""
        phrase = M8Phrase()
        phrase.append(M8PhraseStep())  # Add extra step

        with self.assertRaises(ValueError) as ctx:
            phrase.validate()
        self.assertIn("steps", str(ctx.exception))

    def test_phrase_invalid_instrument_in_step(self):
        """Test that phrase with invalid instrument in step fails."""
        phrase = M8Phrase()
        phrase[0] = M8PhraseStep(note=36, velocity=0xFF, instrument=200)

        with self.assertRaises(ValueError) as ctx:
            phrase.validate()
        self.assertIn("instrument", str(ctx.exception).lower())

    def test_phrases_valid(self):
        """Test that valid phrases collection passes validation."""
        phrases = M8Phrases()
        phrases.validate()  # Should not raise

    def test_phrases_too_many(self):
        """Test that too many phrases fails validation."""
        phrases = M8Phrases()
        phrases.append(M8Phrase())  # Add extra phrase beyond limit

        with self.assertRaises(ValueError) as ctx:
            phrases.validate()
        self.assertIn("Too many phrases", str(ctx.exception))


class TestSongValidation(unittest.TestCase):
    """Tests for song validation methods."""

    def test_song_row_valid(self):
        """Test that valid song row passes validation."""
        row = M8SongRow()
        row.validate()  # Should not raise

    def test_song_row_valid_chain_refs(self):
        """Test that valid chain references pass validation."""
        row = M8SongRow()
        row[0] = 0    # Chain 0
        row[1] = 127  # Chain 127 (max)
        row[2] = 255  # Empty
        row.validate()  # Should not raise

    def test_song_row_invalid_chain_ref(self):
        """Test that invalid chain reference (128-254) fails validation."""
        row = M8SongRow()
        row[0] = 128  # Invalid: 128-254 are not valid chain refs

        with self.assertRaises(ValueError) as ctx:
            row.validate()
        self.assertIn("chain", str(ctx.exception).lower())

    def test_song_row_invalid_chain_ref_200(self):
        """Test that chain reference 200 fails validation."""
        row = M8SongRow()
        row[0] = 200

        with self.assertRaises(ValueError) as ctx:
            row.validate()
        self.assertIn("chain", str(ctx.exception).lower())

    def test_song_matrix_valid(self):
        """Test that valid song matrix passes validation."""
        matrix = M8SongMatrix()
        matrix.validate()  # Should not raise

    def test_song_matrix_too_many_rows(self):
        """Test that too many rows fails validation."""
        matrix = M8SongMatrix()
        matrix.append(M8SongRow())  # Add extra row beyond limit

        with self.assertRaises(ValueError) as ctx:
            matrix.validate()
        self.assertIn("Too many song rows", str(ctx.exception))

    def test_song_matrix_invalid_chain_in_row(self):
        """Test that invalid chain reference in row fails."""
        matrix = M8SongMatrix()
        matrix[0][0] = 200  # Invalid chain reference

        with self.assertRaises(ValueError) as ctx:
            matrix.validate()
        self.assertIn("chain", str(ctx.exception).lower())


class TestInstrumentsValidation(unittest.TestCase):
    """Tests for instruments collection validation."""

    def test_instruments_valid(self):
        """Test that valid instruments collection passes validation."""
        instruments = M8Instruments()
        instruments.validate()  # Should not raise

    def test_instruments_too_many(self):
        """Test that too many instruments fails validation."""
        from m8.api import M8Block
        instruments = M8Instruments()
        # Add extra instrument beyond limit
        instruments.append(M8Block())

        with self.assertRaises(ValueError) as ctx:
            instruments.validate()
        self.assertIn("Too many instruments", str(ctx.exception))


class TestProjectValidation(unittest.TestCase):
    """Tests for project-level validation."""

    def test_project_valid(self):
        """Test that a valid project passes validation."""
        project = M8Project.initialise()
        project.validate()  # Should not raise

    def test_project_valid_with_content(self):
        """Test that a project with valid content passes validation."""
        from m8.api.instruments.sampler import M8Sampler
        from m8.api.phrase import M8Note

        project = M8Project.initialise()
        project.metadata.name = "TEST"

        # Add valid instrument
        project.instruments[0] = M8Sampler(name="KICK")

        # Add valid phrase
        project.phrases[0][0] = M8PhraseStep(note=M8Note.C_4, velocity=0xFF, instrument=0)

        # Add valid chain
        project.chains[0][0] = M8ChainStep(phrase=0, transpose=0)

        # Add to song
        project.song[0][0] = 0

        project.validate()  # Should not raise

    def test_project_invalid_instrument_ref(self):
        """Test that project with invalid instrument reference fails."""
        project = M8Project.initialise()

        # Add phrase with invalid instrument reference
        project.phrases[0][0] = M8PhraseStep(note=36, velocity=0xFF, instrument=200)

        with self.assertRaises(ValueError) as ctx:
            project.validate()
        self.assertIn("instrument", str(ctx.exception).lower())

    def test_project_invalid_chain_ref(self):
        """Test that project with invalid chain reference fails."""
        project = M8Project.initialise()

        # Add invalid chain reference to song
        project.song[0][0] = 200

        with self.assertRaises(ValueError) as ctx:
            project.validate()
        self.assertIn("chain", str(ctx.exception).lower())


class TestChainBuilderValidation(unittest.TestCase):
    """Tests for ChainBuilder slice limit validation."""

    def test_chain_builder_max_slices(self):
        """Test that ChainBuilder allows up to 128 slices."""
        from m8.tools.chain_builder import ChainBuilder
        from pydub import AudioSegment

        builder = ChainBuilder(slice_duration_ms=100)

        # Create 128 short samples (at the limit)
        samples = []
        for _ in range(128):
            samples.append(AudioSegment.silent(duration=50, frame_rate=44100))

        # Should not raise
        chain_wav, mapping = builder.build_chain(samples)
        self.assertEqual(len(mapping), 128)

    def test_chain_builder_too_many_slices(self):
        """Test that ChainBuilder rejects more than 128 slices."""
        from m8.tools.chain_builder import ChainBuilder
        from pydub import AudioSegment

        builder = ChainBuilder(slice_duration_ms=100)

        # Create 129 samples (one over the limit)
        samples = []
        for _ in range(129):
            samples.append(AudioSegment.silent(duration=50, frame_rate=44100))

        with self.assertRaises(ValueError) as ctx:
            builder.build_chain(samples)
        self.assertIn("128", str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
