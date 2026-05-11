"""Tests for M8Version, including the new ordered-comparison helpers."""
import unittest

from m8.api.version import M8Version


class TestM8Version(unittest.TestCase):
    def test_defaults(self):
        v = M8Version()
        self.assertEqual(v.major, 6)
        self.assertEqual(v.minor, 0)
        self.assertEqual(v.patch, 17)

    def test_binary_round_trip(self):
        # On-disk byte order is [patch, major, minor, 0]
        data = bytes([17, 6, 0, 0])
        v = M8Version.read(data)
        self.assertEqual(v.tuple(), (6, 0, 17))
        self.assertEqual(v.write(), data)

    def test_str(self):
        self.assertEqual(str(M8Version(4, 0, 33)), "4.0.33")

    def test_from_str(self):
        v = M8Version.from_str("4.1.0")
        self.assertEqual(v.tuple(), (4, 1, 0))

    def test_from_str_empty_returns_default(self):
        self.assertEqual(M8Version.from_str("").tuple(), (6, 0, 17))
        self.assertEqual(M8Version.from_str(None).tuple(), (6, 0, 17))
        self.assertEqual(M8Version.from_str("None").tuple(), (6, 0, 17))

    def test_comparison_with_tuple(self):
        v = M8Version(4, 1, 0)
        self.assertTrue(v >= (4, 0, 0))
        self.assertTrue(v < (5, 0, 0))
        self.assertTrue(v == (4, 1, 0))
        self.assertFalse(v == (4, 0, 0))

    def test_comparison_with_version(self):
        self.assertTrue(M8Version(6, 2, 1) > M8Version(6, 0, 17))
        self.assertTrue(M8Version(4, 0, 33) < M8Version(4, 1, 0))

    def test_eq_against_other_types(self):
        v = M8Version(4, 0, 0)
        self.assertFalse(v == "4.0.0")
        self.assertFalse(v == 4)

    def test_hashable(self):
        s = {M8Version(4, 0, 0), M8Version(4, 0, 0), M8Version(6, 2, 1)}
        self.assertEqual(len(s), 2)

    def test_compare_raises_for_invalid(self):
        with self.assertRaises(TypeError):
            M8Version() < "6.0.17"


if __name__ == "__main__":
    unittest.main()
