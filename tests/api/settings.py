"""Tests for M8MixerSettings and M8EffectsSettings.

Covers byte layout against the bundled template, descriptor round-trips,
project-level integration (read at right offset, clone independence), and
the convenience accessors for the 8-track volume array.
"""
import unittest

from m8.api.project import (
    EFFECTS_SETTINGS_OFFSET, MIXER_SETTINGS_OFFSET, M8Project,
)
from m8.api.settings import M8EffectsSettings, M8MixerSettings


class TestM8MixerSettingsByteLayout(unittest.TestCase):
    """Confirm offsets and total size match m8-file-parser/src/settings.rs."""

    def test_block_size(self):
        self.assertEqual(M8MixerSettings.BYTES, 32)
        self.assertEqual(len(M8MixerSettings().write()), 32)

    def test_master_volume_at_byte_0(self):
        m = M8MixerSettings()
        m.master_volume = 0xAB
        self.assertEqual(m.write()[0], 0xAB)

    def test_track_volumes_at_bytes_2_through_9(self):
        m = M8MixerSettings()
        for i in range(8):
            m.set_track_volume(i, 0x10 + i)
        data = m.write()
        for i in range(8):
            self.assertEqual(data[2 + i], 0x10 + i)

    def test_dj_filter_block_at_25_27(self):
        m = M8MixerSettings(dj_filter=0xCC, dj_peak=0xDD, dj_filter_type=0x02)
        data = m.write()
        self.assertEqual(data[25], 0xCC)
        self.assertEqual(data[26], 0xDD)
        self.assertEqual(data[27], 0x02)

    def test_v6_0_limiter_at_28_30(self):
        m = M8MixerSettings(limiter_attack=0x11, limiter_release=0x22, limiter_soft_clip=1)
        data = m.write()
        self.assertEqual(data[28], 0x11)
        self.assertEqual(data[29], 0x22)
        self.assertEqual(data[30], 0x01)

    def test_v6_2_ott_level_at_byte_31(self):
        m = M8MixerSettings(ott_level=0x40)
        self.assertEqual(m.write()[31], 0x40)


class TestM8MixerSettingsTrackVolumeAccessor(unittest.TestCase):
    def test_get_set(self):
        m = M8MixerSettings()
        m.set_track_volume(3, 0x80)
        self.assertEqual(m.track_volume(3), 0x80)
        # Doesn't affect other tracks
        self.assertEqual(m.track_volume(0), 0)
        self.assertEqual(m.track_volume(7), 0)

    def test_out_of_range_raises(self):
        m = M8MixerSettings()
        with self.assertRaises(IndexError):
            m.track_volume(8)
        with self.assertRaises(IndexError):
            m.set_track_volume(-1, 0)


class TestM8MixerSettingsAnalogStereo(unittest.TestCase):
    def test_stereo_by_default(self):
        # apply_default leaves analog_mode at 0; but the M8 template ships
        # with analog_mode = 0xFF (stereo). Construct from template to check.
        m = M8MixerSettings()
        m.analog_mode = 0xFF
        self.assertTrue(m.is_analog_stereo)

    def test_dual_mono_when_mode_is_not_ff(self):
        m = M8MixerSettings()
        m.analog_mode = 0x80
        self.assertFalse(m.is_analog_stereo)


class TestM8MixerSettingsRoundTrip(unittest.TestCase):
    def test_binary(self):
        m = M8MixerSettings(
            master_volume=0xA0,
            chorus_volume=0x40,
            dj_filter=0x88,
            limiter_release=0x30,
            ott_level=0x10,
        )
        m.set_track_volume(5, 0x70)
        reloaded = M8MixerSettings.read(m.write())
        self.assertEqual(reloaded.master_volume, 0xA0)
        self.assertEqual(reloaded.track_volume(5), 0x70)
        self.assertEqual(reloaded.chorus_volume, 0x40)
        self.assertEqual(reloaded.dj_filter, 0x88)
        self.assertEqual(reloaded.limiter_release, 0x30)
        self.assertEqual(reloaded.ott_level, 0x10)

    def test_dict(self):
        m = M8MixerSettings(master_volume=0x88, ott_level=0x44)
        m.set_track_volume(0, 0x50)
        reloaded = M8MixerSettings.from_dict(m.to_dict())
        self.assertEqual(reloaded.master_volume, 0x88)
        self.assertEqual(reloaded.track_volume(0), 0x50)
        self.assertEqual(reloaded.ott_level, 0x44)

    def test_clone(self):
        m = M8MixerSettings(master_volume=0x88)
        cloned = m.clone()
        cloned.master_volume = 0x11
        self.assertEqual(m.master_volume, 0x88)


class TestM8EffectsSettingsByteLayout(unittest.TestCase):
    def test_block_size(self):
        self.assertEqual(M8EffectsSettings.BYTES, 26)
        self.assertEqual(len(M8EffectsSettings().write()), 26)

    def test_chorus_at_bytes_0_3(self):
        fx = M8EffectsSettings(
            chorus_mod_depth=0xA0, chorus_mod_freq=0xB0,
            chorus_width=0xC0, chorus_reverb_send=0xD0,
        )
        data = fx.write()
        self.assertEqual(data[0:4], bytes([0xA0, 0xB0, 0xC0, 0xD0]))

    def test_delay_at_bytes_7_13(self):
        fx = M8EffectsSettings(
            delay_filter_hp=0x11, delay_filter_lp=0x22,
            delay_time_l=0x33, delay_time_r=0x44,
            delay_feedback=0x55, delay_width=0x66, delay_reverb_send=0x77,
        )
        data = fx.write()
        self.assertEqual(data[7], 0x11)
        self.assertEqual(data[8], 0x22)
        self.assertEqual(data[9], 0x33)
        self.assertEqual(data[13], 0x77)

    def test_reverb_at_bytes_15_21(self):
        fx = M8EffectsSettings(
            reverb_filter_hp=0xAA, reverb_filter_lp=0xBB,
            reverb_size=0xCC, reverb_damping=0xDD,
        )
        data = fx.write()
        self.assertEqual(data[15], 0xAA)
        self.assertEqual(data[17], 0xCC)
        self.assertEqual(data[18], 0xDD)

    def test_v6_2_fields_at_22_25(self):
        fx = M8EffectsSettings(
            reverb_shimmer=0x88, ott_time=0x99, ott_color=0xAA, mfx_kind=2,
        )
        data = fx.write()
        self.assertEqual(data[22:26], bytes([0x88, 0x99, 0xAA, 0x02]))


class TestM8EffectsSettingsRoundTrip(unittest.TestCase):
    def test_binary(self):
        fx = M8EffectsSettings(reverb_size=0xC0, mfx_kind=1, reverb_shimmer=0x40)
        reloaded = M8EffectsSettings.read(fx.write())
        self.assertEqual(reloaded.reverb_size, 0xC0)
        self.assertEqual(reloaded.mfx_kind, 1)
        self.assertEqual(reloaded.reverb_shimmer, 0x40)

    def test_dict(self):
        fx = M8EffectsSettings(delay_time_l=0x60, reverb_damping=0x80)
        reloaded = M8EffectsSettings.from_dict(fx.to_dict())
        self.assertEqual(reloaded.delay_time_l, 0x60)
        self.assertEqual(reloaded.reverb_damping, 0x80)


class TestProjectIntegration(unittest.TestCase):
    def test_template_mixer_master_volume(self):
        """Template ships with master_volume = 0xE0 (per Rust songs.rs test)."""
        p = M8Project.initialise()
        self.assertEqual(p.mixer.master_volume, 0xE0)

    def test_template_track_volumes_all_e0(self):
        p = M8Project.initialise()
        for i in range(8):
            self.assertEqual(p.mixer.track_volume(i), 0xE0)

    def test_template_dj_filter(self):
        p = M8Project.initialise()
        self.assertEqual(p.mixer.dj_filter, 0x80)

    def test_template_analog_input_is_stereo(self):
        p = M8Project.initialise()
        self.assertTrue(p.mixer.is_analog_stereo)

    def test_mixer_at_expected_offset(self):
        p = M8Project.initialise()
        p.mixer.master_volume = 0xC9
        data = p.write()
        self.assertEqual(data[MIXER_SETTINGS_OFFSET], 0xC9)

    def test_effects_at_expected_offset(self):
        p = M8Project.initialise()
        p.effects.chorus_mod_depth = 0xC9
        data = p.write()
        self.assertEqual(data[EFFECTS_SETTINGS_OFFSET], 0xC9)

    def test_settings_round_trip(self):
        p = M8Project.initialise()
        p.mixer.master_volume = 0x55
        p.mixer.set_track_volume(2, 0x66)
        p.effects.reverb_size = 0x77
        loaded = M8Project.read(p.write())
        self.assertEqual(loaded.mixer.master_volume, 0x55)
        self.assertEqual(loaded.mixer.track_volume(2), 0x66)
        self.assertEqual(loaded.effects.reverb_size, 0x77)

    def test_stable_round_trip(self):
        p = M8Project.initialise()
        p.mixer.dj_filter_type = 1
        p.effects.ott_color = 0x40
        bytes1 = p.write()
        bytes2 = M8Project.read(bytes1).write()
        self.assertEqual(bytes1, bytes2)

    def test_clone_independence(self):
        p = M8Project.initialise()
        p.mixer.master_volume = 0x10
        p.effects.reverb_size = 0x20
        cloned = p.clone()
        cloned.mixer.master_volume = 0xFF
        cloned.effects.reverb_size = 0xEE
        self.assertEqual(p.mixer.master_volume, 0x10)
        self.assertEqual(p.effects.reverb_size, 0x20)


if __name__ == "__main__":
    unittest.main()
