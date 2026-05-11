"""Tests for M8 modulators (descriptor-based subclasses).

Each modulator type is a distinct class with descriptor-based parameters.
Changing the type of a modulator slot means replacing it.
"""
import unittest

from m8.api.modulator import (
    M8Modulator, M8Modulators,
    M8AHDModulator, M8ADSRModulator, M8DrumModulator,
    M8LFOModulator, M8TrigModulator, M8TrackingModulator,
    M8ModulatorType, M8LFOShape, M8LFOTriggerMode,
)


# (class, type_enum, sample_field_mutations). One row per modulator type.
MODULATOR_CASES = [
    (M8AHDModulator, M8ModulatorType.AHD_ENVELOPE, [
        ("attack", 0x10), ("hold", 0x20), ("decay", 0x40),
    ]),
    (M8ADSRModulator, M8ModulatorType.ADSR_ENVELOPE, [
        ("attack", 0x10), ("decay", 0x20), ("sustain", 0x80), ("release", 0x30),
    ]),
    (M8DrumModulator, M8ModulatorType.DRUM_ENVELOPE, [
        ("peak", 0x40), ("body", 0x80), ("decay", 0x60),
    ]),
    (M8LFOModulator, M8ModulatorType.LFO, [
        ("shape", M8LFOShape.SIN),
        ("trigger_mode", M8LFOTriggerMode.RETRIG),
        ("freq", 0x25),
    ]),
    (M8TrigModulator, M8ModulatorType.TRIG_ENVELOPE, [
        ("attack", 0x10), ("hold", 0x20), ("decay", 0x30), ("src", 0x40),
    ]),
    (M8TrackingModulator, M8ModulatorType.TRACKING_ENVELOPE, [
        ("src", 0x05), ("lval", 0x10), ("hval", 0xF0),
    ]),
]


class TestEveryModulatorType(unittest.TestCase):
    """One-shot cross-cutting checks for every modulator subclass."""

    def _apply(self, mod, muts):
        for attr, value in muts:
            setattr(mod, attr, value)

    def _check(self, mod, muts):
        for attr, value in muts:
            self.assertEqual(getattr(mod, attr), int(value),
                             f"{type(mod).__name__}.{attr}")

    def test_mod_type_byte(self):
        for cls, mod_type, _ in MODULATOR_CASES:
            with self.subTest(cls=cls.__name__):
                mod = cls()
                self.assertEqual(mod.mod_type, int(mod_type))

    def test_amount_default(self):
        for cls, _, _ in MODULATOR_CASES:
            with self.subTest(cls=cls.__name__):
                self.assertEqual(cls().amount, 0xFF)

    def test_binary_round_trip(self):
        for cls, _, muts in MODULATOR_CASES:
            with self.subTest(cls=cls.__name__):
                src = cls()
                src.destination = 5
                src.amount = 0xA0
                self._apply(src, muts)
                round_tripped = cls.read(src.write())
                self.assertEqual(round_tripped.destination, 5)
                self.assertEqual(round_tripped.amount, 0xA0)
                self._check(round_tripped, muts)

    def test_clone(self):
        for cls, _, muts in MODULATOR_CASES:
            with self.subTest(cls=cls.__name__):
                src = cls()
                self._apply(src, muts)
                cloned = src.clone()
                self.assertIsNot(cloned, src)
                self._check(cloned, muts)

    def test_dict_round_trip(self):
        for cls, mod_type, muts in MODULATOR_CASES:
            with self.subTest(cls=cls.__name__):
                src = cls()
                src.destination = 3
                self._apply(src, muts)
                params = src.to_dict()
                self.assertEqual(params["type"], mod_type.name)
                reloaded = cls.from_dict(params)
                self.assertEqual(reloaded.destination, 3)
                self._check(reloaded, muts)

    def test_factory_dispatch(self):
        """M8Modulator.from_dict(...) dispatches to the right subclass."""
        for cls, _, muts in MODULATOR_CASES:
            with self.subTest(cls=cls.__name__):
                src = cls()
                self._apply(src, muts)
                reloaded = M8Modulator.from_dict(src.to_dict())
                self.assertIsInstance(reloaded, cls)


class TestTypeDestinationNibblePacking(unittest.TestCase):
    def test_byte_zero_layout(self):
        """High nibble = type, low nibble = destination."""
        lfo = M8LFOModulator()
        lfo.destination = 5
        self.assertEqual(lfo._data[0], 0x35)  # type=3 LFO, dest=5

        ahd = M8AHDModulator()
        ahd.destination = 7
        self.assertEqual(ahd._data[0], 0x07)  # type=0 AHD, dest=7


class TestEnumSerialization(unittest.TestCase):
    def test_lfo_shape_uses_names(self):
        mod = M8LFOModulator()
        mod.shape = M8LFOShape.RANDOM
        mod.trigger_mode = M8LFOTriggerMode.ONCE
        result = mod.to_dict()
        self.assertEqual(result["params"]["shape"], "RANDOM")
        self.assertEqual(result["params"]["trigger_mode"], "ONCE")

    def test_destination_uses_dest_enum_class(self):
        from m8.api.instruments.wavsynth import M8WavsynthModDest
        mod = M8AHDModulator()
        mod.destination = int(M8WavsynthModDest.CUTOFF)
        result = mod.to_dict(dest_enum_class=M8WavsynthModDest)
        self.assertEqual(result["destination"], "CUTOFF")

    def test_from_dict_accepts_enum_name(self):
        params = {
            "type": "LFO",
            "destination": 5,
            "amount": 0x80,
            "params": {
                "shape": "EXP_UP",
                "trigger_mode": "ONCE",
                "freq": 0x18,
                "retrigger": 0,
            },
        }
        mod = M8Modulator.from_dict(params)
        self.assertIsInstance(mod, M8LFOModulator)
        self.assertEqual(mod.shape, int(M8LFOShape.EXP_UP))
        self.assertEqual(mod.trigger_mode, int(M8LFOTriggerMode.ONCE))

    def test_from_dict_accepts_int(self):
        """Forward-compat: integer values still work."""
        params = {
            "type": M8ModulatorType.LFO.value,
            "destination": 5,
            "amount": 0x80,
            "params": {
                "shape": int(M8LFOShape.RAMP_DOWN),
                "trigger_mode": int(M8LFOTriggerMode.HOLD),
                "freq": 0x25,
                "retrigger": 0,
            },
        }
        mod = M8Modulator.from_dict(params)
        self.assertIsInstance(mod, M8LFOModulator)
        self.assertEqual(mod.shape, int(M8LFOShape.RAMP_DOWN))


class TestM8Modulators(unittest.TestCase):
    def test_default_layout(self):
        """Default is [AHD, AHD, LFO, LFO]."""
        mods = M8Modulators()
        self.assertEqual(len(mods), 4)
        self.assertIsInstance(mods[0], M8AHDModulator)
        self.assertIsInstance(mods[1], M8AHDModulator)
        self.assertIsInstance(mods[2], M8LFOModulator)
        self.assertIsInstance(mods[3], M8LFOModulator)

    def test_binary_round_trip_preserves_types(self):
        mods = M8Modulators()
        mods[0].destination = 1
        mods[0].attack = 0x20
        mods[2].destination = 5
        mods[2].freq = 0x30
        reloaded = M8Modulators.read(mods.write())
        self.assertIsInstance(reloaded[0], M8AHDModulator)
        self.assertIsInstance(reloaded[2], M8LFOModulator)
        self.assertEqual(reloaded[0].attack, 0x20)
        self.assertEqual(reloaded[2].freq, 0x30)

    def test_dict_round_trip(self):
        mods = M8Modulators()
        mods[0].destination = 1
        mods[0].attack = 0x20
        mods[2].shape = M8LFOShape.TRI
        reloaded = M8Modulators.from_dict(mods.to_dict())
        self.assertIsInstance(reloaded[0], M8AHDModulator)
        self.assertEqual(reloaded[0].attack, 0x20)
        self.assertIsInstance(reloaded[2], M8LFOModulator)
        self.assertEqual(reloaded[2].shape, int(M8LFOShape.TRI))

    def test_slot_replacement_changes_type(self):
        """Changing modulator type = replace the slot, not mutate."""
        mods = M8Modulators()
        # Replace slot 0 (AHD) with a Drum envelope
        mods[0] = M8DrumModulator(peak=0x80, body=0xA0, decay=0x40)
        self.assertIsInstance(mods[0], M8DrumModulator)
        self.assertEqual(mods[0].peak, 0x80)
        # Round-trip preserves the new type
        reloaded = M8Modulators.read(mods.write())
        self.assertIsInstance(reloaded[0], M8DrumModulator)
        self.assertEqual(reloaded[0].peak, 0x80)


class TestM8iConversion(unittest.TestCase):
    """M8i (single-instrument file) modulators have a different layout."""

    def test_ahd_in_m8i_slot_zero(self):
        # M8i AHD: dest, amt, atk, hold, dec, ?
        m8i_bytes = bytes([3, 0x80, 0x10, 0x20, 0x30, 0x00])
        # Pad to 4 slots worth
        full = m8i_bytes + bytes(18)
        mods = M8Modulators.read_m8i(full)
        self.assertIsInstance(mods[0], M8AHDModulator)
        self.assertEqual(mods[0].destination, 3)
        self.assertEqual(mods[0].amount, 0x80)
        self.assertEqual(mods[0].attack, 0x10)

    def test_lfo_in_m8i_slot_two_reorders_bytes(self):
        # M8i LFO: osc, dest, trig, freq, amt, retrig
        m8i_lfo = bytes([
            int(M8LFOShape.SIN),  # osc
            5,                     # dest
            0,                     # trig
            0x20,                  # freq
            0x90,                  # amt
            0,                     # retrig
        ])
        # Slot layout: AHD, AHD, LFO, LFO
        data = bytes(6) + bytes(6) + m8i_lfo + bytes(6)
        mods = M8Modulators.read_m8i(data)
        self.assertIsInstance(mods[2], M8LFOModulator)
        self.assertEqual(mods[2].destination, 5)
        self.assertEqual(mods[2].amount, 0x90)
        self.assertEqual(mods[2].shape, int(M8LFOShape.SIN))
        self.assertEqual(mods[2].freq, 0x20)


if __name__ == "__main__":
    unittest.main()
