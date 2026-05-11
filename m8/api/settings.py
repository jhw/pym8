# m8/api/settings.py
"""M8 mixer and effects settings.

Follows m8-file-parser/src/settings.rs. pym8 targets firmware 6.0+ which
means all the firmware-conditional fields (limiter attack/release, OTT
controls, reverb shimmer) are present unconditionally.

Layout in the project file:

  byte 206       MixerSettings (32 bytes in v6.2+)
  byte 107969    EffectsSettings (26 bytes in v6.2+)

MidiSettings (27 bytes between the project name and the key byte, file byte
160) is **not yet modelled**. It interleaves with what pym8's M8Metadata
currently treats as a single block; integrating it requires restructuring
the metadata reader. Tracked in docs/planning/roadmap.md.
"""

from m8.api.fields import ByteField, IndexedBytesField, iter_fields


# ---- mixer ----

class M8MixerSettings:
    """Project-level mixer state.

    Lives at file offset 206. 32 bytes in firmware 6.2+. The Rust source
    splits this across MixerSettings + LimiterParameter + AnalogInputSettings;
    pym8 keeps it flat — same bytes, fewer wrappers.
    """

    BYTES = 32

    master_volume       = ByteField(0)
    master_limit        = ByteField(1)

    # Per-track volumes. `mixer.track_volumes[3] = 0x80` writes through.
    track_volumes       = IndexedBytesField(2, length=8)

    chorus_volume       = ByteField(10)
    delay_volume        = ByteField(11)
    reverb_volume       = ByteField(12)

    # Analog input — stereo or dual-mono depending on `analog_mode`:
    #   analog_mode == 0xFF      → stereo  (use analog_l_* fields only)
    #   analog_mode anything else → dual mono (it IS the right volume; use
    #                              both analog_l_* and analog_r_* fields)
    analog_l_volume      = ByteField(13)
    analog_mode          = ByteField(14)
    usb_volume           = ByteField(15)

    analog_l_chorus_send = ByteField(16)
    analog_l_delay_send  = ByteField(17)
    analog_l_reverb_send = ByteField(18)
    analog_r_chorus_send = ByteField(19)
    analog_r_delay_send  = ByteField(20)
    analog_r_reverb_send = ByteField(21)

    usb_chorus_send      = ByteField(22)
    usb_delay_send       = ByteField(23)
    usb_reverb_send      = ByteField(24)

    dj_filter            = ByteField(25)
    dj_peak              = ByteField(26)
    dj_filter_type       = ByteField(27)

    # Firmware 6.0+
    limiter_attack       = ByteField(28)
    limiter_release      = ByteField(29)
    limiter_soft_clip    = ByteField(30)

    # Firmware 6.2+
    ott_level            = ByteField(31)

    def __init__(self, **kwargs):
        self._data = bytearray(self.BYTES)
        for _, fld in iter_fields(type(self)):
            fld.apply_default(self)
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def is_analog_stereo(self):
        """True if the analog input is wired as a single stereo pair."""
        return self.analog_mode == 0xFF

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


# ---- effects ----

class M8EffectsSettings:
    """Project-level chorus/delay/reverb knob state.

    Lives at file offset 107969. 26 bytes in firmware 6.2+. The Rust source
    flags some sub-fields as Option<...> for pre-v4.1 vs post-v4.1
    semantics; pym8 just exposes the raw bytes and leaves interpretation
    to the caller (we target v6.0+ where all fields are present).
    """

    BYTES = 26

    chorus_mod_depth   = ByteField(0)
    chorus_mod_freq    = ByteField(1)
    chorus_width       = ByteField(2)
    chorus_reverb_send = ByteField(3)
    # bytes 4-6 reserved (Rust skips 3 bytes here)

    # delay_filter_hp/lp are only meaningful pre-v4.1; in v4.1+ Rust reads
    # but discards them. We expose them so round-trip is exact.
    delay_filter_hp    = ByteField(7)
    delay_filter_lp    = ByteField(8)
    delay_time_l       = ByteField(9)
    delay_time_r       = ByteField(10)
    delay_feedback     = ByteField(11)
    delay_width        = ByteField(12)
    delay_reverb_send  = ByteField(13)
    # byte 14 reserved

    reverb_filter_hp   = ByteField(15)
    reverb_filter_lp   = ByteField(16)
    reverb_size        = ByteField(17)
    reverb_damping     = ByteField(18)
    reverb_mod_depth   = ByteField(19)
    reverb_mod_freq    = ByteField(20)
    reverb_width       = ByteField(21)

    # Firmware 6.2+
    reverb_shimmer     = ByteField(22)
    ott_time           = ByteField(23)
    ott_color          = ByteField(24)
    mfx_kind           = ByteField(25)  # 0=Chorus, 1=Phaser, 2=Flanger

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
