"""Tests for the descriptor field framework underlying instruments."""
import unittest
from enum import IntEnum

from m8.api.fields import ByteField, BytesField, StringField, iter_fields


class Mode(IntEnum):
    A = 1
    B = 2


class Sample:
    """Test harness — small object that uses ByteField/StringField/BytesField."""

    cutoff = ByteField(0, default=0xFF)
    mode = ByteField(1, enum=Mode, default=Mode.A)
    bounded = ByteField(2, min=10, max=20, default=15)
    name = StringField(3, length=8, default="default")
    raw = BytesField(11, length=4, default=[1, 2, 3, 4])

    def __init__(self):
        self._data = bytearray(64)
        for _, fld in iter_fields(type(self)):
            fld.apply_default(self)


class TestByteField(unittest.TestCase):
    def test_default_applied(self):
        s = Sample()
        self.assertEqual(s.cutoff, 0xFF)

    def test_set_and_get_int(self):
        s = Sample()
        s.cutoff = 0x40
        self.assertEqual(s.cutoff, 0x40)

    def test_accepts_enum(self):
        s = Sample()
        s.mode = Mode.B
        self.assertEqual(s.mode, int(Mode.B))

    def test_range_low(self):
        s = Sample()
        with self.assertRaises(ValueError):
            s.bounded = 5

    def test_range_high(self):
        s = Sample()
        with self.assertRaises(ValueError):
            s.bounded = 99

    def test_byte_range_default(self):
        s = Sample()
        with self.assertRaises(ValueError):
            s.cutoff = 256
        with self.assertRaises(ValueError):
            s.cutoff = -1

    def test_dict_round_trip_with_enum(self):
        s = Sample()
        s.mode = Mode.B
        fld = type(s).__dict__["mode"]
        self.assertEqual(fld.to_dict(s), "B")
        # And round-trip via name
        s2 = Sample()
        fld.from_dict(s2, "A")
        self.assertEqual(s2.mode, int(Mode.A))

    def test_dict_round_trip_with_int(self):
        s = Sample()
        s.cutoff = 0x33
        fld = type(s).__dict__["cutoff"]
        self.assertEqual(fld.to_dict(s), 0x33)


class TestStringField(unittest.TestCase):
    def test_default_applied(self):
        s = Sample()
        self.assertEqual(s.name, "default")

    def test_set_and_get(self):
        s = Sample()
        s.name = "kick"
        self.assertEqual(s.name, "kick")

    def test_truncation(self):
        s = Sample()
        s.name = "this_is_too_long"
        self.assertEqual(len(s._data[3:11]), 8)
        # _read_fixed_string trims at null or 0xFF, but the underlying
        # 8-byte slot is fully utilized
        self.assertTrue(s.name.startswith("this_is"))


class TestBytesField(unittest.TestCase):
    def test_default_applied(self):
        s = Sample()
        self.assertEqual(s.raw, [1, 2, 3, 4])

    def test_set_and_get(self):
        s = Sample()
        s.raw = [10, 20, 30, 40]
        self.assertEqual(s.raw, [10, 20, 30, 40])
        # Confirms writes go through to _data
        self.assertEqual(list(s._data[11:15]), [10, 20, 30, 40])

    def test_wrong_length_rejected(self):
        s = Sample()
        with self.assertRaises(ValueError):
            s.raw = [1, 2, 3]
        with self.assertRaises(ValueError):
            s.raw = [1, 2, 3, 4, 5]

    def test_bytes_are_masked_to_unsigned_byte(self):
        s = Sample()
        s.raw = [0x100 | 0xAB, -1 & 0xFF, 0, 0]
        # int(0x1AB) & 0xFF == 0xAB; int(-1) & 0xFF == 0xFF
        self.assertEqual(s._data[11], 0xAB)
        self.assertEqual(s._data[12], 0xFF)

    def test_dict_round_trip(self):
        s = Sample()
        s.raw = [7, 8, 9, 10]
        fld = type(s).__dict__["raw"]
        self.assertEqual(fld.to_dict(s), [7, 8, 9, 10])
        s2 = Sample()
        fld.from_dict(s2, [11, 12, 13, 14])
        self.assertEqual(s2.raw, [11, 12, 13, 14])

    def test_invalid_default_length_at_class_definition(self):
        with self.assertRaises(ValueError):
            BytesField(0, length=4, default=[1, 2])


class TestIterFields(unittest.TestCase):
    def test_yields_all_descriptors_in_declaration_order(self):
        names = [name for name, _ in iter_fields(Sample)]
        self.assertEqual(names, ["cutoff", "mode", "bounded", "name", "raw"])

    def test_subclass_overrides_base(self):
        class SubSample(Sample):
            cutoff = ByteField(0, default=0x10)

        s = SubSample()
        # Subclass descriptor takes precedence
        self.assertEqual(s.cutoff, 0x10)
        names = [name for name, _ in iter_fields(SubSample)]
        # Each name appears exactly once
        self.assertEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()
