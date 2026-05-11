"""Tests for M8Scale / M8Scales."""
import unittest

from m8.api.project import M8Project, SCALE_OFFSET
from m8.api.scale import (
    M8Scale, M8Scales,
    SCALE_BYTES, SCALE_COUNT, SCALE_NOTE_COUNT,
)


class TestM8ScaleLayout(unittest.TestCase):
    def test_block_size_is_46(self):
        self.assertEqual(SCALE_BYTES, 46)
        self.assertEqual(M8Scale.BYTES, 46)
        self.assertEqual(len(M8Scale().write()), 46)

    def test_default_all_notes_enabled(self):
        s = M8Scale()
        # Default bitmap is 0x0FFF — all 12 notes enabled (matches the
        # CHROMATIC default in the template).
        self.assertEqual(s.enabled_bitmap, 0x0FFF)
        for i in range(SCALE_NOTE_COUNT):
            self.assertTrue(s.is_note_enabled(i))


class TestM8ScaleEnabledBitmap(unittest.TestCase):
    def test_set_individual_notes(self):
        s = M8Scale()
        s.enabled_bitmap = 0  # disable all
        self.assertFalse(s.is_note_enabled(0))
        s.set_note_enabled(0, True)
        s.set_note_enabled(4, True)
        s.set_note_enabled(7, True)
        self.assertTrue(s.is_note_enabled(0))
        self.assertFalse(s.is_note_enabled(1))
        self.assertTrue(s.is_note_enabled(4))
        self.assertTrue(s.is_note_enabled(7))

    def test_bitmap_low_byte_is_first(self):
        """u16 little-endian: low byte at offset 0."""
        s = M8Scale()
        s.enabled_bitmap = 0x0FFF
        data = s.write()
        self.assertEqual(data[0], 0xFF)
        self.assertEqual(data[1], 0x0F)

    def test_note_index_out_of_range(self):
        s = M8Scale()
        with self.assertRaises(IndexError):
            s.is_note_enabled(12)
        with self.assertRaises(IndexError):
            s.set_note_enabled(-1, True)


class TestM8ScaleNoteOffsets(unittest.TestCase):
    def test_default_offsets_zero(self):
        s = M8Scale()
        for i in range(SCALE_NOTE_COUNT):
            self.assertEqual(s.get_note_offset(i), (0, 0))

    def test_set_offset(self):
        s = M8Scale()
        s.set_note_offset(0, semitones=2, cents=50)
        self.assertEqual(s.get_note_offset(0), (2, 50))

    def test_offset_byte_layout(self):
        """Per-note pair: byte 2+2i = semitones, byte 3+2i = cents."""
        s = M8Scale()
        s.set_note_offset(3, semitones=0x42, cents=0x99)
        data = s.write()
        self.assertEqual(data[2 + 3 * 2], 0x42)
        self.assertEqual(data[2 + 3 * 2 + 1], 0x99)


class TestM8ScaleName(unittest.TestCase):
    def test_default_name_empty(self):
        s = M8Scale()
        self.assertEqual(s.name, "")

    def test_set_and_get(self):
        s = M8Scale(name="MAJOR")
        self.assertEqual(s.name, "MAJOR")

    def test_name_at_byte_26(self):
        s = M8Scale(name="ABC")
        data = s.write()
        self.assertEqual(bytes(data[26:29]), b"ABC")


class TestM8ScaleRoundTrip(unittest.TestCase):
    def test_binary(self):
        s = M8Scale(name="PENTATONIC")
        s.enabled_bitmap = 0
        s.set_note_enabled(0, True)
        s.set_note_enabled(2, True)
        s.set_note_offset(2, semitones=2, cents=15)

        loaded = M8Scale.read(s.write())
        self.assertEqual(loaded.name, "PENTATONIC")
        self.assertTrue(loaded.is_note_enabled(0))
        self.assertTrue(loaded.is_note_enabled(2))
        self.assertFalse(loaded.is_note_enabled(1))
        self.assertEqual(loaded.get_note_offset(2), (2, 15))

    def test_dict(self):
        s = M8Scale(name="MICRO")
        s.set_note_enabled(0, True)
        s.set_note_offset(0, semitones=1, cents=25)
        loaded = M8Scale.from_dict(s.to_dict())
        self.assertEqual(loaded.name, "MICRO")
        self.assertEqual(loaded.get_note_offset(0), (1, 25))

    def test_clone(self):
        s = M8Scale(name="TEST")
        c = s.clone()
        c.name = "CHANGED"
        self.assertEqual(s.name, "TEST")


class TestM8Scales(unittest.TestCase):
    def test_collection_size(self):
        ss = M8Scales()
        self.assertEqual(len(ss), SCALE_COUNT)
        self.assertEqual(SCALE_COUNT, 16)

    def test_total_bytes(self):
        self.assertEqual(M8Scales.TOTAL_BYTES, 16 * 46)
        self.assertEqual(len(M8Scales().write()), 16 * 46)

    def test_round_trip_preserves_individual_scales(self):
        ss = M8Scales()
        ss[0].name = "FIRST"
        ss[15].name = "LAST"
        loaded = M8Scales.read(ss.write())
        self.assertEqual(loaded[0].name, "FIRST")
        self.assertEqual(loaded[15].name, "LAST")


class TestProjectIntegration(unittest.TestCase):
    def test_template_first_scale_is_chromatic(self):
        """The bundled v6.2 template ships with scale 0 = CHROMATIC,
        all 12 notes enabled, zero offsets."""
        p = M8Project.initialise()
        self.assertEqual(p.scales[0].name, "CHROMATIC")
        # Bitmap should have all 12 low bits set
        self.assertEqual(p.scales[0].enabled_bitmap & 0x0FFF, 0x0FFF)

    def test_at_expected_offset(self):
        p = M8Project.initialise()
        p.scales[0].name = "ZZ"
        data = p.write()
        # Name starts at scale-byte 26, so first scale's name byte 0
        # lands at SCALE_OFFSET + 26.
        self.assertEqual(data[SCALE_OFFSET + 26], ord("Z"))

    def test_round_trip_through_project(self):
        p = M8Project.initialise()
        p.scales[3].name = "TEST"
        p.scales[3].set_note_offset(5, semitones=4, cents=99)
        loaded = M8Project.read(p.write())
        self.assertEqual(loaded.scales[3].name, "TEST")
        self.assertEqual(loaded.scales[3].get_note_offset(5), (4, 99))

    def test_stable_round_trip(self):
        p = M8Project.initialise()
        p.scales[5].name = "X"
        b1 = p.write()
        b2 = M8Project.read(b1).write()
        self.assertEqual(b1, b2)


if __name__ == "__main__":
    unittest.main()
