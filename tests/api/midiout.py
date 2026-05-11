"""M8MIDIOut-specific tests. Cross-cutting behaviour lives in instruments.py.

M8MIDIOut (type 3) is the pure MIDI-output instrument with 10 CC slots,
distinct from M8External (type 6, audio routing + 4 CCs).
"""
import unittest

from m8.api.instruments.midiout import M8MIDIOut, M8MIDIPort, M8MIDIOutModDest
from m8.api.instrument import M8InstrumentType


class TestM8MIDIOut(unittest.TestCase):
    def test_type_is_three(self):
        self.assertEqual(M8MIDIOut.TYPE_ID, M8InstrumentType.MIDIOUT)
        self.assertEqual(M8MIDIOut().type_id, 3)

    def test_ten_cc_slots(self):
        """MIDIOut exposes CCA through CCJ (10 slots) — the key differentiator from External."""
        m = M8MIDIOut()
        for letter in "abcdefghij":
            self.assertTrue(hasattr(m, f"cc{letter}_num"), f"cc{letter}_num")
            self.assertTrue(hasattr(m, f"cc{letter}_val"))

    def test_port_enum_includes_internal(self):
        """Unlike External, MIDIOut's port enum includes INTERNAL."""
        m = M8MIDIOut()
        m.port = M8MIDIPort.INTERNAL
        self.assertEqual(m.to_dict()["params"]["port"], "INTERNAL")

    def test_default_cc_slots_disabled(self):
        m = M8MIDIOut()
        for letter in "abcdefghij":
            self.assertEqual(getattr(m, f"cc{letter}_num"), 0x7F)
            self.assertEqual(getattr(m, f"cc{letter}_val"), 0x7F)

    def test_no_filter_section(self):
        """MIDIOut has no filter/amp/sends — that's an External concept."""
        m = M8MIDIOut()
        self.assertFalse(hasattr(m, "filter_type"))
        self.assertFalse(hasattr(m, "cutoff"))
        self.assertFalse(hasattr(m, "amp"))

    def test_mod_destinations_include_cce_through_ccj(self):
        """The MIDIOut mod-destination enum extends to CCE-CCJ for the extra CC slots."""
        self.assertEqual(M8MIDIOut.MOD_DEST_ENUM_CLASS, M8MIDIOutModDest)
        # Sanity-check the high CC entries exist
        self.assertEqual(M8MIDIOutModDest.CCJ, 0x0A)
        self.assertEqual(M8MIDIOutModDest.MOD_BINV, 0x0E)


if __name__ == "__main__":
    unittest.main()
