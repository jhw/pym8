"""Tests for M8Wavsynth — instrument-specific coverage.

Cross-instrument behaviour (write/read round-trip, clone, to_dict/from_dict)
is covered by tests/api/instruments.py.
"""
import unittest

from m8.api.instruments.wavsynth import M8Wavsynth, M8WavShape, M8WavsynthModDest
from m8.api.instrument import M8InstrumentType


class TestM8Wavsynth(unittest.TestCase):
    def test_defaults(self):
        w = M8Wavsynth()
        self.assertEqual(w.type_id, int(M8InstrumentType.WAVSYNTH))
        self.assertEqual(w.fine_tune, 0x80)
        self.assertEqual(w.size, 0x20)
        self.assertEqual(w.cutoff, 0xFF)
        self.assertEqual(w.pan, 0x80)
        self.assertEqual(w.dry, 0xC0)

    def test_field_access(self):
        w = M8Wavsynth(name="LEAD")
        self.assertEqual(w.name, "LEAD")

        # Plain int assignment
        w.cutoff = 0x40
        self.assertEqual(w.cutoff, 0x40)

        # Enum assignment, integer read-back
        w.shape = M8WavShape.SAW
        self.assertEqual(w.shape, int(M8WavShape.SAW))

    def test_range_validation(self):
        w = M8Wavsynth()
        with self.assertRaises(ValueError):
            w.cutoff = 256
        with self.assertRaises(ValueError):
            w.cutoff = -1

    def test_mod_dest_enum(self):
        self.assertEqual(M8WavsynthModDest.CUTOFF, 0x07)
        self.assertEqual(M8Wavsynth.MOD_DEST_ENUM_CLASS, M8WavsynthModDest)


if __name__ == "__main__":
    unittest.main()
