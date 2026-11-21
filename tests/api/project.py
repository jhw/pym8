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
from m8.api.instruments.fmsynth import M8FMSynth
from m8.api.instruments.wavsynth import M8Wavsynth
from m8.api.instrument_file import M8InstrumentFile
from m8.api.eq import M8Eq, NO_EQ
from m8.api.version import M8Version


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

    def test_read_truncated_data_raises(self):
        """Regression: a truncated .m8s used to silently produce a mangled
        project (short sections read as short slices) instead of failing.
        Matches m8-file-parser's length check in songs.rs, which raises a
        ParseError rather than reading past-EOF as zeros.

        Truncate right at MIN_SIZE (the boundary pym8 actually enforces),
        not just the last byte of the file — the bundled template carries
        trailing reserved padding past MIN_SIZE, so lopping off its last
        byte wouldn't touch any section pym8 parses."""
        full = M8Project.initialise().write()
        with self.assertRaises(ValueError):
            M8Project.read(full[:M8Project.MIN_SIZE - 1])

    def test_read_pre_6_0_names_firmware(self):
        """A pre-6.0 song is shorter than MIN_SIZE too, but the error should
        say it's old firmware, not that the file is truncated."""
        data = bytearray(M8Project.initialise().write())
        data[10:14] = M8Version(3, 0, 1).write()
        with self.assertRaisesRegex(ValueError, r"Firmware 3\.0\.1 project"):
            M8Project.read(bytes(data[:109854]))

    def test_read_empty_data_raises(self):
        with self.assertRaises(ValueError):
            M8Project.read(b"")

    def test_read_minimum_size_data_succeeds(self):
        full = M8Project.initialise().write()
        self.assertGreaterEqual(len(full), M8Project.MIN_SIZE)
        M8Project.read(full[:M8Project.MIN_SIZE])  # exact minimum size must not raise


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


class TestProjectDeepValidation(unittest.TestCase):
    """check_references() / validate(deep=True) — referential integrity
    beyond byte-range checks: song->chain->phrase->instrument must resolve
    to real, populated data, not just in-range indices."""

    def _wired_project(self):
        from m8.api.phrase import M8PhraseStep, M8Note
        from m8.api.chain import M8ChainStep
        project = M8Project.initialise()
        project.instruments[0] = M8Sampler(name="KICK")
        project.phrases[0][0] = M8PhraseStep(note=M8Note.C_4, velocity=0xFF, instrument=0)
        project.chains[0][0] = M8ChainStep(phrase=0, transpose=0)
        project.song[0][0] = 0
        return project

    def test_fully_wired_project_has_no_problems(self):
        project = self._wired_project()
        self.assertEqual(project.check_references(), [])
        project.validate(deep=True)  # no raise

    def test_song_references_empty_chain(self):
        project = M8Project.initialise()
        project.song[0][0] = 5  # chain 5 has no phrase references
        problems = project.check_references()
        self.assertEqual(len(problems), 1)
        self.assertIn("song[0][0]", problems[0])
        self.assertIn("chain 5", problems[0])
        with self.assertRaises(ValueError) as ctx:
            project.validate(deep=True)
        self.assertIn("song[0][0]", str(ctx.exception))

    def test_chain_references_empty_phrase(self):
        from m8.api.chain import M8ChainStep
        project = M8Project.initialise()
        project.chains[0][0] = M8ChainStep(phrase=7, transpose=0)  # phrase 7 is empty
        project.song[0][0] = 0
        problems = project.check_references()
        self.assertEqual(len(problems), 1)
        self.assertIn("chain 0 step 0", problems[0])
        self.assertIn("phrase 7", problems[0])

    def test_phrase_references_non_concrete_instrument(self):
        from m8.api.phrase import M8PhraseStep, M8Note
        from m8.api.chain import M8ChainStep
        project = M8Project.initialise()
        # instrument slot 3 is left as the default empty M8Block slot
        project.phrases[0][0] = M8PhraseStep(note=M8Note.C_4, velocity=0xFF, instrument=3)
        project.chains[0][0] = M8ChainStep(phrase=0, transpose=0)
        project.song[0][0] = 0
        problems = project.check_references()
        self.assertEqual(len(problems), 1)
        self.assertIn("phrase 0 step 0", problems[0])
        self.assertIn("instrument 3", problems[0])

    def test_shallow_validate_ignores_dangling_references(self):
        """deep=False (the default) must not be affected by this new check —
        it only catches byte-range/count problems, same as before."""
        project = M8Project.initialise()
        project.song[0][0] = 5  # dangling reference, but a valid byte value
        project.validate()  # no raise

    def test_deep_validate_reports_multiple_problems(self):
        project = M8Project.initialise()
        project.song[0][0] = 5
        project.song[1][0] = 6
        with self.assertRaises(ValueError) as ctx:
            project.validate(deep=True)
        self.assertIn("2 dangling", str(ctx.exception))


class TestImportExportInstrument(unittest.TestCase):
    FIXTURE = os.path.join(os.path.dirname(__file__), "..", "fixtures", "METRONOME.m8i")

    def setUp(self):
        self.project = M8Project.initialise()
        self.file = M8InstrumentFile.read_from_file(self.FIXTURE)

    def test_import_into_first_empty_slot(self):
        self.project.instruments[0] = M8Wavsynth(name="TAKEN")
        slot = self.project.import_instrument(self.file)
        self.assertEqual(slot, 1)
        self.assertIsInstance(self.project.instruments[1], M8FMSynth)
        self.assertEqual(self.project.tables[1].write(), self.file.table.write())
        self.assertEqual(self.project.instruments[1].associated_eq, NO_EQ)

    def test_import_with_eq_pairs_eq_with_slot(self):
        self.file.eq = M8Eq()
        self.file.eq.mid.level = 0x22
        self.file.instrument.associated_eq = 40   # source project's numbering
        slot = self.project.import_instrument(self.file, slot=7)
        self.assertEqual(slot, 7)
        self.assertEqual(self.project.instruments[7].associated_eq, 7)
        self.assertEqual(self.project.eqs[7].mid.level, 0x22)
        # The file object is left untouched.
        self.assertEqual(self.file.instrument.associated_eq, 40)

    def test_import_without_empty_slot_raises(self):
        for i in range(len(self.project.instruments)):
            self.project.instruments[i] = M8Wavsynth(name="X")
        with self.assertRaises(ValueError):
            self.project.import_instrument(self.file)

    def test_import_slot_out_of_range_raises(self):
        with self.assertRaises(IndexError):
            self.project.import_instrument(self.file, slot=128)

    def test_export_then_import_round_trips(self):
        self.file.eq = M8Eq()
        self.file.eq.low.level = 0x33
        self.project.import_instrument(self.file, slot=3)

        exported = self.project.export_instrument(3)
        self.assertEqual(exported.eq.low.level, 0x33)
        self.assertEqual(exported.instrument.associated_eq, 3)

        other = M8Project.initialise()
        other.import_instrument(M8InstrumentFile.read(exported.write()), slot=9)
        self.assertEqual(other.instruments[9].name, "METRONOME")
        self.assertEqual(other.tables[9].write(), self.file.table.write())
        self.assertEqual(other.eqs[9].low.level, 0x33)

    def test_export_without_eq(self):
        self.project.import_instrument(self.file, slot=2)
        self.assertIsNone(self.project.export_instrument(2).eq)

    def test_export_empty_slot_raises(self):
        with self.assertRaises(ValueError):
            self.project.export_instrument(50)


if __name__ == "__main__":
    unittest.main()
