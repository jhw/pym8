# tests/api/roundtrip.py
"""Byte-exact read -> write guarantees for populated project data.

Format-faithful round-tripping is pym8's core guarantee (see CLAUDE.md /
docs/out-of-scope.md): M8Project.write() starts from the raw bytes it read
and only overwrites the sections it parses, so unmodelled bytes survive
untouched. This file locks that guarantee in with a committed test rather
than relying on anecdotal confidence, and is the safety net for any change
to the binary read/write layer (e.g. migrating a hand-rolled record like
M8ChainStep onto ByteField descriptors).
"""

import os
import unittest

from m8.api.chain import M8ChainStep
from m8.api.fx import M8FXTuple, M8SamplerFX, M8SequenceFX
from m8.api.phrase import M8Note, M8PhraseStep
from m8.api.project import M8Project

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")


class TestProjectRoundTrip(unittest.TestCase):
    """read(bytes).write() must reproduce the original bytes exactly."""

    def test_unmodified_real_project_round_trips_byte_identically(self):
        """A pure read -> write with no edits must reproduce the source
        file exactly, including metadata: EXTERNAL.m8s has stale non-zero
        bytes trailing the `directory` string's null terminator (left over
        from a previously-longer path), which used to get zeroed on every
        save regardless of whether metadata was touched."""
        fixture_path = os.path.join(FIXTURES_DIR, "EXTERNAL.m8s")
        with open(fixture_path, "rb") as f:
            original = f.read()

        project = M8Project.read(original)
        rewritten = project.write()

        self.assertEqual(rewritten, original)

    def test_populated_project_round_trips(self):
        """Exercise chain/phrase/FX data specifically (not just near-empty
        template defaults) so the golden test actually covers the classes
        most likely to break under a serialisation refactor."""
        project = M8Project.initialise()

        project.phrases[0][0] = M8PhraseStep(note=M8Note.C_4, velocity=0x7F, instrument=0x00)
        project.phrases[0][0].fx[0] = M8FXTuple(key=M8SequenceFX.RET, value=0x03)
        project.phrases[0][1] = M8PhraseStep(note=M8Note.E_4, velocity=0x60, instrument=0x01)
        project.phrases[0][1].fx[1] = M8FXTuple(key=M8SamplerFX.VOL, value=0x80)
        project.phrases[0][2] = M8PhraseStep()
        project.phrases[0][2].off()

        project.chains[0][0] = M8ChainStep(phrase=0x00, transpose=0x0C)
        project.chains[0][1] = M8ChainStep(phrase=0x01, transpose=0xF4)

        project.song[0][0] = 0x00

        first = project.write()
        reloaded = M8Project.read(first)
        second = reloaded.write()

        self.assertEqual(second, first, "populated project did not round-trip byte-identically")


if __name__ == "__main__":
    unittest.main()
