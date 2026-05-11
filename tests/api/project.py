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
        """OFFSETS used to list unimplemented sections (groove, eq, scale...)
        that were never actually read or written, which was misleading.
        """
        self.assertEqual(
            set(OFFSETS),
            {"version", "metadata", "song", "phrases", "chains", "instruments"},
        )


if __name__ == "__main__":
    unittest.main()
