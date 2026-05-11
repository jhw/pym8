"""Macrosynth-specific tests. Cross-cutting behaviour lives in instruments.py."""
import unittest

from m8.api.instruments.macrosynth import (
    M8Macrosynth, M8MacroShape, M8MacrosynthModDest,
)


class TestM8MacrosynthSpecifics(unittest.TestCase):
    def test_braids_shape_enum(self):
        m = M8Macrosynth()
        m.shape = M8MacroShape.PLUK
        self.assertEqual(m.to_dict()["params"]["shape"], "PLUK")

    def test_mod_dest_class(self):
        self.assertEqual(M8Macrosynth.MOD_DEST_ENUM_CLASS, M8MacrosynthModDest)


if __name__ == "__main__":
    unittest.main()
