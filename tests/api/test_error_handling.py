# tests/api/test_error_handling.py
"""Tests for error handling and edge cases."""

import unittest
import os
import tempfile
from m8.api.project import M8Project
from m8.api.instruments.sampler import M8Sampler, M8SamplerParam
from m8.api.instruments.wavsynth import M8Wavsynth
from m8.api.instrument import M8Instrument, M8InstrumentType
from m8.api.phrase import M8Phrase, M8PhraseStep, M8Note
from m8.api.chain import M8Chain, M8ChainStep
from m8.api.metadata import M8Metadata


class TestInstrumentErrorHandling(unittest.TestCase):
    """Tests for instrument error handling."""

    def test_unknown_instrument_type_in_factory(self):
        """Test factory raises error for unknown type string."""
        params = {
            'type': 'INVALID_TYPE',
            'name': 'Test',
            'params': {},
            'modulators': []
        }
        with self.assertRaises(ValueError):
            M8Instrument.from_dict(params)

    def test_unknown_instrument_type_id(self):
        """Test factory raises error for unknown integer type."""
        params = {
            'type': 99,  # Invalid type ID
            'name': 'Test',
            'params': {},
            'modulators': []
        }
        with self.assertRaises(ValueError):
            M8Instrument.from_dict(params)

    def test_parameter_value_masking(self):
        """Test that parameter values are masked to 8-bit."""
        sampler = M8Sampler(name="Test")

        # Set value larger than 0xFF
        sampler.set(M8SamplerParam.VOLUME, 0x1FF)

        # Should be masked to 0xFF
        self.assertEqual(sampler.get(M8SamplerParam.VOLUME), 0xFF)

    def test_name_truncation(self):
        """Test that long names are truncated."""
        # Name field is 12 bytes
        long_name = "THIS_IS_A_VERY_LONG_NAME"
        sampler = M8Sampler(name=long_name)

        # Name should be truncated
        self.assertEqual(len(sampler.name), 12)
        self.assertEqual(sampler.name, "THIS_IS_A_VE")


class TestProjectErrorHandling(unittest.TestCase):
    """Tests for project error handling."""

    def test_read_nonexistent_file(self):
        """Test reading non-existent file raises error."""
        with self.assertRaises(FileNotFoundError):
            M8Project.read_from_file("/nonexistent/path/file.m8s")

    def test_write_to_invalid_path(self):
        """Test writing to invalid path raises error."""
        project = M8Project.initialise()

        with self.assertRaises((OSError, FileNotFoundError)):
            project.write_to_file("/nonexistent/directory/file.m8s")


class TestMetadataEdgeCases(unittest.TestCase):
    """Tests for metadata edge cases."""

    def test_empty_name(self):
        """Test empty project name."""
        project = M8Project.initialise()
        project.metadata.name = ""

        self.assertEqual(project.metadata.name, "")

    def test_special_characters_in_name(self):
        """Test special characters in name."""
        project = M8Project.initialise()
        project.metadata.name = "TEST-123"

        self.assertEqual(project.metadata.name, "TEST-123")

    def test_tempo_boundary_values(self):
        """Test tempo at boundary values."""
        project = M8Project.initialise()

        # Low tempo
        project.metadata.tempo = 60.0
        self.assertEqual(project.metadata.tempo, 60.0)

        # High tempo
        project.metadata.tempo = 300.0
        self.assertEqual(project.metadata.tempo, 300.0)


class TestChainBoundaryConditions(unittest.TestCase):
    """Tests for chain boundary conditions."""

    def test_empty_phrase_reference(self):
        """Test empty phrase reference (255)."""
        step = M8ChainStep()
        self.assertEqual(step.phrase, 255)  # EMPTY_PHRASE

    def test_max_phrase_reference(self):
        """Test maximum valid phrase reference."""
        step = M8ChainStep(phrase=254, transpose=0)
        self.assertEqual(step.phrase, 254)

    def test_transpose_boundary_values(self):
        """Test transpose at boundary values."""
        chain = M8Chain()

        # Maximum positive transpose
        chain[0] = M8ChainStep(phrase=0, transpose=127)
        self.assertEqual(chain[0].transpose, 127)

        # Maximum negative transpose (two's complement)
        chain[1] = M8ChainStep(phrase=0, transpose=128)
        self.assertEqual(chain[1].transpose, 128)


class TestPhraseBoundaryConditions(unittest.TestCase):
    """Tests for phrase boundary conditions."""

    def test_empty_note(self):
        """Test empty note value (255)."""
        step = M8PhraseStep()
        self.assertEqual(step.note, 255)  # EMPTY_NOTE

    def test_off_note(self):
        """Test OFF note value."""
        step = M8PhraseStep(note=M8Note.C_4, velocity=0xFF, instrument=0)
        step.off()
        self.assertEqual(step.note, 0x80)  # OFF_NOTE = 128

    def test_max_velocity(self):
        """Test maximum velocity value."""
        step = M8PhraseStep(note=M8Note.C_4, velocity=0xFF, instrument=0)
        self.assertEqual(step.velocity, 0xFF)

    def test_zero_velocity(self):
        """Test zero velocity value."""
        step = M8PhraseStep(note=M8Note.C_4, velocity=0x00, instrument=0)
        self.assertEqual(step.velocity, 0x00)

    def test_max_instrument_reference(self):
        """Test maximum instrument reference."""
        step = M8PhraseStep(note=M8Note.C_4, velocity=0xFF, instrument=127)
        self.assertEqual(step.instrument, 127)


class TestSongMatrixBoundaryConditions(unittest.TestCase):
    """Tests for song matrix boundary conditions."""

    def test_empty_chain_reference(self):
        """Test empty chain reference (255)."""
        project = M8Project.initialise()
        # Default should be empty (255)
        self.assertEqual(project.song[0][0], 255)

    def test_max_row_access(self):
        """Test accessing maximum row."""
        project = M8Project.initialise()
        project.song[254][0] = 0x00  # Row 254 (0-indexed)
        self.assertEqual(project.song[254][0], 0x00)

    def test_max_column_access(self):
        """Test accessing maximum column (track 8)."""
        project = M8Project.initialise()
        project.song[0][7] = 0x00  # Column 7 (0-indexed, 8 tracks)
        self.assertEqual(project.song[0][7], 0x00)


class TestInstrumentCollectionEdgeCases(unittest.TestCase):
    """Tests for instrument collection edge cases."""

    def test_max_instrument_slot(self):
        """Test using maximum instrument slot."""
        project = M8Project.initialise()
        project.instruments[127] = M8Sampler(name="LAST")

        self.assertEqual(project.instruments[127].name, "LAST")

    def test_replace_instrument(self):
        """Test replacing an existing instrument."""
        project = M8Project.initialise()

        project.instruments[0] = M8Sampler(name="FIRST")
        project.instruments[0] = M8Wavsynth(name="SECOND")

        self.assertIsInstance(project.instruments[0], M8Wavsynth)
        self.assertEqual(project.instruments[0].name, "SECOND")


class TestBinaryRoundtripEdgeCases(unittest.TestCase):
    """Tests for binary roundtrip edge cases."""

    def test_all_empty_project_roundtrip(self):
        """Test roundtrip of completely empty project."""
        original = M8Project.initialise()

        with tempfile.NamedTemporaryFile(suffix='.m8s', delete=False) as f:
            temp_path = f.name

        try:
            original.write_to_file(temp_path)
            loaded = M8Project.read_from_file(temp_path)

            # Verify it's still valid
            self.assertIsNotNone(loaded.metadata)
            self.assertIsNotNone(loaded.instruments)
            self.assertIsNotNone(loaded.phrases)
            self.assertIsNotNone(loaded.chains)
            self.assertIsNotNone(loaded.song)
        finally:
            os.unlink(temp_path)

    def test_full_project_roundtrip(self):
        """Test roundtrip of project with all slots populated."""
        original = M8Project.initialise()
        original.metadata.name = "FULLTEST"
        original.metadata.tempo = 145.5

        # Add instrument to slot 0
        original.instruments[0] = M8Sampler(name="KICK")

        # Add a phrase
        original.phrases[0][0] = M8PhraseStep(note=M8Note.C_4, velocity=0xFF, instrument=0)

        # Add a chain
        original.chains[0][0] = M8ChainStep(phrase=0, transpose=0)

        # Add to song
        original.song[0][0] = 0

        with tempfile.NamedTemporaryFile(suffix='.m8s', delete=False) as f:
            temp_path = f.name

        try:
            original.write_to_file(temp_path)
            loaded = M8Project.read_from_file(temp_path)

            self.assertEqual(loaded.metadata.name, "FULLTEST")
            self.assertEqual(loaded.metadata.tempo, 145.5)
            self.assertEqual(loaded.instruments[0].name, "KICK")
            self.assertEqual(loaded.phrases[0][0].note, M8Note.C_4)
            self.assertEqual(loaded.chains[0][0].phrase, 0)
            self.assertEqual(loaded.song[0][0], 0)
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()
