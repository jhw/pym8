# m8/api/remapper.py
"""Cross-project reference walker (Phase 1 of remapper).

Given a starting set of slot IDs in a source project, walk every
reference field and FX-command-value reference to compute the *full*
set of slots that need to be carried along when copying that selection
into another project.

This module only computes the dependency closure. Slot allocation in
the destination and the actual byte rewriting live in the follow-up
commits.

Reference inventory (matches m8-file-parser/src/remapper.rs):

    chain.step.phrase                → phrase index
    phrase.step.instrument           → instrument index
    phrase.step.fx[j] when key in    → various, see below
        INSTRUMENT_REF_FX_KEYS
        TABLE_REF_FX_KEYS
        EQ_REF_FX_KEYS
    table.step.fx[j]                 → same as phrase FX
    instrument.associated_eq         → EQ index

FX commands that carry a reference in their value byte:

    SequenceFX.TBL (0x14), TBX (0x17)           → table index
    MixerFX.EQM   (0x41), EQI (0x42)            → EQ index
    MixerFX.INS   (0x43), NXT (0x47)            → instrument index

Implicit reference (firmware 6.0+): instrument slot N has an
"instrument table" at table slot N. Touching instrument N → touch
table N (which may further reference tables/instruments via FX).
"""
from dataclasses import dataclass, field
from typing import Iterable, Optional

from m8.api.fx import M8MixerFX, M8SequenceFX
from m8.api.instrument import BLOCK_COUNT as N_INSTRUMENTS, M8InstrumentType
from m8.api.table import TABLE_COUNT as N_TABLES
from m8.api.eq import EQ_COUNT as N_EQS


# Sentinel values for "no reference" in each slot kind.
EMPTY_PHRASE = 0xFF
EMPTY_CHAIN = 0xFF
EMPTY_INSTRUMENT_REF = 0xFF
NO_EQ = 0xFF

# FX keys whose value byte is a reference into another section.
INSTRUMENT_REF_FX_KEYS = frozenset({int(M8MixerFX.INS), int(M8MixerFX.NXT)})
TABLE_REF_FX_KEYS = frozenset({int(M8SequenceFX.TBL), int(M8SequenceFX.TBX)})
EQ_REF_FX_KEYS = frozenset({int(M8MixerFX.EQM), int(M8MixerFX.EQI)})


@dataclass
class Mappings:
    """Closure of source-project slot indices touched by a walk.

    Each set holds *source-project* slot indices (0-based). To turn these
    into a destination remapping you'd allocate free slots in the
    destination — that's what the next commit does.
    """

    chains: set = field(default_factory=set)
    phrases: set = field(default_factory=set)
    instruments: set = field(default_factory=set)
    tables: set = field(default_factory=set)
    eqs: set = field(default_factory=set)

    def total(self):
        return (
            len(self.chains) + len(self.phrases) + len(self.instruments)
            + len(self.tables) + len(self.eqs)
        )

    def __bool__(self):
        return self.total() > 0


def _is_concrete_instrument(project, instrument_index):
    """A populated instrument slot, not an M8Block / empty slot."""
    if not (0 <= instrument_index < N_INSTRUMENTS):
        return False
    inst = project.instruments[instrument_index]
    # M8Block has no associated_eq; real instruments do (the descriptor
    # is on the base class).
    return hasattr(inst, "associated_eq")


def _walk_fx(step_fx, mappings, queue_instruments, queue_tables):
    """Walk a step's three FX slots, adding any references to the queues
    (and EQ refs straight into mappings — EQs are leaves)."""
    for tup in step_fx:
        key = tup.key
        value = tup.value
        if key in INSTRUMENT_REF_FX_KEYS:
            if 0 <= value < N_INSTRUMENTS:
                queue_instruments.add(value)
        elif key in TABLE_REF_FX_KEYS:
            if 0 <= value < N_TABLES:
                queue_tables.add(value)
        elif key in EQ_REF_FX_KEYS:
            if 0 <= value < N_EQS:
                mappings.eqs.add(value)


def walk_dependencies(
    project,
    *,
    chains: Optional[Iterable[int]] = None,
    instruments: Optional[Iterable[int]] = None,
    tables: Optional[Iterable[int]] = None,
    eqs: Optional[Iterable[int]] = None,
) -> Mappings:
    """Compute the dependency closure for the given seed slots.

    Walks chain → phrase → instrument → eq, with phrase/table FX commands
    contributing extra instrument/table/EQ references. Cycles in table
    references (table A → table B → table A) are handled via visited
    tracking. The firmware-6.0 convention "instrument N implicitly owns
    table N" is modelled: touching instrument N enqueues table N.

    Arguments are seed sets. All four can be supplied; the walker treats
    them as a union.
    """
    m = Mappings()

    queue_chains = set(chains or ())
    queue_phrases = set()
    queue_instruments = set(instruments or ())
    queue_tables = set(tables or ())

    # Seed EQs go straight into mappings — there's nothing to recurse
    # through (EQs reference nothing else).
    for e in (eqs or ()):
        if 0 <= e < N_EQS:
            m.eqs.add(e)

    while queue_chains or queue_phrases or queue_instruments or queue_tables:
        # Walk chains first to expose their phrases
        if queue_chains:
            c = queue_chains.pop()
            if c == EMPTY_CHAIN or c in m.chains or not (0 <= c < 255):
                continue
            m.chains.add(c)
            for step in project.chains[c]:
                if step.phrase != EMPTY_PHRASE:
                    queue_phrases.add(step.phrase)
            continue

        # Then phrases — note + instrument refs + FX
        if queue_phrases:
            p = queue_phrases.pop()
            if p == EMPTY_PHRASE or p in m.phrases or not (0 <= p < 255):
                continue
            m.phrases.add(p)
            for step in project.phrases[p]:
                if step.instrument != EMPTY_INSTRUMENT_REF and 0 <= step.instrument < N_INSTRUMENTS:
                    queue_instruments.add(step.instrument)
                _walk_fx(step.fx, m, queue_instruments, queue_tables)
            continue

        # Then instruments — pulls associated_eq + implicit table N
        if queue_instruments:
            i = queue_instruments.pop()
            if i in m.instruments or not _is_concrete_instrument(project, i):
                continue
            m.instruments.add(i)
            inst = project.instruments[i]
            if inst.associated_eq != NO_EQ and 0 <= inst.associated_eq < N_EQS:
                m.eqs.add(inst.associated_eq)
            # Firmware-6+ convention: instrument N owns table N.
            # Enqueue (may already be a default-empty table — walker
            # still tracks it as "touched").
            queue_tables.add(i)
            continue

        # Then tables — FX refs (instruments / tables / EQs)
        if queue_tables:
            t = queue_tables.pop()
            if t in m.tables or not (0 <= t < N_TABLES):
                continue
            m.tables.add(t)
            for step in project.tables[t]:
                _walk_fx(step.fx, m, queue_instruments, queue_tables)
            continue

    return m


def walk_song(project) -> Mappings:
    """Convenience: compute dependencies for everything reachable from the
    song matrix (i.e. the entire playable set of the project)."""
    chain_seeds = set()
    for row in project.song:
        for slot in row:
            if slot != EMPTY_CHAIN:
                chain_seeds.add(slot)
    return walk_dependencies(project, chains=chain_seeds)
