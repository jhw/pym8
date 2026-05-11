"""Tests for the EQ data model.

Covers:
- M8EqBand: byte packing of type/mode, freq/gain decoding, round-trip
- M8Eq: 3-band container, defaults, round-trip
- M8Eqs: collection of 132 EQs, dict round-trip, default state
- Project integration: M8Project reads/writes the EQ region at the right
  offset and stable-round-trips
- Per-instrument: `associated_eq` byte 62 on every instrument class
"""
import unittest

from m8.api.eq import (
    EQ_BAND_BYTES, EQ_BYTES, EQ_COUNT,
    M8Eq, M8EqBand, M8EqMode, M8EqType, M8Eqs,
)
from m8.api.instruments.wavsynth import M8Wavsynth
from m8.api.instruments.hypersynth import M8HyperSynth
from m8.api.project import EQ_OFFSET, M8Project


class TestM8EqBand(unittest.TestCase):
    def test_default_band(self):
        band = M8EqBand()
        self.assertEqual(band.mode_byte, 0)
        self.assertEqual(band.freq, 0)
        self.assertEqual(band.q, 0)

    def test_eq_type_packed_in_low_3_bits(self):
        band = M8EqBand()
        band.eq_type = M8EqType.HISHELF  # = 4
        self.assertEqual(band.mode_byte & 0x07, 4)
        self.assertEqual(band.eq_type, 4)

    def test_eq_mode_packed_in_bits_5_7(self):
        band = M8EqBand()
        band.eq_mode = M8EqMode.RIGHT  # = 4
        self.assertEqual((band.mode_byte >> 5) & 0x07, 4)
        self.assertEqual(band.eq_mode, 4)

    def test_type_and_mode_independent(self):
        band = M8EqBand()
        band.eq_type = M8EqType.BELL
        band.eq_mode = M8EqMode.MID
        self.assertEqual(band.eq_type, int(M8EqType.BELL))
        self.assertEqual(band.eq_mode, int(M8EqMode.MID))
        # Underlying byte holds both
        self.assertEqual(band.mode_byte, int(M8EqType.BELL) | (int(M8EqMode.MID) << 5))

    def test_setting_type_preserves_mode_bits(self):
        band = M8EqBand()
        band.eq_mode = M8EqMode.LEFT
        band.eq_type = M8EqType.LOWCUT
        self.assertEqual(band.eq_mode, int(M8EqMode.LEFT))
        self.assertEqual(band.eq_type, int(M8EqType.LOWCUT))

    def test_frequency_combines_freq_high_low(self):
        band = M8EqBand()
        band.freq = 0x03
        band.freq_fin = 0xE8
        self.assertEqual(band.frequency(), 1000)

    def test_gain_is_signed_centi_db(self):
        band = M8EqBand()
        band.level = 0x00
        band.level_fin = 0x64  # 100 / 100 = +1.00 dB
        self.assertAlmostEqual(band.gain_db(), 1.00)

        # Negative gain (two's complement)
        band.level = 0xFF
        band.level_fin = 0x9C  # 0xFF9C = -100 as signed16 / 100 = -1.00 dB
        self.assertAlmostEqual(band.gain_db(), -1.00)

    def test_binary_round_trip(self):
        band = M8EqBand()
        band.eq_type = M8EqType.BANDPASS
        band.eq_mode = M8EqMode.SIDE
        band.freq, band.freq_fin = 0x08, 0x00
        band.level, band.level_fin = 0x00, 0xC8
        band.q = 0x40

        loaded = M8EqBand.read(band.write())
        self.assertEqual(loaded, band)
        self.assertEqual(loaded.eq_type, int(M8EqType.BANDPASS))
        self.assertEqual(loaded.eq_mode, int(M8EqMode.SIDE))

    def test_dict_round_trip_uses_names(self):
        band = M8EqBand()
        band.eq_type = M8EqType.ALLPASS
        band.eq_mode = M8EqMode.STEREO
        d = band.to_dict()
        self.assertEqual(d["eq_type"], "ALLPASS")
        self.assertEqual(d["eq_mode"], "STEREO")
        reloaded = M8EqBand.from_dict(d)
        self.assertEqual(reloaded, band)

    def test_size_is_six_bytes(self):
        self.assertEqual(len(M8EqBand().write()), EQ_BAND_BYTES)
        self.assertEqual(M8EqBand.BYTES, 6)


class TestM8Eq(unittest.TestCase):
    def test_default_eq_has_three_bands(self):
        eq = M8Eq()
        self.assertIsInstance(eq.low, M8EqBand)
        self.assertIsInstance(eq.mid, M8EqBand)
        self.assertIsInstance(eq.high, M8EqBand)

    def test_default_band_types_match_spec(self):
        """Rust EqBand::default_low/mid/high — LowShelf @ 100Hz, Bell @ 1kHz,
        HiShelf @ 5kHz, all Stereo, Q=50."""
        eq = M8Eq()
        self.assertEqual(eq.low.eq_type, int(M8EqType.LOWSHELF))
        self.assertEqual(eq.low.frequency(), 100)
        self.assertEqual(eq.low.q, 50)

        self.assertEqual(eq.mid.eq_type, int(M8EqType.BELL))
        self.assertEqual(eq.mid.frequency(), 1000)

        self.assertEqual(eq.high.eq_type, int(M8EqType.HISHELF))
        self.assertEqual(eq.high.frequency(), 5000)

    def test_size_is_eighteen_bytes(self):
        self.assertEqual(len(M8Eq().write()), EQ_BYTES)
        self.assertEqual(M8Eq.BYTES, 18)

    def test_binary_round_trip(self):
        eq = M8Eq()
        eq.low.q = 0x99
        eq.mid.level = 0x05
        eq.high.eq_mode = M8EqMode.LEFT

        loaded = M8Eq.read(eq.write())
        self.assertEqual(loaded.low.q, 0x99)
        self.assertEqual(loaded.mid.level, 0x05)
        self.assertEqual(loaded.high.eq_mode, int(M8EqMode.LEFT))

    def test_dict_round_trip(self):
        eq = M8Eq()
        eq.low.eq_type = M8EqType.LOWCUT
        eq.mid.q = 0x77
        reloaded = M8Eq.from_dict(eq.to_dict())
        self.assertEqual(reloaded, eq)

    def test_is_default_after_construction(self):
        self.assertTrue(M8Eq().is_default())

    def test_is_default_false_after_mutation(self):
        eq = M8Eq()
        eq.low.q = 99
        self.assertFalse(eq.is_default())


class TestM8Eqs(unittest.TestCase):
    def test_collection_size(self):
        eqs = M8Eqs()
        self.assertEqual(len(eqs), EQ_COUNT)
        self.assertEqual(EQ_COUNT, 132)

    def test_total_bytes_matches_v6_layout(self):
        self.assertEqual(M8Eqs.TOTAL_BYTES, 132 * 18)
        self.assertEqual(len(M8Eqs().write()), 132 * 18)

    def test_binary_round_trip_preserves_individual_eqs(self):
        eqs = M8Eqs()
        eqs[0].low.q = 0x11
        eqs[131].high.level = 0x22

        reloaded = M8Eqs.read(eqs.write())
        self.assertEqual(reloaded[0].low.q, 0x11)
        self.assertEqual(reloaded[131].high.level, 0x22)

    def test_dict_round_trip(self):
        eqs = M8Eqs()
        eqs[5].mid.eq_type = M8EqType.HISHELF
        reloaded = M8Eqs.from_dict(eqs.to_dict())
        self.assertEqual(len(reloaded), EQ_COUNT)
        self.assertEqual(reloaded[5].mid.eq_type, int(M8EqType.HISHELF))


class TestEqWiredIntoProject(unittest.TestCase):
    def test_template_has_eq_collection(self):
        p = M8Project.initialise()
        self.assertIsInstance(p.eq, M8Eqs)
        self.assertEqual(len(p.eq), EQ_COUNT)

    def test_eq_mutations_round_trip_through_binary(self):
        p = M8Project.initialise()
        p.eq[0].low.q = 0x42
        p.eq[10].mid.eq_type = M8EqType.BANDPASS

        loaded = M8Project.read(p.write())
        self.assertEqual(loaded.eq[0].low.q, 0x42)
        self.assertEqual(loaded.eq[10].mid.eq_type, int(M8EqType.BANDPASS))

    def test_eq_at_expected_byte_offset(self):
        """Sanity: EQ region starts at the documented offset."""
        p = M8Project.initialise()
        # Stamp a recognizable byte at the first EQ position
        p.eq[0].low.mode_byte = 0xA5
        data = p.write()
        self.assertEqual(data[EQ_OFFSET], 0xA5)

    def test_stable_round_trip_with_eq_mutations(self):
        p = M8Project.initialise()
        p.eq[3].high.q = 0x33
        bytes1 = p.write()
        bytes2 = M8Project.read(bytes1).write()
        self.assertEqual(bytes1, bytes2)

    def test_clone_preserves_eq_independence(self):
        p = M8Project.initialise()
        p.eq[0].low.q = 0x10
        cloned = p.clone()
        self.assertIsNot(cloned.eq, p.eq)
        self.assertIsNot(cloned.eq[0], p.eq[0])
        cloned.eq[0].low.q = 0xFF
        self.assertEqual(p.eq[0].low.q, 0x10)


class TestAssociatedEqOnInstrument(unittest.TestCase):
    """Every instrument has a byte at offset 62 binding it to a project EQ."""

    def test_default_is_unassigned(self):
        """0xFF = no EQ bound; matches Rust's pre-v5 default."""
        self.assertEqual(M8Wavsynth().associated_eq, 0xFF)
        self.assertEqual(M8HyperSynth().associated_eq, 0xFF)

    def test_set_round_trips(self):
        for cls in (M8Wavsynth, M8HyperSynth):
            with self.subTest(cls=cls.__name__):
                src = cls()
                src.associated_eq = 0x07
                reloaded = cls.read(src.write())
                self.assertEqual(reloaded.associated_eq, 0x07)

    def test_at_byte_62_in_block(self):
        """The Rust spec puts associated_eq at the byte just before
        modulators (offset 63), i.e. byte 62 of the instrument block."""
        w = M8Wavsynth()
        w.associated_eq = 0xAB
        data = w.write()
        self.assertEqual(data[62], 0xAB)

    def test_survives_project_round_trip(self):
        """End-to-end: setting associated_eq survives M8Project.read/write."""
        p = M8Project.initialise()
        w = M8Wavsynth(name="EQBOUND")
        w.associated_eq = 0x05
        p.instruments[0] = w

        loaded = M8Project.read(p.write())
        self.assertEqual(loaded.instruments[0].associated_eq, 0x05)


if __name__ == "__main__":
    unittest.main()
