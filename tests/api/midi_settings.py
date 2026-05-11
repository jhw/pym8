"""Tests for M8MidiSettings (27 bytes at file offset 160) and the
project-level musical key byte at file offset 187.

Both used to be invisible to pym8 — the bytes lived in what M8Metadata
incorrectly modelled as part of its block (with `metadata.key` actually
pointing at MidiSettings.receive_sync). This commit untangles that and
puts each byte at its correct file position.
"""
import unittest

from m8.api.midi_settings import M8MidiSettings, MIDI_SETTINGS_BYTES, N_TRACKS
from m8.api.project import KEY_OFFSET, MIDI_SETTINGS_OFFSET, M8Project


class TestM8MidiSettingsLayout(unittest.TestCase):
    def test_block_size_is_27(self):
        self.assertEqual(MIDI_SETTINGS_BYTES, 27)
        self.assertEqual(M8MidiSettings.BYTES, 27)
        self.assertEqual(len(M8MidiSettings().write()), 27)

    def test_field_offsets_match_rust(self):
        m = M8MidiSettings(
            receive_sync=1,
            receive_transport=2,
            send_sync=1,
            send_transport=4,
            record_note_channel=5,
            record_note_velocity=1,
            record_note_delay_kill_commands=7,
            control_map_channel=8,
            song_row_cue_channel=9,
            track_input_program_change=1,
            track_input_mode=11,
        )
        data = m.write()
        self.assertEqual(data[0], 1)
        self.assertEqual(data[1], 2)
        self.assertEqual(data[2], 1)
        self.assertEqual(data[3], 4)
        self.assertEqual(data[4], 5)
        self.assertEqual(data[5], 1)
        self.assertEqual(data[6], 7)
        self.assertEqual(data[7], 8)
        self.assertEqual(data[8], 9)
        self.assertEqual(data[25], 1)
        self.assertEqual(data[26], 11)

    def test_track_input_channel_array_at_9_through_16(self):
        m = M8MidiSettings()
        for i in range(N_TRACKS):
            m.set_track_input_channel(i, 0x10 + i)
        data = m.write()
        for i in range(N_TRACKS):
            self.assertEqual(data[9 + i], 0x10 + i)

    def test_track_input_instrument_array_at_17_through_24(self):
        m = M8MidiSettings()
        for i in range(N_TRACKS):
            m.set_track_input_instrument(i, 0x20 + i)
        data = m.write()
        for i in range(N_TRACKS):
            self.assertEqual(data[17 + i], 0x20 + i)


class TestM8MidiSettingsAccessors(unittest.TestCase):
    def test_track_input_channel_round_trip(self):
        m = M8MidiSettings()
        m.set_track_input_channel(3, 5)
        self.assertEqual(m.track_input_channel(3), 5)
        # Other tracks unaffected
        self.assertEqual(m.track_input_channel(0), 0)

    def test_track_input_instrument_round_trip(self):
        m = M8MidiSettings()
        m.set_track_input_instrument(7, 42)
        self.assertEqual(m.track_input_instrument(7), 42)

    def test_track_index_out_of_range(self):
        m = M8MidiSettings()
        with self.assertRaises(IndexError):
            m.track_input_channel(8)
        with self.assertRaises(IndexError):
            m.set_track_input_instrument(-1, 0)


class TestM8MidiSettingsRoundTrip(unittest.TestCase):
    def test_binary(self):
        m = M8MidiSettings(receive_sync=1, song_row_cue_channel=15)
        m.set_track_input_channel(2, 10)
        reloaded = M8MidiSettings.read(m.write())
        self.assertEqual(reloaded.receive_sync, 1)
        self.assertEqual(reloaded.song_row_cue_channel, 15)
        self.assertEqual(reloaded.track_input_channel(2), 10)

    def test_dict(self):
        m = M8MidiSettings(receive_sync=1, control_map_channel=4)
        m.set_track_input_channel(0, 1)
        m.set_track_input_instrument(0, 8)
        d = m.to_dict()
        self.assertEqual(d["receive_sync"], 1)
        self.assertIn("track_input_channel", d)
        self.assertEqual(d["track_input_channel"][0], 1)
        self.assertEqual(d["track_input_instrument"][0], 8)

        reloaded = M8MidiSettings.from_dict(d)
        self.assertEqual(reloaded.receive_sync, 1)
        self.assertEqual(reloaded.track_input_channel(0), 1)
        self.assertEqual(reloaded.track_input_instrument(0), 8)

    def test_clone(self):
        m = M8MidiSettings(receive_sync=1)
        cloned = m.clone()
        cloned.receive_sync = 0
        self.assertEqual(m.receive_sync, 1)


class TestProjectMidiAndKey(unittest.TestCase):
    """Integration: project.midi at file offset 160, metadata.key at 187."""

    def test_template_midi_settings_present(self):
        p = M8Project.initialise()
        self.assertIsInstance(p.midi, M8MidiSettings)

    def test_midi_at_expected_offset(self):
        p = M8Project.initialise()
        p.midi.receive_sync = 0xAB
        data = p.write()
        self.assertEqual(data[MIDI_SETTINGS_OFFSET], 0xAB)

    def test_key_at_offset_187_not_160(self):
        """Regression: the key byte must land at file 187, not 160.

        Prior to this commit pym8 wrote it to file 160 (clobbering
        MidiSettings.receive_sync).
        """
        p = M8Project.initialise()
        p.metadata.key = 7
        p.midi.receive_sync = 1
        data = p.write()
        self.assertEqual(data[KEY_OFFSET], 7)
        self.assertEqual(data[MIDI_SETTINGS_OFFSET], 1)
        # And they must not have collided
        self.assertNotEqual(KEY_OFFSET, MIDI_SETTINGS_OFFSET)

    def test_key_round_trip_through_project(self):
        p = M8Project.initialise()
        p.metadata.key = 9
        loaded = M8Project.read(p.write())
        self.assertEqual(loaded.metadata.key, 9)

    def test_midi_round_trip_through_project(self):
        p = M8Project.initialise()
        p.midi.receive_sync = 1
        p.midi.send_transport = 3
        p.midi.set_track_input_channel(0, 5)
        loaded = M8Project.read(p.write())
        self.assertEqual(loaded.midi.receive_sync, 1)
        self.assertEqual(loaded.midi.send_transport, 3)
        self.assertEqual(loaded.midi.track_input_channel(0), 5)

    def test_stable_round_trip_with_mutations(self):
        p = M8Project.initialise()
        p.metadata.key = 11
        p.midi.receive_sync = 1
        bytes1 = p.write()
        bytes2 = M8Project.read(bytes1).write()
        self.assertEqual(bytes1, bytes2)

    def test_clone_preserves_midi_and_key(self):
        p = M8Project.initialise()
        p.metadata.key = 5
        p.midi.receive_sync = 1
        cloned = p.clone()
        self.assertEqual(cloned.metadata.key, 5)
        self.assertEqual(cloned.midi.receive_sync, 1)
        # Independence
        cloned.metadata.key = 99
        cloned.midi.receive_sync = 0
        self.assertEqual(p.metadata.key, 5)
        self.assertEqual(p.midi.receive_sync, 1)


if __name__ == "__main__":
    unittest.main()
