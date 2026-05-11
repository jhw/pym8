"""Cross-cutting tests applied to every instrument type.

Per-instrument quirks live in tests/api/<instrument>.py. Each case in
INSTRUMENT_CASES contributes to write/read round-trip, clone, dict round-trip,
and factory-dispatch coverage.
"""
import os
import unittest

from m8.api import M8Block
from m8.api.instrument import (
    BLOCK_SIZE,
    M8Instrument,
    M8Instruments,
    M8InstrumentType,
)
from m8.api.instruments.external import M8External, M8ExternalPort
from m8.api.instruments.fmsynth import M8FMSynth, M8FMAlgo
from m8.api.instruments.hypersynth import M8HyperSynth
from m8.api.instruments.macrosynth import M8Macrosynth, M8MacroShape
from m8.api.instruments.midiout import M8MIDIOut, M8MIDIPort
from m8.api.instruments.sampler import M8Sampler, M8PlayMode
from m8.api.instruments.wavsynth import M8Wavsynth, M8WavShape


# (class, sample_mutations, default_checks). Mutations cover enum + numeric
# values; default_checks verify non-zero defaults survive construction.
INSTRUMENT_CASES = [
    (M8Wavsynth, [
        ("shape", M8WavShape.SAW),
        ("size", 0x40),
        ("cutoff", 0x20),
        ("resonance", 0xC0),
    ], [("fine_tune", 0x80), ("size", 0x20), ("cutoff", 0xFF), ("pan", 0x80), ("dry", 0xC0)]),

    (M8Macrosynth, [
        ("shape", M8MacroShape.PLUK),
        ("timbre", 0x40),
        ("colour", 0x60),
        ("cutoff", 0x80),
    ], [("fine_tune", 0x80), ("timbre", 0x80), ("colour", 0x80), ("cutoff", 0xFF), ("pan", 0x80), ("dry", 0xC0)]),

    (M8Sampler, [
        ("play_mode", M8PlayMode.FWDLOOP),
        ("start", 0x10),
        ("length", 0x80),
        ("cutoff", 0x40),
    ], [("fine_tune", 0x80), ("length", 0xFF), ("cutoff", 0xFF), ("pan", 0x80), ("dry", 0xC0)]),

    (M8FMSynth, [
        ("algo", M8FMAlgo.AB_C_D),
        ("op_a_level", 0x80),
        ("op_b_ratio", 0x02),
        ("cutoff", 0x60),
    ], [("fine_tune", 0x80), ("cutoff", 0xFF), ("pan", 0x80), ("dry", 0xC0)]),

    (M8External, [
        ("port", M8ExternalPort.MIDI),
        ("channel", 0x05),
        ("bank", 0x10),
        ("cutoff", 0x80),
    ], [("fine_tune", 0x80), ("bank", 0x7F), ("program", 0x7F), ("cca_num", 0x7F), ("cutoff", 0xFF), ("pan", 0x80), ("dry", 0xC0)]),

    (M8MIDIOut, [
        ("port", M8MIDIPort.MIDI),
        ("channel", 0x02),
        ("bank", 0x08),
        ("cca_num", 0x40),
    ], [("bank", 0x7F), ("program", 0x7F), ("cca_num", 0x7F), ("cca_val", 0x7F), ("ccj_num", 0x7F)]),

    (M8HyperSynth, [
        ("scale", 0x05),
        ("shift", 0x10),
        ("swarm", 0x80),
        ("width", 0x40),
        ("subosc", 0x20),
        ("cutoff", 0x60),
    ], [("fine_tune", 0x80), ("cutoff", 0xFF), ("pan", 0x80), ("dry", 0xC0)]),
]


class TestEveryInstrument(unittest.TestCase):
    """Each instrument type passes the same structural assertions."""

    def _apply(self, instance, mutations):
        for attr, value in mutations:
            setattr(instance, attr, value)

    def _check(self, instance, mutations):
        for attr, value in mutations:
            self.assertEqual(getattr(instance, attr), int(value), f"{type(instance).__name__}.{attr}")

    def test_construct_with_defaults(self):
        for cls, _, defaults in INSTRUMENT_CASES:
            with self.subTest(cls=cls.__name__):
                inst = cls()
                self.assertEqual(inst.type_id, int(cls.TYPE_ID))
                for attr, expected in defaults:
                    self.assertEqual(getattr(inst, attr), expected, f"{cls.__name__}.{attr}")

    def test_write_size_is_block_size(self):
        for cls, _, _ in INSTRUMENT_CASES:
            with self.subTest(cls=cls.__name__):
                self.assertEqual(len(cls().write()), BLOCK_SIZE)

    def test_binary_round_trip(self):
        for cls, muts, _ in INSTRUMENT_CASES:
            with self.subTest(cls=cls.__name__):
                src = cls(name="ROUND")
                self._apply(src, muts)
                round_tripped = cls.read(src.write())
                self.assertEqual(round_tripped.name, "ROUND")
                self._check(round_tripped, muts)
                self.assertEqual(len(round_tripped.modulators), 4)

    def test_clone(self):
        for cls, muts, _ in INSTRUMENT_CASES:
            with self.subTest(cls=cls.__name__):
                src = cls(name="C")
                self._apply(src, muts)
                clone = src.clone()
                self.assertIsNot(clone, src)
                self.assertIsNot(clone.modulators, src.modulators)
                self._check(clone, muts)

    def test_dict_round_trip(self):
        for cls, muts, _ in INSTRUMENT_CASES:
            with self.subTest(cls=cls.__name__):
                src = cls(name="DICT")
                self._apply(src, muts)
                params = src.to_dict()
                self.assertEqual(params["type"], cls.TYPE_ID.name)
                self.assertEqual(params["name"], "DICT")
                reloaded = cls.from_dict(params)
                self._check(reloaded, muts)
                self.assertEqual(reloaded.name, "DICT")

    def test_factory_dispatch(self):
        for cls, muts, _ in INSTRUMENT_CASES:
            with self.subTest(cls=cls.__name__):
                src = cls(name="FAC")
                self._apply(src, muts)
                reloaded = M8Instrument.from_dict(src.to_dict())
                self.assertIsInstance(reloaded, cls)
                self._check(reloaded, muts)

    def test_to_dict_uses_enum_names(self):
        w = M8Wavsynth()
        w.shape = M8WavShape.TRIANGLE
        params = w.to_dict()
        self.assertEqual(params["params"]["shape"], "TRIANGLE")


class TestM8Instruments(unittest.TestCase):
    def test_default_initialization(self):
        instruments = M8Instruments()
        self.assertEqual(len(instruments), 128)
        for inst in instruments:
            self.assertIsInstance(inst, M8Block)
            self.assertEqual(inst.data[0], 0xFF)

    def test_assign_into_slot(self):
        instruments = M8Instruments()
        instruments[3] = M8Wavsynth(name="W3")
        self.assertIsInstance(instruments[3], M8Wavsynth)
        self.assertEqual(instruments[3].name, "W3")

    def test_round_trip_via_binary(self):
        instruments = M8Instruments()
        instruments[0] = M8Wavsynth(name="A")
        instruments[5] = M8FMSynth(name="B")
        instruments[10] = M8MIDIOut(name="C")
        reloaded = M8Instruments.read(instruments.write())
        self.assertIsInstance(reloaded[0], M8Wavsynth)
        self.assertIsInstance(reloaded[5], M8FMSynth)
        self.assertIsInstance(reloaded[10], M8MIDIOut)
        self.assertEqual(reloaded[0].name, "A")
        self.assertEqual(reloaded[5].name, "B")
        self.assertEqual(reloaded[10].name, "C")

    def test_unknown_type_warns(self):
        """A type byte not registered to a subclass should warn and survive as M8Block."""
        instruments = M8Instruments()
        raw = bytearray(instruments.write())
        raw[0] = 0x7E
        with self.assertWarns(UserWarning):
            reloaded = M8Instruments.read(bytes(raw))
        self.assertIsInstance(reloaded[0], M8Block)


class TestM8iRoundTrip(unittest.TestCase):
    FIXTURE = os.path.join(
        os.path.dirname(__file__), "..", "fixtures", "KICK_MORPH.m8i"
    )

    def test_read_m8i_file(self):
        if not os.path.exists(self.FIXTURE):
            self.skipTest("KICK_MORPH.m8i fixture not present")
        inst = M8Instrument.read_from_file(self.FIXTURE)
        self.assertIsInstance(inst, M8FMSynth)
        self.assertEqual(len(inst.modulators), 4)


if __name__ == "__main__":
    unittest.main()
