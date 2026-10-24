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

from m8.api.fields import ByteField, IndexedBytesField, iter_fields


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
    # Per-track input arrays. `midi.track_input_channels[3] = 5` writes through.
    track_input_channels             = IndexedBytesField(9, length=N_TRACKS)
    track_input_instruments          = IndexedBytesField(17, length=N_TRACKS)
    track_input_program_change       = ByteField(25)
    track_input_mode                 = ByteField(26)

    def __init__(self, **kwargs):
        self._data = bytearray(self.BYTES)
        for _, fld in iter_fields(type(self)):
            fld.apply_default(self)
        for key, value in kwargs.items():
            setattr(self, key, value)

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
        return {name: fld.to_dict(self) for name, fld in iter_fields(type(self))}

    @classmethod
    def from_dict(cls, d):
        instance = cls()
        fields_by_name = {name: fld for name, fld in iter_fields(cls)}
        for key, value in d.items():
            fld = fields_by_name.get(key)
            if fld is not None:
                fld.from_dict(instance, value)
        return instance
