import os
import tempfile
import unittest

from m8.api.eq import M8Eq, M8EqType, NO_EQ
from m8.api.fx import M8SequenceFX
from m8.api.instrument_file import M8InstrumentFile, EQ_OFFSET, FILE_BYTES
from m8.api.instruments.fmsynth import M8FMSynth
from m8.api.instruments.wavsynth import M8Wavsynth
from m8.api.modulator import M8ADSRModulator, M8AHDModulator, M8LFOModulator
from m8.api.table import M8Table
from m8.api.version import M8Version

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def _fixture(name):
    with open(os.path.join(FIXTURES, name), "rb") as f:
        return f.read()


class TestModernFile(unittest.TestCase):
    """METRONOME.m8i is firmware 6.0.1, shipped in the M8's System folder."""

    def setUp(self):
        self.data = _fixture("METRONOME.m8i")
        self.file = M8InstrumentFile.read(self.data)

    def test_instrument(self):
        inst = self.file.instrument
        self.assertIsInstance(inst, M8FMSynth)
        self.assertEqual(inst.name, "METRONOME")
        self.assertEqual(inst.version, (6, 0, 1))
        # Typed modulators at offset 63 — slot 0 is an ADSR, which the
        # pre-3.0 layout can't express.
        self.assertEqual(
            [type(m) for m in inst.modulators],
            [M8ADSRModulator, M8AHDModulator, M8LFOModulator, M8LFOModulator],
        )

    def test_table_and_no_eq(self):
        self.assertEqual(len(self.data), FILE_BYTES)
        self.assertIsInstance(self.file.table, M8Table)
        self.assertEqual(self.file.table.write(), self.data[229:357])
        self.assertIsNone(self.file.eq)

    def test_round_trip(self):
        self.assertEqual(self.file.write(), self.data)


class TestFileWithEq(unittest.TestCase):
    def setUp(self):
        eq = M8Eq()
        eq.mid.eq_type = M8EqType.BELL
        eq.mid.level = 0x03
        self.eq_bytes = eq.write()
        self.data = _fixture("METRONOME.m8i") + self.eq_bytes

    def test_reads_eq(self):
        f = M8InstrumentFile.read(self.data)
        self.assertIsNotNone(f.eq)
        self.assertEqual(f.eq.write(), self.eq_bytes)
        self.assertEqual(f.eq.mid.eq_type, M8EqType.BELL)
        self.assertEqual(f.eq.mid.level, 0x03)

    def test_round_trip(self):
        self.assertEqual(M8InstrumentFile.read(self.data).write(), self.data)

    def test_dropping_eq_writes_short_file(self):
        f = M8InstrumentFile.read(self.data)
        f.eq = None
        self.assertEqual(len(f.write()), FILE_BYTES)

    def test_pre_4_0_ignores_eq_bytes(self):
        data = bytearray(self.data)
        data[10:14] = M8Version(3, 3, 0).write()
        self.assertIsNone(M8InstrumentFile.read(bytes(data)).eq)


class TestV2File(unittest.TestCase):
    """KICK_MORPH.m8i is firmware 2.7.0: untyped modulators at offset 61."""

    def setUp(self):
        self.file = M8InstrumentFile.read(_fixture("KICK_MORPH.m8i"))

    def test_modulators_converted(self):
        inst = self.file.instrument
        self.assertIsInstance(inst, M8FMSynth)
        self.assertEqual(
            [type(m) for m in inst.modulators],
            [M8AHDModulator, M8AHDModulator, M8LFOModulator, M8LFOModulator],
        )
        self.assertEqual(inst.modulators[0].destination, 1)
        self.assertEqual(inst.modulators[0].decay, 0x60)
        # Byte 62 is modulator data in this layout, not an EQ index.
        self.assertEqual(inst.associated_eq, NO_EQ)
        self.assertIsNone(self.file.eq)

    def test_write_refused(self):
        with self.assertRaises(ValueError):
            self.file.write()


class TestToDictAndRepr(unittest.TestCase):
    def test_to_dict_is_json_ready(self):
        import json
        f = M8InstrumentFile.read(_fixture("METRONOME.m8i"))
        d = json.loads(json.dumps(f.to_dict()))
        self.assertEqual(d["version"], "6.0.1")
        self.assertEqual(d["instrument"]["name"], "METRONOME")
        self.assertEqual(len(d["table"]), 16)
        self.assertIsNone(d["eq"])

    def test_repr(self):
        f = M8InstrumentFile.read(_fixture("METRONOME.m8i"))
        self.assertEqual(repr(f), "M8InstrumentFile(M8FMSynth 'METRONOME', firmware 6.0.1, table, no EQ)")


class TestNewFile(unittest.TestCase):
    def test_build_write_read(self):
        inst = M8Wavsynth(name="LEAD")
        table = M8Table()
        table[0].fx[0].key = int(M8SequenceFX.ARP)
        table[0].fx[0].value = 0x37
        f = M8InstrumentFile(inst, table=table, eq=M8Eq())

        data = f.write()
        self.assertEqual(data[:10], b"M8VERSION\x00")
        self.assertEqual(len(data), EQ_OFFSET + M8Eq.BYTES)

        back = M8InstrumentFile.read(data)
        self.assertIsInstance(back.instrument, M8Wavsynth)
        self.assertEqual(back.instrument.name, "LEAD")
        self.assertEqual(back.table[0].fx[0].value, 0x37)
        self.assertEqual(back.version, M8Version())

    def test_file_round_trip(self):
        f = M8InstrumentFile(M8Wavsynth(name="X"))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "sub", "X.m8i")
            f.write_to_file(path)
            self.assertEqual(M8InstrumentFile.read_from_file(path).write(), f.write())


class TestErrors(unittest.TestCase):
    def test_truncated_raises(self):
        with self.assertRaises(ValueError):
            M8InstrumentFile.read(b"\x00" * 10)

    def test_unknown_type_raises(self):
        data = bytearray(_fixture("METRONOME.m8i"))
        data[14] = 0x42
        with self.assertRaises(ValueError):
            M8InstrumentFile.read(bytes(data))


if __name__ == "__main__":
    unittest.main()
