#!/usr/bin/env python3
"""Demo: normalise a project's own chain/phrase/instrument numbering.

remapper.py's Remapper/apply() moves slots *between* two projects. This
demo is the intra-project counterpart: reindex a single project's own
chains/phrases/instruments to a tidy scheme, using renumber() (the
same-project-safe primitive) plus the song matrix as the source of truth
for what's actually in use.

The scheme here (one of many you could build on the same primitives):
  - Each song column gets a dedicated 16-slot chain/phrase block:
    column N's chains and phrases live at 16*N .. 16*N+15.
  - Instruments compact into a single global pool starting at slot 0,
    in first-referenced order (instruments aren't column-specific — the
    same instrument could in principle appear in more than one column).

Placement policy like this isn't something pym8 bakes into the library —
build_column_scheme() below is demo code you'd adapt, not public API.
`renumber()` is the only part of this that's a library guarantee (safe
even if your own scheme happens to produce a cyclic remap).

Note on the M8 "0xFE = deliberately silent phrase" convention some
device-authored files show in unused chain steps: this demo does not
model it. It isn't documented in m8-file-parser's Rust reference (the
authoritative source for pym8's binary layout — see CLAUDE.md), so
there's nothing to verify it against; unused steps are left at the
ordinary EMPTY_PHRASE (0xFF) pym8 already uses everywhere.

Output: tmp/demos/normalise_song/NORMALISED.m8s
"""
from pathlib import Path

from m8.api.chain import M8Chain, M8ChainStep, EMPTY_PHRASE
from m8.api.instrument import M8Instruments
from m8.api.instruments.wavsynth import M8Wavsynth, M8WavShape
from m8.api.modulator import M8AHDModulator
from m8.api.phrase import M8Note, M8Phrase, M8PhraseStep, EMPTY_INSTRUMENT
from m8.api.project import M8Project
from m8.api.remapper import Remapping, renumber
from m8.api.song import EMPTY_CHAIN, COL_COUNT


PROJECT_NAME = "NORMALISED"
OUTPUT_DIR = Path("tmp/demos/normalise_song")
BPM = 128
SLOTS_PER_COLUMN = 16


def build_messy_project():
    """A project that plays fine but whose slot numbering has no
    structure — as if it grew organically over an editing session:
    instruments, phrases, and chains scattered across whatever index
    happened to be free at the time.

    Layout (by column):
      col 0 (drums): chain 90 (main, rows 0-6) + chain 45 (fill, row 7)
                      -> phrase 150 (main) + phrase 12 (fill)
                      -> instruments 77 (KICK), 3 (SNARE)
      col 1 (bass):   chain 61 (rows 0-7) -> phrase 33 -> instrument 5 (BASS)
      col 2 (lead):   chain 199 (rows 0-7) -> phrase 210 -> instrument 101 (LEAD)
    """
    p = M8Project.initialise()
    p.metadata.name = "MESSY"
    p.metadata.tempo = BPM

    kick = M8Wavsynth(name="KICK")
    kick.shape = M8WavShape.PULSE50
    kick.pitch = 0x18
    kick.cutoff = 0xC0
    kick.modulators[0] = M8AHDModulator(destination=1, amount=0xFF, attack=0x00, hold=0x00, decay=0x18)
    p.instruments[77] = kick

    snare = M8Wavsynth(name="SNARE")
    snare.shape = M8WavShape.NOISE
    snare.cutoff = 0x80
    snare.modulators[0] = M8AHDModulator(destination=1, amount=0xFF, attack=0x00, hold=0x00, decay=0x28)
    p.instruments[3] = snare

    bass = M8Wavsynth(name="BASS")
    bass.shape = M8WavShape.SAW
    bass.cutoff = 0x70
    bass.resonance = 0x60
    p.instruments[5] = bass

    lead = M8Wavsynth(name="LEAD")
    lead.shape = M8WavShape.TRIANGLE
    lead.cutoff = 0xA0
    lead.pan = 0x80
    p.instruments[101] = lead

    # Drums — main groove + a fill for the last row of the pattern
    main_drum_phrase = p.phrases[150]
    for step in (0, 4, 8, 12):
        main_drum_phrase[step] = M8PhraseStep(note=M8Note.C_4, velocity=0x7F, instrument=77)
    for step in (4, 12):
        main_drum_phrase[step] = M8PhraseStep(note=M8Note.E_4, velocity=0x7F, instrument=3)

    fill_drum_phrase = p.phrases[12]
    for step in (0, 2, 4, 6, 8, 10, 12, 14):
        fill_drum_phrase[step] = M8PhraseStep(note=M8Note.C_4, velocity=0x7F, instrument=77)
    for step in (1, 3, 5, 7, 9, 11, 13, 15):
        fill_drum_phrase[step] = M8PhraseStep(note=M8Note.E_4, velocity=0x60, instrument=3)

    p.chains[90][0] = M8ChainStep(phrase=150, transpose=0)
    p.chains[45][0] = M8ChainStep(phrase=12, transpose=0)

    # Bass — simple root-fifth line
    bass_phrase = p.phrases[33]
    for step, note in ((0, M8Note.C_2), (4, M8Note.C_2), (8, M8Note.GS_2), (12, M8Note.C_2)):
        bass_phrase[step] = M8PhraseStep(note=note, velocity=0x7F, instrument=5)
    p.chains[61][0] = M8ChainStep(phrase=33, transpose=0)

    # Lead — a short melodic hook
    lead_phrase = p.phrases[210]
    for step, note in ((0, M8Note.E_4), (4, M8Note.G_4), (8, M8Note.C_5), (12, M8Note.G_4)):
        lead_phrase[step] = M8PhraseStep(note=note, velocity=0x6F, instrument=101)
    p.chains[199][0] = M8ChainStep(phrase=210, transpose=0)

    for row in range(8):
        p.song[row][0] = 45 if row == 7 else 90
        p.song[row][1] = 61
        p.song[row][2] = 199

    return p


def build_column_scheme(project, slots_per_column=SLOTS_PER_COLUMN):
    """Compute a Remapping that reindexes each song column's chains and
    phrases into a dedicated per-column block, and compacts every
    referenced instrument into a global pool starting at 0.

    Raises ValueError if a column references more chains/phrases than fit
    in its block, or if the same chain/phrase is referenced by more than
    one column (this scheme assumes each chain/phrase belongs to a single
    column — a reasonable assumption for per-track patterns, not a rule
    pym8 enforces generally).
    """
    chain_map = {}
    phrase_map = {}
    instrument_order = []
    seen_instruments = set()

    for col in range(COL_COUNT):
        col_chains = []
        for row in project.song:
            ref = row[col]
            if ref != EMPTY_CHAIN and ref not in col_chains:
                col_chains.append(ref)

        if len(col_chains) > slots_per_column:
            raise ValueError(
                f"column {col} references {len(col_chains)} chains, more "
                f"than the {slots_per_column}-slot block allows"
            )

        base = col * slots_per_column
        for i, src_chain in enumerate(col_chains):
            if src_chain in chain_map:
                raise ValueError(
                    f"chain {src_chain} is referenced by more than one song "
                    "column; this scheme assumes one column per chain"
                )
            chain_map[src_chain] = base + i

        col_phrases = []
        for src_chain in col_chains:
            for step in project.chains[src_chain]:
                if step.phrase != EMPTY_PHRASE and step.phrase not in col_phrases:
                    col_phrases.append(step.phrase)

        if len(col_phrases) > slots_per_column:
            raise ValueError(
                f"column {col} references {len(col_phrases)} phrases, more "
                f"than the {slots_per_column}-slot block allows"
            )

        for i, src_phrase in enumerate(col_phrases):
            if src_phrase in phrase_map:
                raise ValueError(
                    f"phrase {src_phrase} is referenced by more than one "
                    "song column; this scheme assumes one column per phrase"
                )
            phrase_map[src_phrase] = base + i

            for pstep in project.phrases[src_phrase]:
                if pstep.instrument != EMPTY_INSTRUMENT and pstep.instrument not in seen_instruments:
                    seen_instruments.add(pstep.instrument)
                    instrument_order.append(pstep.instrument)

    instrument_map = {src: i for i, src in enumerate(instrument_order)}
    return Remapping(chains=chain_map, phrases=phrase_map, instruments=instrument_map)


def clear_orphaned_sources(project, remap):
    """Turn renumber()'s copy semantics into a clean move.

    renumber() only writes declared destinations — a source slot that
    isn't *also* a destination in the same kind's mapping keeps its old
    content (see renumber()'s docstring). For a normalisation pass that's
    exactly the case for every slot we moved away from, so explicitly
    blank those out here rather than leaving duplicate ghost data behind.
    """
    chain_dsts = set(remap.chains.values())
    for src in remap.chains:
        if src not in chain_dsts:
            project.chains[src] = M8Chain()

    phrase_dsts = set(remap.phrases.values())
    for src in remap.phrases:
        if src not in phrase_dsts:
            project.phrases[src] = M8Phrase()

    instrument_dsts = set(remap.instruments.values())
    blank_instruments = M8Instruments()
    for src in remap.instruments:
        if src not in instrument_dsts:
            project.instruments[src] = blank_instruments[src]


def main():
    print("Building a project with scattered slot numbering...")
    project = build_messy_project()

    print("\nBefore:")
    print(f"  song col 0 (drums) -> chains {sorted({project.song[r][0] for r in range(8)})}")
    print(f"  song col 1 (bass)  -> chains {sorted({project.song[r][1] for r in range(8)})}")
    print(f"  song col 2 (lead)  -> chains {sorted({project.song[r][2] for r in range(8)})}")
    print(f"  instruments used   -> {sorted(i for i, inst in enumerate(project.instruments) if project.instruments.is_concrete(i))}")

    remap = build_column_scheme(project)
    print("\nComputed scheme:")
    print(f"  chains:      {dict(sorted(remap.chains.items()))}")
    print(f"  phrases:     {dict(sorted(remap.phrases.items()))}")
    print(f"  instruments: {dict(sorted(remap.instruments.items()))}")

    renumber(project, remap)
    clear_orphaned_sources(project, remap)
    project.metadata.name = PROJECT_NAME

    print("\nAfter:")
    print(f"  song col 0 (drums) -> chains {sorted({project.song[r][0] for r in range(8)})}")
    print(f"  song col 1 (bass)  -> chains {sorted({project.song[r][1] for r in range(8)})}")
    print(f"  song col 2 (lead)  -> chains {sorted({project.song[r][2] for r in range(8)})}")
    print(f"  instruments used   -> {sorted(i for i, inst in enumerate(project.instruments) if project.instruments.is_concrete(i))}")

    problems = project.check_references()
    print(f"\ncheck_references() after normalising: {len(problems)} problem(s)")
    for p in problems:
        print(f"  ! {p}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{PROJECT_NAME}.m8s"
    project.write_to_file(str(out_path))

    print(f"\n✓ Wrote {out_path}")
    print(f"  ship to your M8 with: python tools/sync.py push")


if __name__ == "__main__":
    main()
