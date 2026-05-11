"""Tests for M8Project, including the clone() data-loss bug fix."""
import os
import tempfile
import unittest

from m8.api.project import M8Project, OFFSETS
from m8.api.metadata import M8Metadata
from m8.api.song import M8SongMatrix
from m8.api.chain import M8Chain, M8Chains
from m8.api.phrase import M8Phrase, M8Phrases
from m8.api.instrument import M8Instruments
from m8.api.instruments.sampler import M8Sampler


class TestM8Project(unittest.TestCase):
    def _build(self):
        project = M8Project()
        project.metadata = M8Metadata(name="Test Project")
        project.song = M8SongMatrix()
        project.chains = M8Chains()
        project.phrases = M8Phrases()
        project.instruments = M8Instruments()
        project.instruments[0] = M8Sampler(name="TestSynth")
        project.phrases[0][0].instrument = 0
        project.chains[0][0].phrase = 0
        project.song[0][0] = 0
        return project

    def test_write_read_round_trip(self):
        project = M8Project.initialise()
        with tempfile.NamedTemporaryFile(suffix='.m8s', delete=False) as tmp:
            tmp_path = tmp.name
        try:
            project.write_to_file(tmp_path)
            reloaded = M8Project.read_from_file(tmp_path)
            self.assertEqual(reloaded.metadata.name, project.metadata.name)
            self.assertEqual(len(reloaded.instruments), len(project.instruments))
        finally:
            os.unlink(tmp_path)

    def test_initialise(self):
        project = M8Project.initialise()
        self.assertIsNotNone(project.metadata)
        self.assertIsNotNone(project.song)
        self.assertIsNotNone(project.chains)
        self.assertIsNotNone(project.phrases)
        self.assertIsNotNone(project.instruments)

    def test_initialise_missing_template(self):
        with self.assertRaises(FileNotFoundError):
            M8Project.initialise("NONEXISTENT_TEMPLATE")

    def test_clone_preserves_components(self):
        original = self._build()
        clone = original.clone()
        self.assertIsNot(clone, original)
        self.assertIsNot(clone.metadata, original.metadata)
        self.assertIsNot(clone.instruments, original.instruments)
        self.assertEqual(clone.metadata.name, original.metadata.name)
        self.assertEqual(clone.instruments[0].name, "TestSynth")

    def test_clone_preserves_raw_data_for_round_trip(self):
        """Regression test: clone() used to drop the underlying byte buffer,
        causing write() to emit a truncated file missing the ~30 KB of
        unparsed sections (grooves, tables, EQ, settings, scales, MIDI maps).
        """
        original = M8Project.initialise()
        original.metadata.name = "CLONETEST"
        clone = original.clone()
        self.assertEqual(len(clone.data), len(original.data))
        self.assertEqual(clone.write(), original.write())

    def test_clone_independence(self):
        original = self._build()
        clone = original.clone()
        clone.metadata.name = "Modified"
        self.assertEqual(original.metadata.name, "Test Project")
        self.assertEqual(clone.metadata.name, "Modified")

    def test_offsets_dict_only_lists_implemented_sections(self):
        """OFFSETS used to list unimplemented sections (groove, scale...)
        that were never actually read or written. Each name in OFFSETS now
        must correspond to a section that M8Project.read() actually parses.
        """
        self.assertEqual(
            set(OFFSETS),
            {
                "version", "metadata", "midi",
                "mixer", "grooves", "effects", "midi_mappings", "scales", "eqs",
                "song", "phrases", "chains", "tables", "instruments",
            },
        )


class TestProjectErrorHandling(unittest.TestCase):
    def test_read_nonexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            M8Project.read_from_file("/nonexistent/path/file.m8s")

    def test_write_to_invalid_path(self):
        project = M8Project.initialise()
        with self.assertRaises((OSError, FileNotFoundError)):
            project.write_to_file("/nonexistent/directory/file.m8s")


class TestMetadataEdgeCasesViaProject(unittest.TestCase):
    """Edge values on metadata fields reached via M8Project.initialise()."""

    def test_empty_name(self):
        project = M8Project.initialise()
        project.metadata.name = ""
        self.assertEqual(project.metadata.name, "")

    def test_special_characters_in_name(self):
        project = M8Project.initialise()
        project.metadata.name = "TEST-123"
        self.assertEqual(project.metadata.name, "TEST-123")

    def test_tempo_boundary_values(self):
        project = M8Project.initialise()
        project.metadata.tempo = 60.0
        self.assertEqual(project.metadata.tempo, 60.0)
        project.metadata.tempo = 300.0
        self.assertEqual(project.metadata.tempo, 300.0)


class TestProjectBinaryRoundtrip(unittest.TestCase):
    """End-to-end .m8s file write + read."""

    def test_empty_project_roundtrip(self):
        from m8.api.phrase import M8PhraseStep, M8Note
        from m8.api.chain import M8ChainStep
        original = M8Project.initialise()
        with tempfile.NamedTemporaryFile(suffix=".m8s", delete=False) as f:
            tmp_path = f.name
        try:
            original.write_to_file(tmp_path)
            loaded = M8Project.read_from_file(tmp_path)
            self.assertIsNotNone(loaded.metadata)
            self.assertIsNotNone(loaded.instruments)
            self.assertIsNotNone(loaded.phrases)
            self.assertIsNotNone(loaded.chains)
            self.assertIsNotNone(loaded.song)
        finally:
            os.unlink(tmp_path)

    def test_populated_project_roundtrip(self):
        from m8.api.phrase import M8PhraseStep, M8Note
        from m8.api.chain import M8ChainStep
        original = M8Project.initialise()
        original.metadata.name = "FULLTEST"
        original.metadata.tempo = 145.5
        original.instruments[0] = M8Sampler(name="KICK")
        original.phrases[0][0] = M8PhraseStep(note=M8Note.C_4, velocity=0xFF, instrument=0)
        original.chains[0][0] = M8ChainStep(phrase=0, transpose=0)
        original.song[0][0] = 0

        with tempfile.NamedTemporaryFile(suffix=".m8s", delete=False) as f:
            tmp_path = f.name
        try:
            original.write_to_file(tmp_path)
            loaded = M8Project.read_from_file(tmp_path)
            self.assertEqual(loaded.metadata.name, "FULLTEST")
            self.assertEqual(loaded.metadata.tempo, 145.5)
            self.assertEqual(loaded.instruments[0].name, "KICK")
            self.assertEqual(loaded.phrases[0][0].note, M8Note.C_4)
            self.assertEqual(loaded.chains[0][0].phrase, 0)
            self.assertEqual(loaded.song[0][0], 0)
        finally:
            os.unlink(tmp_path)


class TestProjectValidation(unittest.TestCase):
    def test_project_valid(self):
        M8Project.initialise().validate()

    def test_project_valid_with_content(self):
        from m8.api.phrase import M8PhraseStep, M8Note
        from m8.api.chain import M8ChainStep
        project = M8Project.initialise()
        project.metadata.name = "TEST"
        project.instruments[0] = M8Sampler(name="KICK")
        project.phrases[0][0] = M8PhraseStep(note=M8Note.C_4, velocity=0xFF, instrument=0)
        project.chains[0][0] = M8ChainStep(phrase=0, transpose=0)
        project.song[0][0] = 0
        project.validate()

    def test_project_invalid_instrument_ref(self):
        from m8.api.phrase import M8PhraseStep
        project = M8Project.initialise()
        project.phrases[0][0] = M8PhraseStep(note=36, velocity=0xFF, instrument=200)
        with self.assertRaises(ValueError) as ctx:
            project.validate()
        self.assertIn("instrument", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
