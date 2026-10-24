"""Tests for M8Groove / M8Grooves."""
import os
import unittest

from m8.api.groove import (
    EMPTY_STEP, M8Groove, M8GroovePPQN, M8Grooves,
    GROOVE_BYTES, GROOVE_COUNT, GROOVE_STEPS,
)
from m8.api.project import GROOVE_OFFSET, GROOVE_PPQN_OFFSET, M8Project

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def _read_fixture(name):
    with open(os.path.join(FIXTURES_DIR, name), "rb") as f:
        return f.read()


class TestM8GrooveBasics(unittest.TestCase):
    def test_block_size(self):
        self.assertEqual(GROOVE_BYTES, 16)
        self.assertEqual(GROOVE_STEPS, 16)
        self.assertEqual(M8Groove.BYTES, 16)
        self.assertEqual(len(M8Groove().write()), 16)

    def test_default_is_all_empty(self):
        g = M8Groove()
        self.assertTrue(g.is_empty())
        self.assertEqual(g.active_steps(), [])

    def test_index_access(self):
        g = M8Groove()
        g[0] = 5
        g[3] = 10
        self.assertEqual(g[0], 5)
        self.assertEqual(g[3], 10)
        self.assertEqual(g[1], EMPTY_STEP)

    def test_out_of_range_raises(self):
        g = M8Groove()
        with self.assertRaises(IndexError):
            g[16]
        with self.assertRaises(IndexError):
            g[-1] = 0

    def test_active_steps_terminates_at_first_ff(self):
        g = M8Groove(steps=[5, 10, 15, 0xFF, 20, 25])
        # Active steps end at the first 0xFF
        self.assertEqual(g.active_steps(), [5, 10, 15])

    def test_active_steps_all_used(self):
        g = M8Groove(steps=[1] * 16)
        self.assertEqual(len(g.active_steps()), 16)


class TestM8GrooveRoundTrip(unittest.TestCase):
    def test_binary(self):
        g = M8Groove(steps=[2, 4, 6, 8])
        loaded = M8Groove.read(g.write())
        self.assertEqual(loaded[0], 2)
        self.assertEqual(loaded[3], 8)
        self.assertEqual(loaded[4], EMPTY_STEP)

    def test_dict(self):
        g = M8Groove(steps=[10, 20, 30])
        loaded = M8Groove.from_dict(g.to_dict())
        self.assertEqual(loaded[0], 10)
        self.assertEqual(loaded[2], 30)

    def test_clone_independent(self):
        g = M8Groove(steps=[1, 2, 3])
        c = g.clone()
        c[0] = 99
        self.assertEqual(g[0], 1)


class TestM8Grooves(unittest.TestCase):
    def test_default_count(self):
        gs = M8Grooves()
        self.assertEqual(len(gs), GROOVE_COUNT)
        self.assertEqual(GROOVE_COUNT, 32)

    def test_total_bytes(self):
        self.assertEqual(M8Grooves.TOTAL_BYTES, 32 * 16)
        self.assertEqual(len(M8Grooves().write()), 32 * 16)

    def test_round_trip_preserves_individual_grooves(self):
        gs = M8Grooves()
        gs[0][0] = 3
        gs[31][15] = 7
        loaded = M8Grooves.read(gs.write())
        self.assertEqual(loaded[0][0], 3)
        self.assertEqual(loaded[31][15], 7)


class TestM8GroovePPQN(unittest.TestCase):
    def test_default_is_24(self):
        g = M8Groove()
        self.assertEqual(g.ppqn, M8GroovePPQN.PPQN_24)
        self.assertEqual(g.active_ppqn(), 24)

    def test_active_ppqn_values(self):
        for value, ticks in [(M8GroovePPQN.PPQN_48, 48), (M8GroovePPQN.PPQN_96, 96),
                             (M8GroovePPQN.PPQN_192, 192)]:
            self.assertEqual(M8Groove(ppqn=value).active_ppqn(), ticks)

    def test_setter_rejects_unknown_value(self):
        with self.assertRaises(ValueError):
            M8Groove().ppqn = 4

    def test_unknown_raw_byte_reads_and_falls_back_to_24(self):
        """Matches Rust active_ppqn: anything unrecognised plays as 24."""
        g = M8Groove.read(bytes(GROOVE_BYTES), ppqn=9)
        self.assertEqual(g.ppqn, 9)
        self.assertEqual(g.active_ppqn(), 24)

    def test_dict_round_trip_by_name(self):
        g = M8Groove(steps=[6, 6], ppqn=M8GroovePPQN.PPQN_96)
        d = g.to_dict()
        self.assertEqual(d["ppqn"], "PPQN_96")
        self.assertEqual(M8Groove.from_dict(d).ppqn, M8GroovePPQN.PPQN_96)

    def test_clone_copies_ppqn(self):
        g = M8Groove(ppqn=M8GroovePPQN.PPQN_48)
        c = g.clone()
        c.ppqn = M8GroovePPQN.PPQN_192
        self.assertEqual(g.ppqn, M8GroovePPQN.PPQN_48)

    def test_collection_ppqn_block(self):
        grooves = M8Grooves.read(bytes(M8Grooves.TOTAL_BYTES), ppqn=bytes([3, 2, 1] + [0] * 29))
        self.assertEqual([g.ppqn for g in grooves[:4]], [3, 2, 1, 0])
        self.assertEqual(grooves.write_ppqn()[:4], bytes([3, 2, 1, 0]))
        self.assertEqual(len(grooves.write_ppqn()), M8Grooves.PPQN_BYTES)


class TestProjectIntegration(unittest.TestCase):
    def test_template_has_grooves(self):
        p = M8Project.initialise()
        self.assertIsInstance(p.grooves, M8Grooves)
        self.assertEqual(len(p.grooves), GROOVE_COUNT)

    def test_at_expected_offset(self):
        p = M8Project.initialise()
        p.grooves[0][0] = 0xAA
        data = p.write()
        self.assertEqual(data[GROOVE_OFFSET], 0xAA)

    def test_round_trip_through_project(self):
        p = M8Project.initialise()
        p.grooves[5][3] = 4
        p.grooves[31][0] = 8
        loaded = M8Project.read(p.write())
        self.assertEqual(loaded.grooves[5][3], 4)
        self.assertEqual(loaded.grooves[31][0], 8)

    def test_stable_round_trip(self):
        p = M8Project.initialise()
        p.grooves[10][0] = 2
        b1 = p.write()
        b2 = M8Project.read(b1).write()
        self.assertEqual(b1, b2)

    def test_reads_ppqn_from_device_file(self):
        """GRV.m8s (from m8-file-parser) sets grooves 0-3 to 24/48/192/96."""
        p = M8Project.read(_read_fixture("GRV.m8s"))
        self.assertEqual([g.active_ppqn() for g in p.grooves[:4]], [24, 48, 192, 96])
        self.assertEqual(p.grooves[1].active_steps()[:2], [28, 28])

    def test_ppqn_written_at_expected_offset(self):
        p = M8Project.initialise()
        p.grooves[3].ppqn = M8GroovePPQN.PPQN_192
        data = p.write()
        self.assertEqual(data[GROOVE_PPQN_OFFSET + 3], 3)
        self.assertEqual(M8Project.read(data).grooves[3].ppqn, M8GroovePPQN.PPQN_192)

    def test_pre_6_5_file_has_no_ppqn_block(self):
        """EXTERNAL.m8s ends at the EQs; PPQN reads as default and writing
        must not grow the file."""
        data = _read_fixture("EXTERNAL.m8s")
        p = M8Project.read(data)
        self.assertLess(p.version, (6, 5, 0))
        self.assertTrue(all(g.ppqn == M8GroovePPQN.PPQN_24 for g in p.grooves))
        p.grooves[0].ppqn = M8GroovePPQN.PPQN_48
        self.assertEqual(len(p.write()), len(data))

    def test_6_5_file_has_ppqn_block(self):
        data = _read_fixture("EMPTY65.m8s")
        p = M8Project.read(data)
        p.grooves[0].ppqn = M8GroovePPQN.PPQN_48
        out = p.write()
        self.assertEqual(len(out), len(data))
        self.assertEqual(out[GROOVE_PPQN_OFFSET], 1)


if __name__ == "__main__":
    unittest.main()
