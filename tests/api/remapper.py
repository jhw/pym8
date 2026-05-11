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
    Mappings, NoFreeSlotError, Remapper, Remapping,
    allocate, apply, move_chains, walk_dependencies, walk_song,
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


# ----------------------------------------------------------------------
# Allocator
# ----------------------------------------------------------------------

class TestAllocatorPreferSameIndex(unittest.TestCase):
    """When a destination slot at the source index is free, keep that index."""

    def test_empty_destination_keeps_indices(self):
        src = M8Project.initialise()
        src.instruments[5] = M8Wavsynth(name="W5")
        src.instruments[5].associated_eq = 10
        src.phrases[7][0] = M8PhraseStep(note=M8Note.C_4, velocity=0x80, instrument=5)
        src.chains[3][0] = M8ChainStep(phrase=7, transpose=0)

        dst = M8Project.initialise()  # all empty
        m = walk_dependencies(src, chains={3})
        remap = allocate(src, dst, m)

        self.assertEqual(remap.chains, {3: 3})
        self.assertEqual(remap.phrases, {7: 7})
        self.assertEqual(remap.instruments, {5: 5})
        # Implicit table 5 piggybacks on instrument 5
        self.assertEqual(remap.tables, {5: 5})
        self.assertEqual(remap.eqs, {10: 10})


class TestAllocatorFindsAlternateOnCollision(unittest.TestCase):
    """Each colliding slot moves to the next free slot."""

    def test_chain_collision_finds_alternate(self):
        src = M8Project.initialise()
        src.chains[3][0] = M8ChainStep(phrase=EMPTY_PHRASE, transpose=0)
        src.chains[3][1] = M8ChainStep(phrase=EMPTY_PHRASE, transpose=0)
        # Actually we need an occupied step. Set step 0 phrase to something:
        src.chains[3][0].phrase = 0
        src.phrases[0][0] = M8PhraseStep(note=M8Note.C_4, velocity=0x80, instrument=EMPTY_INSTRUMENT_REF)

        dst = M8Project.initialise()
        dst.chains[3][0] = M8ChainStep(phrase=99, transpose=0)  # occupies slot 3

        m = walk_dependencies(src, chains={3})
        remap = allocate(src, dst, m)
        self.assertNotEqual(remap.chains[3], 3)
        self.assertEqual(remap.chains[3], 0)  # first free slot (0)

    def test_instrument_collision_finds_alternate(self):
        src = M8Project.initialise()
        src.instruments[2] = M8Wavsynth(name="SRC")

        dst = M8Project.initialise()
        dst.instruments[2] = M8Wavsynth(name="DST")  # collision

        m = Mappings(instruments={2})
        remap = allocate(src, dst, m)
        self.assertNotEqual(remap.instruments[2], 2)
        # First free instrument slot is 0
        self.assertEqual(remap.instruments[2], 0)

    def test_eq_collision_finds_alternate(self):
        """A non-default EQ in destination's slot 5 makes source EQ 5 relocate."""
        src = M8Project.initialise()
        dst = M8Project.initialise()
        dst.eqs[5].low.q = 0xAB  # mark as occupied (not default)

        m = Mappings(eqs={5})
        remap = allocate(src, dst, m)
        self.assertNotEqual(remap.eqs[5], 5)


class TestAllocatorPiggyback(unittest.TestCase):
    """instrument N owning table N: when both are in move set, they get
    the same destination slot."""

    def test_instrument_and_owned_table_share_destination(self):
        src = M8Project.initialise()
        src.instruments[7] = M8Wavsynth(name="W7")
        # Owned table at slot 7 has some content
        src.tables[7][0].transpose = 0x0C

        dst = M8Project.initialise()
        dst.instruments[7] = M8Wavsynth(name="DST-7")  # collision

        m = walk_dependencies(src, instruments={7})
        remap = allocate(src, dst, m)
        # Both instrument and table 7 should land at the same alternate slot
        self.assertIn(7, remap.instruments)
        self.assertIn(7, remap.tables)
        self.assertEqual(remap.instruments[7], remap.tables[7])

    def test_freestanding_table_allocated_independently(self):
        """Table >= N_INSTRUMENTS doesn't piggyback on anything."""
        src = M8Project.initialise()
        src.tables[200][0].transpose = 5

        dst = M8Project.initialise()
        dst.tables[200][0].transpose = 9  # collision

        m = walk_dependencies(src, tables={200})
        remap = allocate(src, dst, m)
        self.assertIn(200, remap.tables)
        self.assertNotEqual(remap.tables[200], 200)


class TestAllocatorMultiCollision(unittest.TestCase):
    """A bunch of source slots colliding with a partially-full destination."""

    def test_multiple_instruments_fall_through_to_free_slots(self):
        src = M8Project.initialise()
        for i in (0, 1, 2):
            src.instruments[i] = M8Wavsynth(name=f"S{i}")

        dst = M8Project.initialise()
        # Destination has slots 0, 1, 2 taken; 3, 4, 5 free
        for i in (0, 1, 2):
            dst.instruments[i] = M8Wavsynth(name=f"D{i}")

        m = Mappings(instruments={0, 1, 2})
        remap = allocate(src, dst, m)

        # No two source instruments map to the same dest slot
        dst_slots = set(remap.instruments.values())
        self.assertEqual(len(dst_slots), 3)
        # All in the free range
        for v in dst_slots:
            self.assertNotIn(v, (0, 1, 2))


class TestAllocatorExhaustion(unittest.TestCase):
    """If the destination has no free slot of some kind, raise."""

    def test_no_free_eq_raises(self):
        src = M8Project.initialise()
        dst = M8Project.initialise()
        # Fill every dst EQ slot with non-default state
        for eq in dst.eqs:
            eq.low.q = 0xAB

        m = Mappings(eqs={0})
        with self.assertRaises(NoFreeSlotError):
            allocate(src, dst, m)


class TestRemappingDataclass(unittest.TestCase):
    def test_empty_remapping(self):
        r = Remapping()
        self.assertEqual(r.chains, {})
        self.assertEqual(r.phrases, {})
        self.assertEqual(r.instruments, {})
        self.assertEqual(r.tables, {})
        self.assertEqual(r.eqs, {})

    def test_out_returns_mapped_value(self):
        r = Remapping(chains={3: 7}, phrases={1: 5})
        self.assertEqual(r.out_chain(3), 7)
        self.assertEqual(r.out_phrase(1), 5)

    def test_out_passes_unmapped_through(self):
        """References to slots not in the move set are preserved literally."""
        r = Remapping(chains={3: 7})
        self.assertEqual(r.out_chain(99), 99)
        self.assertEqual(r.out_instrument(5), 5)


# ----------------------------------------------------------------------
# Apply
# ----------------------------------------------------------------------

class TestApplyEndToEnd(unittest.TestCase):
    """Walker + allocator + apply: move chain N from src to dst."""

    def _build_src_with_chain_3(self):
        """Chain 3 → phrase 7 → instrument 5 (with EQ 10) and a TBL FX to
        table 99, plus an INS FX referencing instrument 5 itself."""
        src = M8Project.initialise()
        src.instruments[5] = M8Wavsynth(name="BASS")
        src.instruments[5].cutoff = 0xA0
        src.instruments[5].associated_eq = 10
        src.eqs[10].low.q = 0xAB  # marker we'll verify in destination

        src.phrases[7][0] = M8PhraseStep(
            note=M8Note.C_4, velocity=0x80, instrument=5,
        )
        src.phrases[7][4] = M8PhraseStep(
            note=M8Note.E_4, velocity=0x80, instrument=5,
        )
        src.phrases[7][4].fx[0] = M8FXTuple(key=M8SequenceFX.TBL, value=99)
        src.phrases[7][4].fx[1] = M8FXTuple(key=M8MixerFX.INS, value=5)
        src.tables[99][0].transpose = 0x0C

        src.chains[3][0] = M8ChainStep(phrase=7, transpose=0)
        return src

    def test_chain_with_phrase_lands_at_remap_slot(self):
        src = self._build_src_with_chain_3()
        dst = M8Project.initialise()
        remap = move_chains(src, dst, {3})

        dst_chain = dst.chains[remap.out_chain(3)]
        # Chain step's phrase reference rewritten
        self.assertEqual(dst_chain[0].phrase, remap.out_phrase(7))

    def test_instrument_copied_with_eq_ref_rewritten(self):
        src = self._build_src_with_chain_3()
        dst = M8Project.initialise()
        remap = move_chains(src, dst, {3})

        dst_inst = dst.instruments[remap.out_instrument(5)]
        # Instrument bytes copied
        self.assertEqual(dst_inst.name, "BASS")
        self.assertEqual(dst_inst.cutoff, 0xA0)
        # associated_eq rewritten to point at the new EQ slot
        self.assertEqual(dst_inst.associated_eq, remap.out_eq(10))

    def test_eq_content_traveled(self):
        src = self._build_src_with_chain_3()
        dst = M8Project.initialise()
        remap = move_chains(src, dst, {3})

        dst_eq = dst.eqs[remap.out_eq(10)]
        self.assertEqual(dst_eq.low.q, 0xAB)

    def test_phrase_step_instrument_rewritten(self):
        src = self._build_src_with_chain_3()
        dst = M8Project.initialise()
        remap = move_chains(src, dst, {3})

        dst_phrase = dst.phrases[remap.out_phrase(7)]
        self.assertEqual(dst_phrase[0].instrument, remap.out_instrument(5))
        self.assertEqual(dst_phrase[4].instrument, remap.out_instrument(5))

    def test_phrase_fx_references_rewritten(self):
        """TBL FX value → new table slot; INS FX value → new instrument slot."""
        src = self._build_src_with_chain_3()
        dst = M8Project.initialise()
        remap = move_chains(src, dst, {3})

        dst_phrase = dst.phrases[remap.out_phrase(7)]
        # TBL FX value should now point at table 99's destination slot
        self.assertEqual(dst_phrase[4].fx[0].key, int(M8SequenceFX.TBL))
        self.assertEqual(dst_phrase[4].fx[0].value, remap.out_table(99))
        # INS FX value should now point at instrument 5's destination slot
        self.assertEqual(dst_phrase[4].fx[1].key, int(M8MixerFX.INS))
        self.assertEqual(dst_phrase[4].fx[1].value, remap.out_instrument(5))

    def test_table_content_traveled(self):
        src = self._build_src_with_chain_3()
        dst = M8Project.initialise()
        remap = move_chains(src, dst, {3})

        dst_table = dst.tables[remap.out_table(99)]
        self.assertEqual(dst_table[0].transpose, 0x0C)


class TestApplyDoesNotMutateSource(unittest.TestCase):
    def test_source_chains_unchanged(self):
        src = M8Project.initialise()
        src.instruments[5] = M8Wavsynth(name="X")
        src.phrases[7][0] = M8PhraseStep(note=M8Note.C_4, velocity=0x80, instrument=5)
        src.chains[3][0] = M8ChainStep(phrase=7, transpose=0)

        dst = M8Project.initialise()
        # Force a collision so source-vs-dest indices differ
        dst.chains[3][0] = M8ChainStep(phrase=99, transpose=0)
        dst.instruments[5] = M8Wavsynth(name="OTHER")

        move_chains(src, dst, {3})

        # Source slots still pristine
        self.assertEqual(src.chains[3][0].phrase, 7)
        self.assertEqual(src.phrases[7][0].instrument, 5)
        self.assertEqual(src.instruments[5].name, "X")


class TestApplyPreservesUnmappedReferences(unittest.TestCase):
    """If a reference value points to a slot not in the move set, leave it
    literal — the user chose not to bring that slot along."""

    def test_phrase_instrument_outside_move_set_kept_literal(self):
        src = M8Project.initialise()
        # Chain → phrase, but the phrase references instrument 99 which we
        # never set up; the user is consciously importing without it.
        src.phrases[5][0] = M8PhraseStep(note=M8Note.C_4, velocity=0x80, instrument=99)
        src.chains[3][0] = M8ChainStep(phrase=5, transpose=0)

        dst = M8Project.initialise()
        remap = move_chains(src, dst, {3})

        dst_phrase = dst.phrases[remap.out_phrase(5)]
        # Instrument 99 isn't in remap.instruments; reference stays at 99
        self.assertEqual(dst_phrase[0].instrument, 99)
        self.assertNotIn(99, remap.instruments)


class TestApplyStableRoundTrip(unittest.TestCase):
    def test_destination_writes_consistently_after_apply(self):
        src = M8Project.initialise()
        src.instruments[5] = M8Wavsynth(name="W")
        src.instruments[5].associated_eq = 7
        src.phrases[10][0] = M8PhraseStep(note=M8Note.C_4, velocity=0x80, instrument=5)
        src.chains[2][0] = M8ChainStep(phrase=10, transpose=0)

        dst = M8Project.initialise()
        move_chains(src, dst, {2})

        b1 = dst.write()
        b2 = M8Project.read(b1).write()
        self.assertEqual(b1, b2)


class TestRemapperClass(unittest.TestCase):
    """The inspectable wrapper around walk + allocate + apply."""

    def _build_src(self):
        p = M8Project.initialise()
        p.instruments[5] = M8Wavsynth(name="W")
        p.phrases[10][0] = M8PhraseStep(note=M8Note.C_4, velocity=0x80, instrument=5)
        p.chains[2][0] = M8ChainStep(phrase=10, transpose=0)
        return p

    def test_constructor_runs_walk_and_allocate_eagerly(self):
        src = self._build_src()
        dst = M8Project.initialise()
        r = Remapper(src, dst, chains={2})
        # Mappings + remap computed without applying yet
        self.assertIn(2, r.mappings.chains)
        self.assertIn(2, r.remap.chains)

    def test_constructor_does_not_apply(self):
        """Inspecting Remapper before .apply() shouldn't mutate destination."""
        src = self._build_src()
        dst = M8Project.initialise()
        Remapper(src, dst, chains={2})
        # dst.chains[2] is still the template default (empty)
        self.assertEqual(dst.chains[2][0].phrase, 0xFF)
        # dst.instruments[5] is still empty
        from m8.api import M8Block
        self.assertIsInstance(dst.instruments[5], M8Block)

    def test_apply_commits(self):
        src = self._build_src()
        dst = M8Project.initialise()
        r = Remapper(src, dst, chains={2})
        r.apply()
        dst_chain = dst.chains[r.remap.out_chain(2)]
        self.assertEqual(dst_chain[0].phrase, r.remap.out_phrase(10))

    def test_seed_kwargs_supported(self):
        """Remapper accepts the same seed kwargs as walk_dependencies."""
        src = self._build_src()
        dst = M8Project.initialise()
        # Move just the instrument, not the chain
        r = Remapper(src, dst, instruments={5})
        self.assertIn(5, r.remap.instruments)
        # Chains/phrases are not in the mapping because we didn't seed them
        self.assertEqual(r.remap.chains, {})
        self.assertEqual(r.remap.phrases, {})


class TestApplyCallerWiresSongMatrix(unittest.TestCase):
    """apply doesn't touch destination.song — caller does it via remap.out_chain."""

    def test_song_matrix_untouched_by_apply(self):
        src = M8Project.initialise()
        src.instruments[5] = M8Wavsynth(name="X")
        src.phrases[10][0] = M8PhraseStep(note=M8Note.C_4, velocity=0x80, instrument=5)
        src.chains[2][0] = M8ChainStep(phrase=10, transpose=0)
        # Source has chain 2 placed at song[5][3]
        src.song[5][3] = 2

        dst = M8Project.initialise()
        dst.song[0][0] = 99  # whatever existing content
        remap = move_chains(src, dst, {2})

        # Destination's song matrix is unchanged (still 0xFF / its previous values)
        self.assertEqual(dst.song[0][0], 99)
        # Caller wires up via remap.out_chain
        dst.song[5][3] = remap.out_chain(2)
        self.assertEqual(dst.song[5][3], remap.out_chain(2))


if __name__ == "__main__":
    unittest.main()
