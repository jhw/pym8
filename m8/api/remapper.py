# m8/api/remapper.py
"""Cross-project reference walker and slot allocator.

Commit 1 (this file's original scope): walker — given seed slot IDs in
a source project, walk every reference field and FX-command-value
reference to compute the *full* set of slots that depend on the
selection. See `walk_dependencies` / `walk_song`.

Commit 2 (this section): allocator — given a `Mappings` (what to move)
and a destination project, produce a `Remapping` that maps each source
slot to a free destination slot. Find-next-free per kind with a "prefer
same index" optimization. See `allocate`.

The actual byte rewriting (apply the remapping by copying source state
into destination with refs rewritten) lives in a follow-up commit.

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


# ----------------------------------------------------------------------
# Allocator
# ----------------------------------------------------------------------

@dataclass
class Remapping:
    """Per-slot-kind {source_index → destination_index} mappings.

    For each section the source slot is the dict key and the destination
    slot is the value. Slot kinds not in a mapping are unaffected by the
    remapping.

    Tables in slots 0..N_INSTRUMENTS-1 piggyback on instrument allocation
    (firmware-6 "instrument N owns table N" convention): if instrument 5
    is mapped 5→8, then table 5 is mapped 5→8 too. Free-standing tables
    (index >= N_INSTRUMENTS, or tables in the move set whose matching
    instrument isn't being moved) get independent slot allocations.

    The `out_*` methods translate a source-side reference value: if the
    source slot is in the mapping, return the destination slot; otherwise
    return the source value unchanged (the reference is to something not
    being moved — caller is responsible for whether that's intentional).
    """

    chains: dict = field(default_factory=dict)
    phrases: dict = field(default_factory=dict)
    instruments: dict = field(default_factory=dict)
    tables: dict = field(default_factory=dict)
    eqs: dict = field(default_factory=dict)

    def out_chain(self, src):
        return self.chains.get(src, src)

    def out_phrase(self, src):
        return self.phrases.get(src, src)

    def out_instrument(self, src):
        return self.instruments.get(src, src)

    def out_table(self, src):
        return self.tables.get(src, src)

    def out_eq(self, src):
        return self.eqs.get(src, src)


class NoFreeSlotError(ValueError):
    """Destination project has no free slot of the required kind."""


def _chain_occupied(project, index):
    if not (0 <= index < len(project.chains)):
        return False
    return any(step.phrase != EMPTY_PHRASE for step in project.chains[index])


def _phrase_occupied(project, index):
    if not (0 <= index < len(project.phrases)):
        return False
    phrase = project.phrases[index]
    for step in phrase:
        if step.note != 0xFF or step.velocity != 0xFF or step.instrument != EMPTY_INSTRUMENT_REF:
            return True
        if any(fx.key != 0xFF for fx in step.fx):
            return True
    return False


def _instrument_occupied(project, index):
    if not (0 <= index < N_INSTRUMENTS):
        return False
    return _is_concrete_instrument(project, index)


def _table_occupied(project, index):
    if not (0 <= index < N_TABLES):
        return False
    return not project.tables[index].is_empty()


def _eq_occupied(project, index):
    if not (0 <= index < N_EQS):
        return False
    # On M8Project the collection is `.eq` (singular noun for the section).
    return not project.eq[index].is_default()


def _find_free_slot(occupied, capacity, preferred):
    """Try `preferred` first (if in range and free), then scan upward, then
    wrap from 0 to preferred. Returns None if all slots are full."""
    if 0 <= preferred < capacity and not occupied[preferred]:
        return preferred
    for i in range(capacity):
        if not occupied[i]:
            return i
    return None


def allocate(source, destination, mappings: Mappings) -> Remapping:
    """Allocate destination slots for everything in `mappings`.

    For each source slot the allocator first tries the same index in the
    destination (so chain 3 → chain 3 if possible). If that slot is
    occupied, it scans upward for the first free slot. Raises
    NoFreeSlotError if no free slot is available for some kind.

    Instrument → table piggybacking (instrument N owns table N) is
    applied: tables in `mappings.tables` whose index matches an entry in
    `mappings.instruments` map to the same destination index as the
    instrument. Free-standing tables get independent allocations.
    """
    remap = Remapping()

    # Snapshot destination occupancy. Allocations during this pass update
    # the local snapshots, not the project — caller commits via apply (next
    # commit).
    n_chains = len(destination.chains)
    n_phrases = len(destination.phrases)

    chains_taken = [_chain_occupied(destination, i) for i in range(n_chains)]
    phrases_taken = [_phrase_occupied(destination, i) for i in range(n_phrases)]
    instruments_taken = [_instrument_occupied(destination, i) for i in range(N_INSTRUMENTS)]
    tables_taken = [_table_occupied(destination, i) for i in range(N_TABLES)]
    eqs_taken = [_eq_occupied(destination, i) for i in range(N_EQS)]

    def allocate_one(kind, src_index, taken, capacity):
        dest = _find_free_slot(taken, capacity, preferred=src_index)
        if dest is None:
            raise NoFreeSlotError(
                f"No free {kind} slot in destination for source {kind} {src_index}"
            )
        taken[dest] = True
        return dest

    # Order matters: instruments first because tables 0..127 piggyback.
    for src in sorted(mappings.instruments):
        remap.instruments[src] = allocate_one("instrument", src, instruments_taken, N_INSTRUMENTS)
        # Implicit instrument-N-owns-table-N: if table src is also in the
        # move set, piggyback its allocation onto the instrument's.
        if src in mappings.tables and src < N_INSTRUMENTS:
            remap.tables[src] = remap.instruments[src]
            # If the chosen destination slot's table is occupied, we still
            # need to overwrite it (the implicit ownership rule says
            # touching the instrument touches its table). Mark it taken so
            # later free-standing-table allocation doesn't pick it.
            tables_taken[remap.instruments[src]] = True

    # Free-standing tables: anything in mappings.tables not already
    # piggybacked.
    for src in sorted(mappings.tables):
        if src in remap.tables:
            continue
        remap.tables[src] = allocate_one("table", src, tables_taken, N_TABLES)

    for src in sorted(mappings.eqs):
        remap.eqs[src] = allocate_one("eq", src, eqs_taken, N_EQS)

    for src in sorted(mappings.phrases):
        remap.phrases[src] = allocate_one("phrase", src, phrases_taken, n_phrases)

    for src in sorted(mappings.chains):
        remap.chains[src] = allocate_one("chain", src, chains_taken, n_chains)

    return remap


# ----------------------------------------------------------------------
# Apply
# ----------------------------------------------------------------------

def _rewrite_fx_tuples(fx_tuples, remap: Remapping):
    """Rewrite reference-bearing FX values via the remapping.

    Mutates each tuple in place. Non-reference FX commands are left
    alone. Reference values that aren't in the remap (i.e., the target
    slot isn't being moved) are also left alone — the caller chose not
    to move it, so the reference stays pointing at whatever the
    destination has at that slot.
    """
    for tup in fx_tuples:
        key = tup.key
        if key in INSTRUMENT_REF_FX_KEYS:
            tup.value = remap.out_instrument(tup.value)
        elif key in TABLE_REF_FX_KEYS:
            tup.value = remap.out_table(tup.value)
        elif key in EQ_REF_FX_KEYS:
            tup.value = remap.out_eq(tup.value)


def apply(source, destination, mappings: Mappings, remap: Remapping) -> None:
    """Copy mapped source slots into destination, rewriting references.

    Mutates `destination` in place. `source` is read but never modified
    (every moved object is cloned before writing into destination).

    For each kind in `mappings`, copies the source slot's content to its
    destination index per `remap`, rewriting inline references:

    - chain step .phrase → remap.out_phrase(value)
    - phrase step .instrument → remap.out_instrument(value)
    - phrase / table step FX value (when key is a reference FX) →
      remap.out_X(value) where X depends on the FX key
    - instrument .associated_eq → remap.out_eq(value)

    The song matrix is NOT touched. Callers wanting to play the moved
    chain in destination should place it after apply:

        remap = allocate(src, dst, walk_dependencies(src, chains={3}))
        apply(src, dst, mappings, remap)
        dst.song[0][0] = remap.out_chain(3)
    """
    # EQs first — they have no internal references, and instruments will
    # need them already in place to verify associated_eq remapping is
    # consistent (though for now we don't actually verify).
    for src_eq, dst_eq in remap.eqs.items():
        destination.eq[dst_eq] = source.eq[src_eq].clone()

    # Tables — rewrite FX refs in each step
    for src_table, dst_table in remap.tables.items():
        cloned = source.tables[src_table].clone()
        for step in cloned:
            _rewrite_fx_tuples(step.fx, remap)
        destination.tables[dst_table] = cloned

    # Instruments — rewrite associated_eq
    for src_inst, dst_inst in remap.instruments.items():
        cloned = source.instruments[src_inst].clone()
        # M8Block instances (empty slots) have no associated_eq and were
        # filtered out at walk time, but be defensive.
        if hasattr(cloned, "associated_eq") and cloned.associated_eq != NO_EQ:
            cloned.associated_eq = remap.out_eq(cloned.associated_eq)
        destination.instruments[dst_inst] = cloned

    # Phrases — rewrite step.instrument and FX refs
    for src_phrase, dst_phrase in remap.phrases.items():
        cloned = source.phrases[src_phrase].clone()
        for step in cloned:
            if step.instrument != EMPTY_INSTRUMENT_REF:
                step.instrument = remap.out_instrument(step.instrument)
            _rewrite_fx_tuples(step.fx, remap)
        destination.phrases[dst_phrase] = cloned

    # Chains — rewrite step.phrase
    for src_chain, dst_chain in remap.chains.items():
        cloned = source.chains[src_chain].clone()
        for step in cloned:
            if step.phrase != EMPTY_PHRASE:
                step.phrase = remap.out_phrase(step.phrase)
        destination.chains[dst_chain] = cloned


def move_chains(source, destination, chain_indices) -> Remapping:
    """Convenience: walk + allocate + apply for a set of source chains.

    Returns the Remapping so callers can wire up destination.song with
    `remap.out_chain(src_chain)` after the move.
    """
    mappings = walk_dependencies(source, chains=set(chain_indices))
    remap = allocate(source, destination, mappings)
    apply(source, destination, mappings, remap)
    return remap
