import unittest
from m8.api.midi_settings import (
    M8MidiSettings, M8MidiSettingsParam, M8TransportMode,
    M8TrackInputMode, M8RecordDelayKill, MIDI_SETTINGS_SIZE
)


class TestM8MidiSettings(unittest.TestCase):

    def test_constructor_defaults(self):
        """Test default constructor values."""
        settings = M8MidiSettings()

        # Check defaults
        self.assertEqual(settings.receive_sync, False)
        self.assertEqual(settings.receive_transport, M8TransportMode.OFF)
        self.assertEqual(settings.send_sync, False)
        self.assertEqual(settings.send_transport, M8TransportMode.OFF)
        self.assertEqual(settings.control_map_channel, 0x11)
        self.assertEqual(settings.song_row_cue_channel, 0x0B)

        # Check track input channels default to 1-8
        for i in range(8):
            self.assertEqual(settings.get_track_input_channel(i), i + 1)

    def test_send_sync_property(self):
        """Test send_sync property getter and setter."""
        settings = M8MidiSettings()

        self.assertFalse(settings.send_sync)

        settings.send_sync = True
        self.assertTrue(settings.send_sync)

        settings.send_sync = False
        self.assertFalse(settings.send_sync)

    def test_send_transport_property(self):
        """Test send_transport property getter and setter."""
        settings = M8MidiSettings()

        self.assertEqual(settings.send_transport, M8TransportMode.OFF)

        settings.send_transport = M8TransportMode.PATTERN
        self.assertEqual(settings.send_transport, M8TransportMode.PATTERN)

        settings.send_transport = M8TransportMode.SONG
        self.assertEqual(settings.send_transport, M8TransportMode.SONG)

    def test_receive_sync_property(self):
        """Test receive_sync property getter and setter."""
        settings = M8MidiSettings()

        self.assertFalse(settings.receive_sync)

        settings.receive_sync = True
        self.assertTrue(settings.receive_sync)

    def test_receive_transport_property(self):
        """Test receive_transport property getter and setter."""
        settings = M8MidiSettings()

        self.assertEqual(settings.receive_transport, M8TransportMode.OFF)

        settings.receive_transport = M8TransportMode.SONG
        self.assertEqual(settings.receive_transport, M8TransportMode.SONG)

    def test_track_input_channel(self):
        """Test track input channel get/set."""
        settings = M8MidiSettings()

        # Test setting and getting
        settings.set_track_input_channel(0, 10)
        self.assertEqual(settings.get_track_input_channel(0), 10)

        settings.set_track_input_channel(7, 16)
        self.assertEqual(settings.get_track_input_channel(7), 16)

    def test_track_input_channel_bounds(self):
        """Test track input channel bounds checking."""
        settings = M8MidiSettings()

        with self.assertRaises(ValueError):
            settings.get_track_input_channel(-1)

        with self.assertRaises(ValueError):
            settings.get_track_input_channel(8)

        with self.assertRaises(ValueError):
            settings.set_track_input_channel(-1, 1)

        with self.assertRaises(ValueError):
            settings.set_track_input_channel(8, 1)

    def test_track_input_instrument(self):
        """Test track input instrument get/set."""
        settings = M8MidiSettings()

        settings.set_track_input_instrument(0, 0x10)
        self.assertEqual(settings.get_track_input_instrument(0), 0x10)

        settings.set_track_input_instrument(7, 0x7F)
        self.assertEqual(settings.get_track_input_instrument(7), 0x7F)

    def test_write_read_roundtrip(self):
        """Test write/read round-trip preserves all settings."""
        settings = M8MidiSettings()

        # Customize settings
        settings.send_sync = True
        settings.send_transport = M8TransportMode.SONG
        settings.receive_sync = True
        settings.receive_transport = M8TransportMode.PATTERN
        settings.control_map_channel = 0x05
        settings.song_row_cue_channel = 0x0A
        settings.set_track_input_channel(0, 0x0F)
        settings.set_track_input_instrument(3, 0x20)

        # Write and read back
        binary = settings.write()
        self.assertEqual(len(binary), MIDI_SETTINGS_SIZE)

        restored = M8MidiSettings.read(binary)

        # Verify all values
        self.assertTrue(restored.send_sync)
        self.assertEqual(restored.send_transport, M8TransportMode.SONG)
        self.assertTrue(restored.receive_sync)
        self.assertEqual(restored.receive_transport, M8TransportMode.PATTERN)
        self.assertEqual(restored.control_map_channel, 0x05)
        self.assertEqual(restored.song_row_cue_channel, 0x0A)
        self.assertEqual(restored.get_track_input_channel(0), 0x0F)
        self.assertEqual(restored.get_track_input_instrument(3), 0x20)

    def test_clone(self):
        """Test cloning creates independent copy."""
        original = M8MidiSettings()
        original.send_sync = True
        original.send_transport = M8TransportMode.PATTERN

        cloned = original.clone()

        # Verify values match
        self.assertTrue(cloned.send_sync)
        self.assertEqual(cloned.send_transport, M8TransportMode.PATTERN)

        # Modify clone and verify original unchanged
        cloned.send_sync = False
        cloned.send_transport = M8TransportMode.OFF

        self.assertTrue(original.send_sync)
        self.assertEqual(original.send_transport, M8TransportMode.PATTERN)

    def test_transport_mode_enum(self):
        """Test M8TransportMode enum values."""
        self.assertEqual(M8TransportMode.OFF, 0x00)
        self.assertEqual(M8TransportMode.PATTERN, 0x01)
        self.assertEqual(M8TransportMode.SONG, 0x02)

    def test_track_input_mode_enum(self):
        """Test M8TrackInputMode enum values."""
        self.assertEqual(M8TrackInputMode.MONO, 0x00)
        self.assertEqual(M8TrackInputMode.LEGATO, 0x01)
        self.assertEqual(M8TrackInputMode.POLY, 0x02)


class TestM8MidiSettingsIntegration(unittest.TestCase):
    """Test MIDI settings integration with M8Project."""

    def test_project_midi_settings_read(self):
        """Test that MIDI settings are read from project file."""
        from pathlib import Path
        from m8.api.project import M8Project

        # Use the template file
        template_path = Path(__file__).parent.parent.parent / "m8/templates/TEMPLATE-6-2-1.m8s"
        if not template_path.exists():
            self.skipTest(f"Template not found: {template_path}")

        project = M8Project.read_from_file(str(template_path))

        # MIDI settings should be loaded
        self.assertIsNotNone(project.midi_settings)
        self.assertIsInstance(project.midi_settings, M8MidiSettings)

    def test_project_midi_settings_write(self):
        """Test that MIDI settings are written to project file."""
        from m8.api.project import M8Project

        project = M8Project.initialise()

        # Modify MIDI settings
        project.midi_settings.send_sync = True
        project.midi_settings.send_transport = M8TransportMode.SONG

        # Write and read back
        binary = project.write()
        restored = M8Project.read(binary)

        # Verify settings were preserved
        self.assertTrue(restored.midi_settings.send_sync)
        self.assertEqual(restored.midi_settings.send_transport, M8TransportMode.SONG)


if __name__ == '__main__':
    unittest.main()
