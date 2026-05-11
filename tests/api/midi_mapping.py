"""Tests for M8MidiMapping / M8MidiMappings."""
import unittest

from m8.api.midi_mapping import (
    M8MidiMapping, M8MidiMappings,
    MIDI_MAPPING_BYTES, MIDI_MAPPING_COUNT,
)
from m8.api.project import M8Project, MIDI_MAPPING_OFFSET


class TestM8MidiMappingLayout(unittest.TestCase):
    def test_block_size(self):
        self.assertEqual(MIDI_MAPPING_BYTES, 7)
        self.assertEqual(M8MidiMapping.BYTES, 7)
        self.assertEqual(len(M8MidiMapping().write()), 7)

    def test_field_offsets(self):
        m = M8MidiMapping(
            channel=0x11, control_number=0x22, value=0x33,
            typ=0x44, param_index=0x55, min_value=0x66, max_value=0x77,
        )
        self.assertEqual(m.write(), bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77]))


class TestM8MidiMapping(unittest.TestCase):
    def test_default_is_empty(self):
        """Default channel = 0 ⇒ is_empty() True (matches Rust convention)."""
        m = M8MidiMapping()
        self.assertEqual(m.channel, 0)
        self.assertTrue(m.is_empty())

    def test_set_channel_marks_used(self):
        m = M8MidiMapping(channel=1)
        self.assertFalse(m.is_empty())

    def test_binary_round_trip(self):
        m = M8MidiMapping(channel=2, control_number=71, value=64)
        loaded = M8MidiMapping.read(m.write())
        self.assertEqual(loaded.channel, 2)
        self.assertEqual(loaded.control_number, 71)
        self.assertEqual(loaded.value, 64)

    def test_dict_round_trip(self):
        m = M8MidiMapping(channel=5, control_number=80, min_value=20, max_value=100)
        loaded = M8MidiMapping.from_dict(m.to_dict())
        self.assertEqual(loaded.channel, 5)
        self.assertEqual(loaded.control_number, 80)
        self.assertEqual(loaded.min_value, 20)
        self.assertEqual(loaded.max_value, 100)

    def test_clone_independent(self):
        m = M8MidiMapping(channel=3)
        c = m.clone()
        c.channel = 9
        self.assertEqual(m.channel, 3)


class TestM8MidiMappings(unittest.TestCase):
    def test_default_count(self):
        ms = M8MidiMappings()
        self.assertEqual(len(ms), MIDI_MAPPING_COUNT)
        self.assertEqual(MIDI_MAPPING_COUNT, 128)

    def test_total_bytes(self):
        self.assertEqual(M8MidiMappings.TOTAL_BYTES, 128 * 7)
        self.assertEqual(len(M8MidiMappings().write()), 128 * 7)

    def test_round_trip_preserves_individual_mappings(self):
        ms = M8MidiMappings()
        ms[0].channel = 1
        ms[0].control_number = 71
        ms[127].channel = 16
        ms[127].max_value = 127
        loaded = M8MidiMappings.read(ms.write())
        self.assertEqual(loaded[0].channel, 1)
        self.assertEqual(loaded[0].control_number, 71)
        self.assertEqual(loaded[127].max_value, 127)


class TestProjectIntegration(unittest.TestCase):
    def test_template_has_midi_mappings(self):
        p = M8Project.initialise()
        self.assertIsInstance(p.midi_mappings, M8MidiMappings)
        self.assertEqual(len(p.midi_mappings), MIDI_MAPPING_COUNT)

    def test_at_expected_offset(self):
        p = M8Project.initialise()
        p.midi_mappings[0].channel = 0xCC
        data = p.write()
        self.assertEqual(data[MIDI_MAPPING_OFFSET], 0xCC)

    def test_round_trip_through_project(self):
        p = M8Project.initialise()
        p.midi_mappings[3].channel = 5
        p.midi_mappings[3].control_number = 74
        loaded = M8Project.read(p.write())
        self.assertEqual(loaded.midi_mappings[3].channel, 5)
        self.assertEqual(loaded.midi_mappings[3].control_number, 74)

    def test_stable_round_trip(self):
        p = M8Project.initialise()
        p.midi_mappings[10].channel = 7
        b1 = p.write()
        b2 = M8Project.read(b1).write()
        self.assertEqual(b1, b2)


if __name__ == "__main__":
    unittest.main()
