"""Tests for the remapper reference walker.

Each test hand-builds a project with a known reference shape and asserts
the walker finds exactly the expected closure — no false positives, no
missed references.
"""
import unittest

from m8.api.chain import M8ChainStep
from m8.api.fx import M8FXTuple, M8MixerFX, M8SequenceFX
from m8.api.instruments.wavsynth import M8Wavsynth
from m8.api.phrase import M8Note, M8PhraseStep
from m8.api.project import M8Project
from m8.api.remapper import (
    EMPTY_CHAIN, EMPTY_INSTRUMENT_REF, EMPTY_PHRASE, NO_EQ,
    EQ_REF_FX_KEYS, INSTRUMENT_REF_FX_KEYS, TABLE_REF_FX_KEYS,
    Mappings, walk_dependencies, walk_song,
)


class TestReferenceFxKeyConstants(unittest.TestCase):
    """Sanity: the FX byte codes we track match the Rust spec."""

    def test_instrument_ref_keys(self):
        self.assertEqual(INSTRUMENT_REF_FX_KEYS, {0x43, 0x47})  # INS, NXT

    def test_table_ref_keys(self):
        self.assertEqual(TABLE_REF_FX_KEYS, {0x14, 0x17})  # TBL, TBX

    def test_eq_ref_keys(self):
        self.assertEqual(EQ_REF_FX_KEYS, {0x41, 0x42})  # EQM, EQI


class TestMappings(unittest.TestCase):
    def test_empty_mappings_is_falsy(self):
        m = Mappings()
        self.assertFalse(m)
        self.assertEqual(m.total(), 0)

    def test_total_sums_all_sets(self):
        m = Mappings(
            chains={1}, phrases={2, 3},
            instruments={4, 5, 6}, tables={7}, eqs={8, 9},
        )
        self.assertEqual(m.total(), 9)
        self.assertTrue(m)


class TestWalkFromChain(unittest.TestCase):
    """Chain → phrase → instrument → EQ traversal."""

    def setUp(self):
        self.project = M8Project.initialise()

    def test_chain_with_one_phrase_one_instrument(self):
        self.project.instruments[2] = M8Wavsynth(name="W2")
        self.project.instruments[2].associated_eq = 10

        self.project.phrases[7][0] = M8PhraseStep(
            note=M8Note.C_4, velocity=0x80, instrument=2,
        )
        self.project.chains[3][0] = M8ChainStep(phrase=7, transpose=0)

        m = walk_dependencies(self.project, chains={3})
        self.assertEqual(m.chains, {3})
        self.assertEqual(m.phrases, {7})
        self.assertEqual(m.instruments, {2})
        self.assertIn(10, m.eqs)

    def test_empty_phrase_in_chain_step_not_followed(self):
        """Phrase = 0xFF means empty — should not be walked."""
        self.project.chains[3][0] = M8ChainStep(phrase=EMPTY_PHRASE, transpose=0)
        m = walk_dependencies(self.project, chains={3})
        # The chain itself is touched, but no phrase
        self.assertEqual(m.chains, {3})
        self.assertEqual(m.phrases, set())

    def test_empty_chain_seed_skipped(self):
        m = walk_dependencies(self.project, chains={EMPTY_CHAIN})
        self.assertEqual(m.total(), 0)

    def test_two_phrases_same_instrument_deduplicated(self):
        """Same instrument referenced by multiple phrases — only listed once."""
        self.project.instruments[5] = M8Wavsynth(name="SHARED")
        self.project.phrases[1][0] = M8PhraseStep(note=M8Note.C_4, velocity=0x80, instrument=5)
        self.project.phrases[2][0] = M8PhraseStep(note=M8Note.D_4, velocity=0x80, instrument=5)
        self.project.chains[0][0] = M8ChainStep(phrase=1, transpose=0)
        self.project.chains[0][1] = M8ChainStep(phrase=2, transpose=0)

        m = walk_dependencies(self.project, chains={0})
        self.assertEqual(m.phrases, {1, 2})
        self.assertEqual(m.instruments, {5})

    def test_empty_instrument_ref_skipped(self):
        """Step.instrument == 0xFF — don't walk to instrument."""
        self.project.phrases[5][0] = M8PhraseStep(
            note=M8Note.C_4, velocity=0x80, instrument=EMPTY_INSTRUMENT_REF,
        )
        self.project.chains[0][0] = M8ChainStep(phrase=5, transpose=0)

        m = walk_dependencies(self.project, chains={0})
        self.assertEqual(m.instruments, set())

    def test_instrument_no_eq_assigned_skipped(self):
        """instrument.associated_eq == 0xFF — don't pull an EQ."""
        self.project.instruments[3] = M8Wavsynth(name="NOEQ")
        # default is 0xFF; do not set
        self.assertEqual(self.project.instruments[3].associated_eq, NO_EQ)

        self.project.phrases[1][0] = M8PhraseStep(note=M8Note.C_4, velocity=0x80, instrument=3)
        self.project.chains[0][0] = M8ChainStep(phrase=1, transpose=0)

        m = walk_dependencies(self.project, chains={0})
        self.assertEqual(m.instruments, {3})
        self.assertNotIn(NO_EQ, m.eqs)
        # Note: instrument N implicitly owns table N — that's expected and
        # tested separately. EQ assertion above is the focus.


class TestFxRefsInPhrases(unittest.TestCase):
    """Phrase FX commands that carry references (TBL, INS, EQM, etc.)."""

    def setUp(self):
        self.project = M8Project.initialise()

    def test_tbl_fx_pulls_table(self):
        self.project.phrases[1][0] = M8PhraseStep(note=M8Note.C_4, velocity=0x80, instrument=2)
        self.project.phrases[1][0].fx[0] = M8FXTuple(key=M8SequenceFX.TBL, value=42)
        self.project.chains[0][0] = M8ChainStep(phrase=1, transpose=0)

        m = walk_dependencies(self.project, chains={0})
        self.assertIn(42, m.tables)

    def test_tbx_fx_pulls_table(self):
        self.project.phrases[1][0] = M8PhraseStep(note=M8Note.C_4, velocity=0x80, instrument=2)
        self.project.phrases[1][0].fx[0] = M8FXTuple(key=M8SequenceFX.TBX, value=99)
        self.project.chains[0][0] = M8ChainStep(phrase=1, transpose=0)

        m = walk_dependencies(self.project, chains={0})
        self.assertIn(99, m.tables)

    def test_ins_fx_pulls_instrument(self):
        self.project.phrases[1][0] = M8PhraseStep(note=M8Note.C_4, velocity=0x80, instrument=0)
        self.project.phrases[1][0].fx[0] = M8FXTuple(key=M8MixerFX.INS, value=7)
        self.project.instruments[7] = M8Wavsynth(name="INS-REF")
        self.project.chains[0][0] = M8ChainStep(phrase=1, transpose=0)

        m = walk_dependencies(self.project, chains={0})
        self.assertIn(7, m.instruments)

    def test_eqm_fx_pulls_eq(self):
        self.project.phrases[1][0] = M8PhraseStep(note=M8Note.C_4, velocity=0x80, instrument=0)
        self.project.phrases[1][0].fx[0] = M8FXTuple(key=M8MixerFX.EQM, value=27)
        self.project.chains[0][0] = M8ChainStep(phrase=1, transpose=0)

        m = walk_dependencies(self.project, chains={0})
        self.assertIn(27, m.eqs)

    def test_non_reference_fx_ignored(self):
        """ARP and other non-tracking FX shouldn't pull anything beyond what
        the step's own instrument byte pulls."""
        # Use a real instrument so the implicit "instrument N owns table N"
        # rule fires (otherwise instrument 0 is an empty M8Block and gets
        # skipped, and there's nothing to assert about table tracking).
        self.project.instruments[0] = M8Wavsynth(name="W0")
        self.project.phrases[1][0] = M8PhraseStep(note=M8Note.C_4, velocity=0x80, instrument=0)
        self.project.phrases[1][0].fx[0] = M8FXTuple(key=M8SequenceFX.ARP, value=0x42)
        self.project.chains[0][0] = M8ChainStep(phrase=1, transpose=0)

        m = walk_dependencies(self.project, chains={0})
        # Instrument 0 pulled in via phrase step; ARP FX adds nothing.
        # Table 0 comes from the implicit instrument-0-owns-table-0 rule.
        self.assertEqual(m.instruments, {0})
        self.assertEqual(m.tables, {0})
        self.assertEqual(m.eqs, set())


class TestTableWalk(unittest.TestCase):
    """Tables can reference instruments / other tables / EQs via FX."""

    def setUp(self):
        self.project = M8Project.initialise()

    def test_table_fx_pulls_instrument(self):
        self.project.tables[12][0].fx[0] = M8FXTuple(key=M8MixerFX.INS, value=5)
        self.project.instruments[5] = M8Wavsynth(name="T-REF")

        m = walk_dependencies(self.project, tables={12})
        self.assertIn(5, m.instruments)
        self.assertIn(12, m.tables)

    def test_table_fx_pulls_eq(self):
        self.project.tables[12][3].fx[0] = M8FXTuple(key=M8MixerFX.EQI, value=18)

        m = walk_dependencies(self.project, tables={12})
        self.assertIn(18, m.eqs)

    def test_table_to_table_ref_walked(self):
        """Table A → Table B via TBL FX in A's steps."""
        self.project.tables[10][0].fx[0] = M8FXTuple(key=M8SequenceFX.TBL, value=20)

        m = walk_dependencies(self.project, tables={10})
        self.assertEqual(m.tables, {10, 20})

    def test_table_cycle_terminates(self):
        """Table A → Table B → Table A should terminate, not loop forever."""
        self.project.tables[10][0].fx[0] = M8FXTuple(key=M8SequenceFX.TBL, value=20)
        self.project.tables[20][0].fx[0] = M8FXTuple(key=M8SequenceFX.TBL, value=10)

        m = walk_dependencies(self.project, tables={10})
        self.assertEqual(m.tables, {10, 20})


class TestInstrumentOwnsTableConvention(unittest.TestCase):
    """Firmware 6+: instrument N implicitly owns table N (per-instrument
    modulation table)."""

    def setUp(self):
        self.project = M8Project.initialise()

    def test_touching_instrument_pulls_same_index_table(self):
        self.project.instruments[5] = M8Wavsynth(name="W5")
        m = walk_dependencies(self.project, instruments={5})
        self.assertIn(5, m.instruments)
        self.assertIn(5, m.tables)

    def test_instrument_table_can_recurse_through_fx(self):
        """Instrument 5's table (slot 5) has a TBL FX → table 100."""
        self.project.instruments[5] = M8Wavsynth(name="W5")
        self.project.tables[5][0].fx[0] = M8FXTuple(key=M8SequenceFX.TBL, value=100)

        m = walk_dependencies(self.project, instruments={5})
        self.assertIn(5, m.instruments)
        self.assertIn(5, m.tables)
        self.assertIn(100, m.tables)


class TestSeedMixing(unittest.TestCase):
    """Walker accepts seeds in multiple categories simultaneously."""

    def setUp(self):
        self.project = M8Project.initialise()

    def test_eq_seed(self):
        m = walk_dependencies(self.project, eqs={5, 10})
        self.assertEqual(m.eqs, {5, 10})
        # No other recursion — EQs are leaves
        self.assertEqual(m.chains, set())
        self.assertEqual(m.phrases, set())
        self.assertEqual(m.instruments, set())
        self.assertEqual(m.tables, set())

    def test_combined_seeds(self):
        self.project.instruments[3] = M8Wavsynth(name="I3")
        self.project.instruments[3].associated_eq = 8
        # Instrument 10 needs to be a real instrument for the walker to
        # accept it (empty M8Block slots are skipped).
        self.project.instruments[10] = M8Wavsynth(name="I10")

        self.project.phrases[5][0] = M8PhraseStep(
            note=M8Note.C_4, velocity=0x80, instrument=3,
        )
        self.project.chains[0][0] = M8ChainStep(phrase=5, transpose=0)

        m = walk_dependencies(
            self.project,
            chains={0},
            instruments={10},   # not reachable via chain 0
            eqs={20},
        )
        self.assertIn(0, m.chains)
        self.assertIn(5, m.phrases)
        self.assertIn(3, m.instruments)
        self.assertIn(10, m.instruments)  # from explicit seed
        self.assertIn(8, m.eqs)
        self.assertIn(20, m.eqs)


class TestWalkSong(unittest.TestCase):
    """walk_song() = walk_dependencies seeded from every populated cell of
    the song matrix."""

    def test_empty_template_walks_clean(self):
        p = M8Project.initialise()
        m = walk_song(p)
        # Template song matrix is all 0xFF — no chains touched
        self.assertEqual(m.chains, set())

    def test_song_seeds_from_matrix(self):
        p = M8Project.initialise()
        p.song[0][0] = 5
        p.song[3][2] = 10
        p.chains[5][0] = M8ChainStep(phrase=20, transpose=0)
        p.chains[10][0] = M8ChainStep(phrase=30, transpose=0)

        m = walk_song(p)
        self.assertEqual(m.chains, {5, 10})
        self.assertIn(20, m.phrases)
        self.assertIn(30, m.phrases)


class TestOutOfRangeRefsIgnored(unittest.TestCase):
    """Defensive: corrupt or unparsed-default reference values shouldn't
    crash the walker."""

    def setUp(self):
        self.project = M8Project.initialise()

    def test_fx_value_ge_n_instruments_for_ins_skipped(self):
        """Instrument index >= 128 isn't a real instrument slot."""
        self.project.phrases[1][0] = M8PhraseStep(note=M8Note.C_4, velocity=0x80, instrument=0)
        self.project.phrases[1][0].fx[0] = M8FXTuple(key=M8MixerFX.INS, value=200)
        self.project.chains[0][0] = M8ChainStep(phrase=1, transpose=0)

        m = walk_dependencies(self.project, chains={0})
        self.assertNotIn(200, m.instruments)

    def test_fx_value_ge_n_eqs_for_eqm_skipped(self):
        """EQ index >= 132 (v6 EQ count) isn't a real EQ."""
        self.project.phrases[1][0] = M8PhraseStep(note=M8Note.C_4, velocity=0x80, instrument=0)
        self.project.phrases[1][0].fx[0] = M8FXTuple(key=M8MixerFX.EQM, value=200)
        self.project.chains[0][0] = M8ChainStep(phrase=1, transpose=0)

        m = walk_dependencies(self.project, chains={0})
        self.assertNotIn(200, m.eqs)


if __name__ == "__main__":
    unittest.main()
