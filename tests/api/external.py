"""External-instrument-specific tests. Cross-cutting tests live in instruments.py.

Note: this is the audio-input M8External (type 6). For pure MIDI sequencing
use M8MIDIOut (type 3), tested in tests/api/midiout.py.
"""
import unittest

from m8.api.instruments.external import (
    M8External, M8ExternalInput, M8ExternalPort, M8ExternalModDest,
)


class TestM8ExternalSpecifics(unittest.TestCase):
    def test_default_midi_disabled_values(self):
        """CC slots default to 0x7F (off) so unconfigured ones don't transmit."""
        ext = M8External()
        for attr in ("bank", "program",
                     "cca_num", "cca_val", "ccb_num", "ccb_val",
                     "ccc_num", "ccc_val", "ccd_num", "ccd_val"):
            self.assertEqual(getattr(ext, attr), 0x7F, attr)

    def test_port_and_input_enums(self):
        ext = M8External()
        ext.port = M8ExternalPort.MIDI
        ext.input = M8ExternalInput.LINE_IN_L
        params = ext.to_dict()["params"]
        self.assertEqual(params["port"], "MIDI")
        self.assertEqual(params["input"], "LINE_IN_L")

    def test_four_cc_slots_only(self):
        """External exposes 4 CC slots (CCA-CCD). MIDIOut has 10."""
        ext = M8External()
        for letter in "abcd":
            self.assertTrue(hasattr(ext, f"cc{letter}_num"))
        self.assertFalse(hasattr(ext, "cce_num"))

    def test_mod_dest_class(self):
        self.assertEqual(M8External.MOD_DEST_ENUM_CLASS, M8ExternalModDest)


if __name__ == "__main__":
    unittest.main()
