# m8/api/midi_settings.py
"""M8 project MIDI settings — sync/transport, record options, per-track
input routing.

27 bytes at file offset 160 (between the project name at file byte 148
and the musical key byte at file byte 187). Layout follows
m8-file-parser/src/settings.rs::MidiSettings.

Per-track input arrays (channel + instrument) are 8 entries each; we
provide list-like accessors for ergonomic indexing without exposing 16
discrete `track_input_channel_N` descriptors.
"""

from m8.api.fields import ByteField, iter_fields


MIDI_SETTINGS_BYTES = 27
N_TRACKS = 8


class M8MidiSettings:
    """MIDI sync, transport, and per-track input routing.

    Boolean fields are stored as raw bytes (0 / non-zero). Convenience:
    treat any non-zero value as True when reading; clients typically just
    set 0 or 1.
    """

    BYTES = MIDI_SETTINGS_BYTES

    receive_sync                     = ByteField(0)
    receive_transport                = ByteField(1)
    send_sync                        = ByteField(2)
    send_transport                   = ByteField(3)
    record_note_channel              = ByteField(4)
    record_note_velocity             = ByteField(5)
    record_note_delay_kill_commands  = ByteField(6)
    control_map_channel              = ByteField(7)
    song_row_cue_channel             = ByteField(8)
    # bytes 9-16   : track_input_channel[0..7]    (accessor methods below)
    # bytes 17-24  : track_input_instrument[0..7] (accessor methods below)
    track_input_program_change       = ByteField(25)
    track_input_mode                 = ByteField(26)

    _TRACK_CHANNEL_BASE = 9
    _TRACK_INSTRUMENT_BASE = 17

    def __init__(self, **kwargs):
        self._data = bytearray(self.BYTES)
        for _, fld in iter_fields(type(self)):
            fld.apply_default(self)
        for key, value in kwargs.items():
            setattr(self, key, value)

    # --- per-track input accessors ---

    def track_input_channel(self, track):
        """MIDI channel that records into track 0-7 (0xFF = disabled)."""
        if not 0 <= track < N_TRACKS:
            raise IndexError(f"track index {track} out of range [0, {N_TRACKS - 1}]")
        return self._data[self._TRACK_CHANNEL_BASE + track]

    def set_track_input_channel(self, track, value):
        if not 0 <= track < N_TRACKS:
            raise IndexError(f"track index {track} out of range [0, {N_TRACKS - 1}]")
        if hasattr(value, "value"):
            value = value.value
        self._data[self._TRACK_CHANNEL_BASE + track] = int(value) & 0xFF

    def track_input_instrument(self, track):
        """Instrument slot that incoming MIDI on track 0-7 fires."""
        if not 0 <= track < N_TRACKS:
            raise IndexError(f"track index {track} out of range [0, {N_TRACKS - 1}]")
        return self._data[self._TRACK_INSTRUMENT_BASE + track]

    def set_track_input_instrument(self, track, value):
        if not 0 <= track < N_TRACKS:
            raise IndexError(f"track index {track} out of range [0, {N_TRACKS - 1}]")
        if hasattr(value, "value"):
            value = value.value
        self._data[self._TRACK_INSTRUMENT_BASE + track] = int(value) & 0xFF

    @classmethod
    def read(cls, data, version=None):
        instance = cls.__new__(cls)
        instance._data = bytearray(data[:cls.BYTES])
        return instance

    def write(self):
        return bytes(self._data)

    def clone(self):
        instance = self.__class__.__new__(self.__class__)
        instance._data = bytearray(self._data)
        return instance

    def to_dict(self):
        result = {name: fld.to_dict(self) for name, fld in iter_fields(type(self))}
        result["track_input_channel"] = [
            self.track_input_channel(i) for i in range(N_TRACKS)
        ]
        result["track_input_instrument"] = [
            self.track_input_instrument(i) for i in range(N_TRACKS)
        ]
        return result

    @classmethod
    def from_dict(cls, d):
        instance = cls()
        fields_by_name = {name: fld for name, fld in iter_fields(cls)}
        for key, value in d.items():
            if key == "track_input_channel":
                for i, v in enumerate(value[:N_TRACKS]):
                    instance.set_track_input_channel(i, v)
            elif key == "track_input_instrument":
                for i, v in enumerate(value[:N_TRACKS]):
                    instance.set_track_input_instrument(i, v)
            elif key in fields_by_name:
                fields_by_name[key].from_dict(instance, value)
        return instance
