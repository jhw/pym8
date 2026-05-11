import unittest

from m8.api.fx import (
    M8FXTuple, M8FXTuples, M8SequenceFX, M8SamplerFX, M8ModulatorFX, M8MixerFX,
    EMPTY_KEY,
)
from m8.api.phrase import M8Phrase, M8PhraseStep, M8Note


class TestM8ModulatorFXEnum(unittest.TestCase):
    """Modulator FX commands occupy 0x92..0xA5 (4 mod slots * 5 commands).

    Layout matches m8-file-parser: base instrument commands end at 0x91,
    modulator commands fill 0x92..0xA5, then sampler extras start at 0xA6.
    """

    def test_byte_codes_match_firmware_spec(self):
        # Slot 1 starts at 0x92 (right after base instrument commands)
        self.assertEqual(M8ModulatorFX.EA1, 0x92)
        self.assertEqual(M8ModulatorFX.AT1, 0x93)
        self.assertEqual(M8ModulatorFX.HO1, 0x94)
        self.assertEqual(M8ModulatorFX.DE1, 0x95)
        self.assertEqual(M8ModulatorFX.ET1, 0x96)

        # Each slot is 5 codes wide
        self.assertEqual(M8ModulatorFX.EA2 - M8ModulatorFX.EA1, 5)
        self.assertEqual(M8ModulatorFX.EA3 - M8ModulatorFX.EA2, 5)
        self.assertEqual(M8ModulatorFX.EA4 - M8ModulatorFX.EA3, 5)

        # Last modulator command is at 0xA5 (just before SLI at 0xA6)
        self.assertEqual(M8ModulatorFX.ET4, 0xA5)
        self.assertEqual(M8SamplerFX.SLI, M8ModulatorFX.ET4 + 1)

    def test_all_twenty_codes_present_and_contiguous(self):
        values = sorted(int(v) for v in M8ModulatorFX)
        self.assertEqual(len(values), 20)
        self.assertEqual(values[0], 0x92)
        self.assertEqual(values[-1], 0xA5)
        # No gaps
        for prev, nxt in zip(values, values[1:]):
            self.assertEqual(nxt, prev + 1)

    def test_no_overlap_with_other_fx_enums(self):
        mod_codes = {int(v) for v in M8ModulatorFX}
        sampler_codes = {int(v) for v in M8SamplerFX}
        sequence_codes = {int(v) for v in M8SequenceFX}
        mixer_codes = {int(v) for v in M8MixerFX}
        self.assertEqual(mod_codes & sampler_codes, set())
        self.assertEqual(mod_codes & sequence_codes, set())
        self.assertEqual(mod_codes & mixer_codes, set())


class TestM8ModulatorFXOnPhraseStep(unittest.TestCase):
    """Verify modulator FX can be written into a phrase step and round-trip."""

    def test_de1_fx_round_trip(self):
        # Set DE1 (AHD env 1 decay) FX on a step and read it back
        step = M8PhraseStep(note=int(M8Note.C_4), velocity=0x6F, instrument=0)
        step.fx[0] = M8FXTuple(key=M8ModulatorFX.DE1, value=0x40)
        step.fx[1] = M8FXTuple(key=M8ModulatorFX.DE2, value=0x20)

        raw = step.write()
        restored = M8PhraseStep.read(raw)

        self.assertEqual(restored.fx[0].key, M8ModulatorFX.DE1)
        self.assertEqual(restored.fx[0].value, 0x40)
        self.assertEqual(restored.fx[1].key, M8ModulatorFX.DE2)
        self.assertEqual(restored.fx[1].value, 0x20)

    def test_de1_fx_in_full_phrase_round_trip(self):
        phrase = M8Phrase()
        for s in range(0, 16, 4):
            step = M8PhraseStep(note=int(M8Note.E_2), velocity=0x60, instrument=0)
            step.fx[0] = M8FXTuple(key=M8ModulatorFX.DE1, value=0x10 + s)
            phrase[s] = step

        raw = phrase.write()
        restored = M8Phrase.read(raw)

        for s in range(0, 16, 4):
            self.assertEqual(restored[s].fx[0].key, M8ModulatorFX.DE1)
            self.assertEqual(restored[s].fx[0].value, 0x10 + s)
        for s in (1, 2, 3, 5):
            self.assertEqual(restored[s].fx[0].key, EMPTY_KEY)


class TestM8MixerFXEnum(unittest.TestCase):
    """Mixer FX commands occupy 0x1B..0x4D (51 codes, V6.2)."""

    def test_first_and_last_codes(self):
        self.assertEqual(M8MixerFX.VMV, 0x1B)
        self.assertEqual(M8MixerFX.MTT, 0x4D)

    def test_starts_right_after_sequence_fx(self):
        # OFF is the last sequence command (0x1A); VMV is the first mixer
        # command (0x1B).
        self.assertEqual(M8SequenceFX.OFF + 1, M8MixerFX.VMV)

    def test_all_codes_in_expected_range(self):
        codes = [int(v) for v in M8MixerFX]
        self.assertEqual(len(codes), 51)
        for c in codes:
            self.assertGreaterEqual(c, 0x1B)
            self.assertLessEqual(c, 0x4D)


class TestM8SamplerFXExtras(unittest.TestCase):
    def test_err_present(self):
        # ERR sits right after SLI in the sampler extra block
        self.assertEqual(M8SamplerFX.ERR, M8SamplerFX.SLI + 1)
        self.assertEqual(M8SamplerFX.ERR, 0xA7)


if __name__ == "__main__":
    unittest.main()
