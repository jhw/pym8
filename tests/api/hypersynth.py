"""HyperSynth-specific tests. Cross-cutting behaviour lives in instruments.py.

HyperSynth's distinguishing features are the 7-byte default_chord and the
16-row chord matrix at byte 87. The chord matrix is structured (mask + 6
offsets per row) so it's stored as a separate Python attribute, not as
descriptors — these tests cover that path.
"""
import unittest

from m8.api.instrument import M8InstrumentType
from m8.api.instruments.hypersynth import (
    CHORD_BYTES, CHORD_COUNT, CHORDS_OFFSET,
    M8Chord, M8HyperSynth, M8HyperSynthChords, M8HyperSynthModDest,
)


class TestM8Chord(unittest.TestCase):
    def test_default(self):
        c = M8Chord()
        self.assertEqual(c.mask, 0)
        self.assertEqual(c.offsets, [0, 0, 0, 0, 0, 0])

    def test_binary_round_trip(self):
        c = M8Chord(mask=0b00010101, offsets=[0, 3, 7, 12, 0, 0])
        self.assertEqual(c.write(), bytes([0b00010101, 0, 3, 7, 12, 0, 0]))
        self.assertEqual(M8Chord.read(c.write()), c)

    def test_is_osc_on(self):
        c = M8Chord(mask=0b00100101)
        self.assertTrue(c.is_osc_on(0))
        self.assertFalse(c.is_osc_on(1))
        self.assertTrue(c.is_osc_on(2))
        self.assertTrue(c.is_osc_on(5))
        self.assertFalse(c.is_osc_on(3))

    def test_is_osc_on_out_of_range(self):
        c = M8Chord()
        with self.assertRaises(IndexError):
            c.is_osc_on(6)
        with self.assertRaises(IndexError):
            c.is_osc_on(-1)

    def test_offsets_wrong_length_rejected(self):
        with self.assertRaises(ValueError):
            M8Chord(offsets=[0, 0, 0])

    def test_dict_round_trip(self):
        c = M8Chord(mask=0xFF, offsets=[1, 2, 3, 4, 5, 6])
        reloaded = M8Chord.from_dict(c.to_dict())
        self.assertEqual(reloaded, c)

    def test_clone_independent(self):
        c = M8Chord(mask=0x0F, offsets=[1, 2, 3, 4, 5, 6])
        cl = c.clone()
        cl.mask = 0xFF
        cl.offsets[0] = 99
        self.assertEqual(c.mask, 0x0F)
        self.assertEqual(c.offsets[0], 1)


class TestM8HyperSynthChords(unittest.TestCase):
    def test_default_count(self):
        chords = M8HyperSynthChords()
        self.assertEqual(len(chords), CHORD_COUNT)
        for c in chords:
            self.assertIsInstance(c, M8Chord)

    def test_binary_round_trip(self):
        chords = M8HyperSynthChords()
        chords[0] = M8Chord(mask=0b111, offsets=[0, 4, 7, 0, 0, 0])
        chords[CHORD_COUNT - 1] = M8Chord(mask=0xFF, offsets=[1, 2, 3, 4, 5, 6])

        data = chords.write()
        self.assertEqual(len(data), CHORD_COUNT * CHORD_BYTES)
        reloaded = M8HyperSynthChords.read(data)
        self.assertEqual(reloaded[0], chords[0])
        self.assertEqual(reloaded[CHORD_COUNT - 1], chords[CHORD_COUNT - 1])

    def test_dict_round_trip(self):
        chords = M8HyperSynthChords()
        chords[2] = M8Chord(mask=0x21, offsets=[0, 0, 0, 0, 0, 12])
        reloaded = M8HyperSynthChords.from_dict(chords.to_dict())
        self.assertEqual(reloaded[2], chords[2])
        self.assertEqual(len(reloaded), CHORD_COUNT)

    def test_from_dict_pads_short_input(self):
        """If the dict has fewer than 16 chords, the rest get default-initialised."""
        short = [{"mask": 1, "offsets": [0, 0, 0, 0, 0, 0]}]
        chords = M8HyperSynthChords.from_dict(short)
        self.assertEqual(len(chords), CHORD_COUNT)
        self.assertEqual(chords[0].mask, 1)
        self.assertEqual(chords[15], M8Chord())


class TestM8HyperSynth(unittest.TestCase):
    def test_type_is_five(self):
        self.assertEqual(M8HyperSynth.TYPE_ID, M8InstrumentType.HYPERSYNTH)
        self.assertEqual(M8HyperSynth().type_id, 5)

    def test_default_chord_default(self):
        h = M8HyperSynth()
        self.assertEqual(h.default_chord, [0, 0, 0, 0, 0, 0, 0])

    def test_default_chord_round_trip(self):
        h = M8HyperSynth(name="HC")
        h.default_chord = [0, 4, 7, 11, 0, 0, 0]  # maj7
        reloaded = M8HyperSynth.read(h.write())
        self.assertEqual(reloaded.default_chord, [0, 4, 7, 11, 0, 0, 0])

    def test_default_chord_wrong_length_rejected(self):
        h = M8HyperSynth()
        with self.assertRaises(ValueError):
            h.default_chord = [0, 4, 7]

    def test_chords_preserved_through_binary(self):
        h = M8HyperSynth(name="HS")
        h.chords[0] = M8Chord(mask=0b111, offsets=[0, 4, 7, 0, 0, 0])
        h.chords[7] = M8Chord(mask=0xFF, offsets=[0, 0, 0, 0, 0, 12])
        reloaded = M8HyperSynth.read(h.write())
        self.assertEqual(reloaded.chords[0].mask, 0b111)
        self.assertEqual(reloaded.chords[0].offsets, [0, 4, 7, 0, 0, 0])
        self.assertEqual(reloaded.chords[7].mask, 0xFF)
        self.assertEqual(reloaded.chords[7].offsets[5], 12)

    def test_chords_serialized_at_correct_offset(self):
        """Chord region must start at the byte the Rust spec defines (87)."""
        h = M8HyperSynth()
        h.chords[0] = M8Chord(mask=0xAB, offsets=[1, 2, 3, 4, 5, 6])
        data = h.write()
        self.assertEqual(data[CHORDS_OFFSET], 0xAB)
        self.assertEqual(data[CHORDS_OFFSET + 1:CHORDS_OFFSET + 7], bytes([1, 2, 3, 4, 5, 6]))

    def test_chords_in_dict_round_trip(self):
        h = M8HyperSynth(name="HCD")
        h.chords[3] = M8Chord(mask=0b101010, offsets=[1, 0, 2, 0, 3, 0])
        h.scale = 0x05
        params = h.to_dict()
        self.assertIn("chords", params)
        self.assertEqual(params["chords"][3]["mask"], 0b101010)

        reloaded = M8HyperSynth.from_dict(params)
        self.assertEqual(reloaded.chords[3], h.chords[3])
        self.assertEqual(reloaded.scale, 0x05)

    def test_clone_chords_independent(self):
        h = M8HyperSynth()
        h.chords[0] = M8Chord(mask=0xFF, offsets=[1, 2, 3, 4, 5, 6])
        cloned = h.clone()
        self.assertIsNot(cloned.chords, h.chords)
        self.assertIsNot(cloned.chords[0], h.chords[0])
        cloned.chords[0].mask = 0x00
        self.assertEqual(h.chords[0].mask, 0xFF)

    def test_constructor_chords_kwarg(self):
        """Passing `chords=` as a kwarg should not be clobbered by base __init__."""
        custom = M8HyperSynthChords()
        custom[0] = M8Chord(mask=0xCA, offsets=[7, 7, 7, 7, 7, 7])
        h = M8HyperSynth(name="KW", chords=custom)
        self.assertIs(h.chords, custom)
        self.assertEqual(h.chords[0].mask, 0xCA)

    def test_mod_dest_enum(self):
        """HyperSynth-specific destinations include SHIFT/SWARM/WIDTH/SUBOSC."""
        self.assertEqual(M8HyperSynth.MOD_DEST_ENUM_CLASS, M8HyperSynthModDest)
        self.assertEqual(M8HyperSynthModDest.SHIFT, 0x03)
        self.assertEqual(M8HyperSynthModDest.SWARM, 0x04)
        self.assertEqual(M8HyperSynthModDest.WIDTH, 0x05)
        self.assertEqual(M8HyperSynthModDest.SUBOSC, 0x06)
        self.assertEqual(M8HyperSynthModDest.MOD_BINV, 0x0E)


if __name__ == "__main__":
    unittest.main()
