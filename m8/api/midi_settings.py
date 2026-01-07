# m8/api/midi_settings.py
"""M8 MIDI settings - project-level MIDI configuration."""

from enum import IntEnum

# MIDI settings offset in M8 project file
# Located immediately after metadata (offset 14 + size 147 = 161)
MIDI_SETTINGS_OFFSET = 161
MIDI_SETTINGS_SIZE = 27  # Total size of MIDI settings block


class M8TransportMode(IntEnum):
    """MIDI transport behavior modes."""
    OFF = 0x00      # No transport messages
    PATTERN = 0x01  # Send transport at pattern level
    SONG = 0x02     # Send transport at song level


class M8TrackInputMode(IntEnum):
    """MIDI track input modes."""
    MONO = 0x00
    LEGATO = 0x01
    POLY = 0x02


class M8RecordDelayKill(IntEnum):
    """MIDI record delay/kill command modes."""
    OFF = 0x00
    KILL = 0x01
    DELAY = 0x02
    BOTH = 0x03


# Field offsets within MIDI settings block
class M8MidiSettingsParam(IntEnum):
    """Byte offsets for MIDI settings parameters."""
    RECEIVE_SYNC = 0        # bool: Receive MIDI clock
    RECEIVE_TRANSPORT = 1   # u8: Receive transport mode (M8TransportMode)
    SEND_SYNC = 2           # bool: Send MIDI clock
    SEND_TRANSPORT = 3      # u8: Send transport mode (M8TransportMode)
    RECORD_NOTE_CHANNEL = 4 # u8: Channel for note recording
    RECORD_NOTE_VELOCITY = 5  # bool: Record velocity
    RECORD_DELAY_KILL = 6   # u8: Record delay/kill commands (M8RecordDelayKill)
    CONTROL_MAP_CHANNEL = 7 # u8: Control map channel
    SONG_ROW_CUE_CHANNEL = 8  # u8: Song row cue channel
    TRACK_INPUT_CHANNEL = 9   # [u8; 8]: Per-track input channels (9-16)
    TRACK_INPUT_INSTRUMENT = 17  # [u8; 8]: Per-track instruments (17-24)
    TRACK_INPUT_PROGRAM_CHANGE = 25  # bool: Program change enabled
    TRACK_INPUT_MODE = 26   # u8: Track input mode (M8TrackInputMode)


class M8MidiSettings:
    """M8 project-level MIDI settings.

    Handles MIDI clock, transport, and input routing configuration.
    """

    def __init__(self):
        """Initialize MIDI settings with defaults."""
        self._data = bytearray(MIDI_SETTINGS_SIZE)

        # Apply defaults (matching m8-js defaults)
        self._data[M8MidiSettingsParam.CONTROL_MAP_CHANNEL] = 0x11  # Channel 17
        self._data[M8MidiSettingsParam.SONG_ROW_CUE_CHANNEL] = 0x0B  # Channel 11
        self._data[M8MidiSettingsParam.RECORD_NOTE_VELOCITY] = 0x01  # ON

        # Track input channels default to 1-8
        for i in range(8):
            self._data[M8MidiSettingsParam.TRACK_INPUT_CHANNEL + i] = i + 1

        self._data[M8MidiSettingsParam.TRACK_INPUT_PROGRAM_CHANGE] = 0x01  # ON
        self._data[M8MidiSettingsParam.TRACK_INPUT_MODE] = M8TrackInputMode.LEGATO

    @classmethod
    def read(cls, data):
        """Read MIDI settings from binary data."""
        instance = cls()
        instance._data = bytearray(data[:MIDI_SETTINGS_SIZE])
        return instance

    def write(self):
        """Write MIDI settings to binary data."""
        return bytes(self._data)

    def clone(self):
        """Create a copy of these MIDI settings."""
        instance = M8MidiSettings()
        instance._data = bytearray(self._data)
        return instance

    # Convenience properties for common settings

    @property
    def receive_sync(self):
        """Whether to receive MIDI clock."""
        return bool(self._data[M8MidiSettingsParam.RECEIVE_SYNC])

    @receive_sync.setter
    def receive_sync(self, value):
        self._data[M8MidiSettingsParam.RECEIVE_SYNC] = 1 if value else 0

    @property
    def receive_transport(self):
        """MIDI transport receive mode."""
        return self._data[M8MidiSettingsParam.RECEIVE_TRANSPORT]

    @receive_transport.setter
    def receive_transport(self, value):
        self._data[M8MidiSettingsParam.RECEIVE_TRANSPORT] = int(value)

    @property
    def send_sync(self):
        """Whether to send MIDI clock."""
        return bool(self._data[M8MidiSettingsParam.SEND_SYNC])

    @send_sync.setter
    def send_sync(self, value):
        self._data[M8MidiSettingsParam.SEND_SYNC] = 1 if value else 0

    @property
    def send_transport(self):
        """MIDI transport send mode."""
        return self._data[M8MidiSettingsParam.SEND_TRANSPORT]

    @send_transport.setter
    def send_transport(self, value):
        self._data[M8MidiSettingsParam.SEND_TRANSPORT] = int(value)

    @property
    def control_map_channel(self):
        """Control map MIDI channel."""
        return self._data[M8MidiSettingsParam.CONTROL_MAP_CHANNEL]

    @control_map_channel.setter
    def control_map_channel(self, value):
        self._data[M8MidiSettingsParam.CONTROL_MAP_CHANNEL] = value

    @property
    def song_row_cue_channel(self):
        """Song row cue MIDI channel."""
        return self._data[M8MidiSettingsParam.SONG_ROW_CUE_CHANNEL]

    @song_row_cue_channel.setter
    def song_row_cue_channel(self, value):
        self._data[M8MidiSettingsParam.SONG_ROW_CUE_CHANNEL] = value

    def get_track_input_channel(self, track):
        """Get input channel for a track (0-7)."""
        if not 0 <= track < 8:
            raise ValueError(f"Track must be 0-7, got {track}")
        return self._data[M8MidiSettingsParam.TRACK_INPUT_CHANNEL + track]

    def set_track_input_channel(self, track, channel):
        """Set input channel for a track (0-7)."""
        if not 0 <= track < 8:
            raise ValueError(f"Track must be 0-7, got {track}")
        self._data[M8MidiSettingsParam.TRACK_INPUT_CHANNEL + track] = channel

    def get_track_input_instrument(self, track):
        """Get input instrument for a track (0-7)."""
        if not 0 <= track < 8:
            raise ValueError(f"Track must be 0-7, got {track}")
        return self._data[M8MidiSettingsParam.TRACK_INPUT_INSTRUMENT + track]

    def set_track_input_instrument(self, track, instrument):
        """Set input instrument for a track (0-7)."""
        if not 0 <= track < 8:
            raise ValueError(f"Track must be 0-7, got {track}")
        self._data[M8MidiSettingsParam.TRACK_INPUT_INSTRUMENT + track] = instrument
