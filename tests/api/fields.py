"""Tests for the descriptor field framework underlying instruments."""
import unittest
from enum import IntEnum

from m8.api.fields import (
    ByteField, BytesField, M8Record, StringField, index_ranges, iter_fields, repr_value,
)


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

    def test_terminates_at_first_0xff_only(self):
        """Matches m8-file-parser's Reader::read_string: stop at the FIRST
        0x00 or 0xFF, don't filter 0xFF bytes elsewhere in the field."""
        s = Sample()
        s._data[3:11] = b"AB\xFFCD\x00\x00\x00"
        self.assertEqual(s.name, "AB")

    def test_trailing_whitespace_preserved(self):
        """Rust's read_string doesn't strip whitespace; neither should we —
        stripping would silently change bytes that should round-trip."""
        s = Sample()
        s.name = "kick "
        self.assertEqual(s.name, "kick ")

    def test_invalid_utf8_backs_off_to_longest_valid_prefix(self):
        """Rust backs off byte-by-byte on invalid UTF-8 rather than
        replacing bad bytes with U+FFFD (which would re-encode to a
        different byte length on write and corrupt round-trip)."""
        s = Sample()
        s._data[3:11] = bytes([0x41, 0x42, 0x80, 0x41, 0x42, 0x43, 0x44, 0x45])
        self.assertEqual(s.name, "AB")

    def test_no_terminator_uses_full_length(self):
        s = Sample()
        s._data[3:11] = b"ABCDEFGH"
        self.assertEqual(s.name, "ABCDEFGH")


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



class Rec(M8Record):
    mode = ByteField(0, enum=Mode, default=Mode.A)
    level = ByteField(1, default=0x40)
    label = StringField(2, length=4, default="AB")

    def __init__(self):
        self._data = bytearray(6)
        for _, fld in iter_fields(type(self)):
            fld.apply_default(self)


class TestEnumReads(unittest.TestCase):
    def test_returns_member_when_known(self):
        s = Sample()
        s.mode = 2
        self.assertIs(s.mode, Mode.B)
        self.assertEqual(s.mode, 2)          # still an int

    def test_returns_int_when_unknown(self):
        s = Sample()
        s._data[1] = 0x7F
        self.assertEqual(s.mode, 0x7F)
        self.assertNotIsInstance(s.mode, Mode)

    def test_unbound_field_returns_int(self):
        self.assertIs(type(Sample().cutoff), int)


class TestM8Record(unittest.TestCase):
    def test_to_dict_names_enums(self):
        self.assertEqual(Rec().to_dict(), {"mode": "A", "level": 0x40, "label": "AB"})

    def test_from_dict_round_trip(self):
        r = Rec()
        r.mode, r.level, r.label = Mode.B, 0x11, "XY"
        back = Rec.from_dict(r.to_dict())
        self.assertEqual(back._data, r._data)

    def test_from_dict_ignores_unknown_keys(self):
        self.assertEqual(Rec.from_dict({"nope": 1}).level, 0x40)

    def test_repr(self):
        self.assertEqual(repr(Rec()), "Rec(mode=A, level=0x40, label='AB')")


class TestReprHelpers(unittest.TestCase):
    def test_repr_value(self):
        self.assertEqual(repr_value(Mode.B), "B")
        self.assertEqual(repr_value(10), "0x0A")
        self.assertEqual(repr_value(True), "True")
        self.assertEqual(repr_value("x"), "'x'")
        self.assertEqual(repr_value([1, Mode.A]), "[0x01, A]")

    def test_index_ranges(self):
        self.assertEqual(index_ranges([0, 1, 2, 5, 7, 8]), "0-2, 5, 7-8")
        self.assertEqual(index_ranges([]), "")

if __name__ == "__main__":
    unittest.main()
