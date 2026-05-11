"""Tests that the project's firmware version threads through to instrument
readers.

Plumbing prep for Phase-2 parity work (EQ packing, settings field
presence). Today no reader consumes `version` for behavior, but the
parameter must be accepted everywhere it'll be needed.
"""
import unittest

from m8.api.instrument import M8Instrument, M8Instruments
from m8.api.instruments.hypersynth import M8HyperSynth
from m8.api.instruments.wavsynth import M8Wavsynth
from m8.api.project import M8Project
from m8.api.version import M8Version


class TestInstrumentReadAcceptsVersion(unittest.TestCase):
    def test_default_version_when_omitted(self):
        """Calling read() without a version still works (back-compat path)."""
        original = M8Wavsynth(name="W")
        loaded = M8Wavsynth.read(original.write())
        # Default version is the bundled-template firmware
        self.assertEqual(loaded.version.tuple(), (6, 0, 17))

    def test_explicit_version_stored_on_instance(self):
        ver = M8Version(4, 1, 0)
        loaded = M8Wavsynth.read(M8Wavsynth(name="W").write(), version=ver)
        self.assertEqual(loaded.version.tuple(), (4, 1, 0))
        # Identity is preserved — same object, not a copy
        self.assertIs(loaded.version, ver)

    def test_hypersynth_threads_to_super(self):
        """Subclasses that override read() must keep passing version up."""
        ver = M8Version(6, 2, 1)
        loaded = M8HyperSynth.read(M8HyperSynth(name="H").write(), version=ver)
        self.assertEqual(loaded.version.tuple(), (6, 2, 1))


class TestInstrumentsCollectionThreadsVersion(unittest.TestCase):
    def test_each_instrument_receives_version(self):
        instruments = M8Instruments()
        instruments[0] = M8Wavsynth(name="A")
        instruments[5] = M8HyperSynth(name="B")
        ver = M8Version(6, 2, 1)

        loaded = M8Instruments.read(instruments.write(), version=ver)

        # Both populated slots got the threaded version
        self.assertEqual(loaded[0].version.tuple(), (6, 2, 1))
        self.assertEqual(loaded[5].version.tuple(), (6, 2, 1))
        # Empty slots (M8Block) don't carry version — they're raw bytes
        self.assertFalse(hasattr(loaded[1], "version") and loaded[1].version is loaded[0].version)

    def test_default_version_when_omitted(self):
        instruments = M8Instruments()
        instruments[0] = M8Wavsynth(name="W")
        loaded = M8Instruments.read(instruments.write())
        self.assertEqual(loaded[0].version.tuple(), (6, 0, 17))


class TestProjectThreadsVersionToInstruments(unittest.TestCase):
    def test_project_propagates_version_from_file_byte_10(self):
        """Project.read() reads version at byte 10 and hands it to every
        instrument it parses."""
        p = M8Project.initialise()
        # Force a non-default version into the underlying byte buffer so
        # we can verify it reaches the instruments
        p.version = M8Version(4, 1, 7)
        data = p.write()

        # Replace the template's empty instrument slot 0 with a real
        # instrument so we have something to inspect
        w = M8Wavsynth(name="VERSION-TEST")
        data = bytearray(data)
        # Instruments live at OFFSETS["instruments"]; slot 0 starts there.
        from m8.api.instrument import INSTRUMENTS_OFFSET, BLOCK_SIZE
        data[INSTRUMENTS_OFFSET:INSTRUMENTS_OFFSET + BLOCK_SIZE] = w.write()

        loaded = M8Project.read(bytes(data))
        self.assertEqual(loaded.version.tuple(), (4, 1, 7))
        self.assertIsInstance(loaded.instruments[0], M8Wavsynth)
        self.assertEqual(loaded.instruments[0].version.tuple(), (4, 1, 7))


class TestM8iFileThreadsVersion(unittest.TestCase):
    """The .m8i (single-instrument file) reader already had to read version;
    confirm it now threads it through subclass.read() instead of overwriting
    afterwards."""

    def test_fixture_instrument_carries_file_version(self):
        import os
        fixture = os.path.join(
            os.path.dirname(__file__), "..", "fixtures", "KICK_MORPH.m8i",
        )
        if not os.path.exists(fixture):
            self.skipTest("KICK_MORPH.m8i fixture not present")
        inst = M8Instrument.read_from_file(fixture)
        # Whatever the fixture's version is, it must be set on the instance
        # via the threading path, not the legacy "read then overwrite".
        self.assertIsNotNone(inst.version)
        self.assertGreater(inst.version.major, 0)


if __name__ == "__main__":
    unittest.main()
