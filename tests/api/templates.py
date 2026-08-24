"""Tests that the shipped firmware template loads and round-trips cleanly.

pym8 targets firmware 6.0+; only TEMPLATE-6-6-2 is bundled. Unlike the
older TEMPLATE-6-2-1.m8s this template carries no stray bytes past the
null terminator in the directory field, so read→write is byte-exact.

We also test *stable* round-trip: read→write→read→write produces
identical bytes the second time around. If the parser misinterprets a
section, the second write would also be wrong but in a consistent way —
this catches the more interesting bugs: corruption introduced *between*
the two reads.
"""
import os
import unittest
import warnings

from m8.api.project import M8Project


TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "m8", "templates")
TEMPLATE_NAME = "TEMPLATE-6-6-2"
EXPECTED_VERSION = (6, 6, 2)
EXPECTED_METADATA_NAME = "TEMPLATE-662"


class TestShippedTemplate(unittest.TestCase):
    def _path(self):
        return os.path.join(TEMPLATE_DIR, f"{TEMPLATE_NAME}.m8s")

    def test_loads_without_warnings(self):
        """A clean template should parse with no unsupported-type warnings."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            M8Project.read_from_file(self._path())
        self.assertEqual([str(w.message) for w in caught], [])

    def test_version_parses(self):
        p = M8Project.read_from_file(self._path())
        self.assertEqual(p.version.tuple(), EXPECTED_VERSION)

    def test_metadata_name(self):
        p = M8Project.read_from_file(self._path())
        self.assertEqual(p.metadata.name, EXPECTED_METADATA_NAME)

    def test_structure_present(self):
        p = M8Project.read_from_file(self._path())
        self.assertIsNotNone(p.metadata)
        self.assertEqual(len(p.instruments), 128)
        self.assertIsNotNone(p.song)
        self.assertIsNotNone(p.chains)
        self.assertIsNotNone(p.phrases)

    def test_byte_exact_round_trip(self):
        """read→write should reproduce the file exactly, byte for byte."""
        raw = open(self._path(), "rb").read()
        p = M8Project.read(raw)
        self.assertEqual(raw, bytes(p.write()))

    def test_stable_round_trip(self):
        """read→write twice should produce identical bytes the second time."""
        p1 = M8Project.read_from_file(self._path())
        bytes1 = p1.write()
        p2 = M8Project.read(bytes1)
        bytes2 = p2.write()
        self.assertEqual(bytes1, bytes2,
                         "round-trip not stable: parser is non-idempotent")

    def test_initialise_resolves_by_name(self):
        p = M8Project.initialise(TEMPLATE_NAME)
        self.assertEqual(p.metadata.name, EXPECTED_METADATA_NAME)

    def test_initialise_default(self):
        """initialise() with no arg should use the shipped template."""
        p = M8Project.initialise()
        self.assertEqual(p.metadata.name, EXPECTED_METADATA_NAME)


if __name__ == "__main__":
    unittest.main()
