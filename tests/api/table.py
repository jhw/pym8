"""Tests for M8TableStep / M8Table / M8Tables.

Tables are 256 × 16-step modulation grids at file offset 0xBA3E. Each
step is 8 bytes: transpose + velocity + 3 × (FX key, FX value).
"""
import unittest

from m8.api.fx import M8FXTuple, M8SamplerFX, M8SequenceFX
from m8.api.project import M8Project
from m8.api.table import (
    EMPTY_VELOCITY, M8Table, M8TableStep, M8Tables,
    TABLE_BYTES, TABLE_COUNT, TABLE_OFFSET, TABLE_STEP_BYTES, TABLE_STEP_COUNT,
)


class TestM8TableStep(unittest.TestCase):
    def test_default_step_is_empty(self):
        step = M8TableStep()
        self.assertEqual(step.transpose, 0)
        self.assertEqual(step.velocity, EMPTY_VELOCITY)
        self.assertTrue(step.is_empty())

    def test_block_size(self):
        self.assertEqual(M8TableStep.BYTES, 8)
        self.assertEqual(TABLE_STEP_BYTES, 8)
        self.assertEqual(len(M8TableStep().write()), 8)

    def test_set_transpose_and_velocity(self):
        step = M8TableStep(transpose=0x0C, velocity=0x80)
        self.assertEqual(step.transpose, 0x0C)
        self.assertEqual(step.velocity, 0x80)
        self.assertFalse(step.is_empty())

    def test_byte_layout(self):
        """transpose at 0, velocity at 1, then 3 (key,value) pairs."""
        step = M8TableStep(transpose=0x42, velocity=0x80)
        step.fx[0] = M8FXTuple(key=0x11, value=0x22)
        step.fx[1] = M8FXTuple(key=0x33, value=0x44)
        step.fx[2] = M8FXTuple(key=0x55, value=0x66)
        data = step.write()
        self.assertEqual(data, bytes([0x42, 0x80, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66]))

    def test_binary_round_trip(self):
        step = M8TableStep(transpose=0x0C, velocity=0xA0)
        step.fx[0] = M8FXTuple(key=M8SequenceFX.ARP, value=0x03)
        step.fx[1] = M8FXTuple(key=M8SamplerFX.CUT, value=0x80)
        reloaded = M8TableStep.read(step.write())
        self.assertEqual(reloaded.transpose, 0x0C)
        self.assertEqual(reloaded.velocity, 0xA0)
        self.assertEqual(reloaded.fx[0].key, int(M8SequenceFX.ARP))
        self.assertEqual(reloaded.fx[0].value, 0x03)
        self.assertEqual(reloaded.fx[1].key, int(M8SamplerFX.CUT))

    def test_is_empty_default(self):
        self.assertTrue(M8TableStep().is_empty())

    def test_is_empty_false_when_transpose_set(self):
        step = M8TableStep(transpose=1)
        self.assertFalse(step.is_empty())

    def test_is_empty_false_when_fx_set(self):
        step = M8TableStep()
        step.fx[0] = M8FXTuple(key=M8SequenceFX.ARP, value=0)
        self.assertFalse(step.is_empty())

    def test_clone_independent(self):
        original = M8TableStep(transpose=5, velocity=0x80)
        original.fx[0] = M8FXTuple(key=0x10, value=0x20)
        cloned = original.clone()
        cloned.transpose = 99
        cloned.fx[0].value = 0xFF
        self.assertEqual(original.transpose, 5)
        self.assertEqual(original.fx[0].value, 0x20)

    def test_dict_round_trip(self):
        step = M8TableStep(transpose=0x0C, velocity=0xA0)
        step.fx[0] = M8FXTuple(key=0x05, value=0x44)
        reloaded = M8TableStep.from_dict(step.to_dict())
        self.assertEqual(reloaded.transpose, 0x0C)
        self.assertEqual(reloaded.velocity, 0xA0)
        self.assertEqual(reloaded.fx[0].key, 0x05)
        self.assertEqual(reloaded.fx[0].value, 0x44)


class TestM8Table(unittest.TestCase):
    def test_default_has_16_empty_steps(self):
        table = M8Table()
        self.assertEqual(len(table), TABLE_STEP_COUNT)
        self.assertEqual(TABLE_STEP_COUNT, 16)
        self.assertTrue(table.is_empty())

    def test_block_size(self):
        self.assertEqual(M8Table.BYTES, 128)
        self.assertEqual(TABLE_BYTES, 128)
        self.assertEqual(len(M8Table().write()), 128)

    def test_binary_round_trip(self):
        table = M8Table()
        table[0].transpose = 0x0C
        table[5].velocity = 0x70
        table[15].fx[0] = M8FXTuple(key=M8SequenceFX.RET, value=0x40)

        reloaded = M8Table.read(table.write())
        self.assertEqual(reloaded[0].transpose, 0x0C)
        self.assertEqual(reloaded[5].velocity, 0x70)
        self.assertEqual(reloaded[15].fx[0].key, int(M8SequenceFX.RET))

    def test_clone_independent(self):
        table = M8Table()
        table[3].transpose = 7
        cloned = table.clone()
        cloned[3].transpose = 99
        self.assertEqual(table[3].transpose, 7)

    def test_dict_round_trip(self):
        table = M8Table()
        table[2].transpose = 0x05
        table[2].fx[0] = M8FXTuple(key=0x42, value=0x99)
        reloaded = M8Table.from_dict(table.to_dict())
        self.assertEqual(reloaded[2].transpose, 0x05)
        self.assertEqual(reloaded[2].fx[0].key, 0x42)


class TestM8Tables(unittest.TestCase):
    def test_collection_size(self):
        tables = M8Tables()
        self.assertEqual(len(tables), TABLE_COUNT)
        self.assertEqual(TABLE_COUNT, 256)

    def test_total_bytes(self):
        # 256 tables × 128 bytes = 32 768 bytes (0x8000)
        self.assertEqual(M8Tables.TOTAL_BYTES, 256 * 128)
        self.assertEqual(M8Tables.TOTAL_BYTES, 0x8000)
        self.assertEqual(len(M8Tables().write()), 0x8000)

    def test_individual_tables_round_trip(self):
        tables = M8Tables()
        tables[0][0].transpose = 0x11
        tables[100][7].velocity = 0x22
        tables[255][15].fx[2] = M8FXTuple(key=0x88, value=0x99)

        reloaded = M8Tables.read(tables.write())
        self.assertEqual(reloaded[0][0].transpose, 0x11)
        self.assertEqual(reloaded[100][7].velocity, 0x22)
        self.assertEqual(reloaded[255][15].fx[2].key, 0x88)
        self.assertEqual(reloaded[255][15].fx[2].value, 0x99)


class TestProjectIntegration(unittest.TestCase):
    def test_template_has_tables_collection(self):
        p = M8Project.initialise()
        self.assertIsInstance(p.tables, M8Tables)
        self.assertEqual(len(p.tables), TABLE_COUNT)

    def test_tables_at_expected_offset(self):
        p = M8Project.initialise()
        p.tables[0][0].transpose = 0xCC
        data = p.write()
        # First byte of table region is table[0].steps[0].transpose
        self.assertEqual(data[TABLE_OFFSET], 0xCC)

    def test_mutations_round_trip(self):
        p = M8Project.initialise()
        p.tables[10][3].transpose = 0x0C
        p.tables[10][3].velocity = 0x80
        p.tables[10][3].fx[1] = M8FXTuple(key=M8SamplerFX.CUT, value=0xA0)

        loaded = M8Project.read(p.write())
        self.assertEqual(loaded.tables[10][3].transpose, 0x0C)
        self.assertEqual(loaded.tables[10][3].velocity, 0x80)
        self.assertEqual(loaded.tables[10][3].fx[1].key, int(M8SamplerFX.CUT))
        self.assertEqual(loaded.tables[10][3].fx[1].value, 0xA0)

    def test_stable_round_trip_with_mutations(self):
        p = M8Project.initialise()
        p.tables[42][8].transpose = 5
        p.tables[42][8].fx[0] = M8FXTuple(key=M8SequenceFX.HOP, value=0x08)
        bytes1 = p.write()
        bytes2 = M8Project.read(bytes1).write()
        self.assertEqual(bytes1, bytes2)

    def test_clone_preserves_tables_independence(self):
        p = M8Project.initialise()
        p.tables[5][0].transpose = 0x10
        cloned = p.clone()
        cloned.tables[5][0].transpose = 0xFF
        self.assertEqual(p.tables[5][0].transpose, 0x10)


if __name__ == "__main__":
    unittest.main()
