"""Tests for M8Groove / M8Grooves."""
import unittest

from m8.api.groove import (
    EMPTY_STEP, M8Groove, M8Grooves,
    GROOVE_BYTES, GROOVE_COUNT, GROOVE_STEPS,
)
from m8.api.project import GROOVE_OFFSET, M8Project


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


if __name__ == "__main__":
    unittest.main()
