# Parity roadmap

Goal: bring pym8 to feature parity with
[m8-file-parser](https://github.com/Twinside/m8-file-parser).

The descriptor-refactor base (`m8/api/fields.py`, subclass registries,
generic to_dict/from_dict, version helpers) is the foundation. Each item
below is "declare a class with descriptors, plug it into M8Project, add
fixture rows to the tests". See [plumbing.md](plumbing.md) for groundwork
that may need to land first.

## Phase 1 — Instrument completion ✅

### 1. ~~HyperSynth (instrument type 5)~~ **— done**
Reference: `m8-file-parser/src/instruments/hypersynth.rs` (236 lines).
Implemented in `m8/api/instruments/hypersynth.py`:
- `M8HyperSynth` instrument class
- `M8Chord` record (mask + 6 oscillator offsets)
- `M8HyperSynthChords` collection (16 chord rows, stored as a separate
  attribute and merged into the byte buffer at write time — same pattern as
  `modulators`)
- New `BytesField` descriptor for the 7-byte `default_chord` array

The "known but unsupported type" warning test was dropped (no such type
remains); the truly-unknown warning test still covers future format
additions.

All seven instrument types in `M8InstrumentType` now have concrete subclasses.

## Phase 2 — Top-level sections

These are the sections `m8/api/project.py` defines offsets for but doesn't
parse. Currently round-trip via the raw `data` bytearray; not editable
from Python.

### 2. Version threading (plumbing)
Before any version-conditional section, thread `version` through
`M8Project.read()` into the section readers. See `plumbing.md` item 1.
~30-minute prep commit.

### 3. EQ (`eq.rs`, 217 lines) — highest user-visible value
- 7 EQ types: LowCut, LowShelf, Bell, BandPass, HiShelf, HiCut, AllPass
- 5 modes: Stereo / Mid / Side / L / R
- 6-byte `EqBand` structs with frequency/level fine-tune
- **Per-instrument `associated_eq` byte** — every instrument has an EQ
  reference. Affects all instrument classes.
- Firmware: v4.0 has 32 EQs total; v4.1+ has 128 + per-instrument-EQ
  storage at instrument-offset `+0x165`. **First section needing
  version-aware OFFSETS** (see plumbing.md item 2).

This is where the version-conditional OFFSETS pattern earns its keep.

### 4. Mixer / MIDI / Effects settings (`settings.rs`, 328 lines)
Three structs at offset `0x1A5C1`:
- `MixerSettings` — master + 8 track volumes, send levels, DJ filter,
  limiter (attack/release added v6.0), OTT level (v6.2+)
- `MidiSettings` — 13 fields for sync/transport/record/control/channel
  routing
- `EffectsSettings` — chorus/delay/reverb knobs

Several version-conditional reads here (limiter v6.0+, OTT v6.2+) — this
is where the cursor-style Reader/Writer abstraction starts to pay off if
deferred slicing gets messy.

### 5. Tables (256 entries, offset `0xBA3E`)
The M8's per-step modulation feature. Each table entry contains FX
commands that reference instruments — table entries are themselves
reference-bearing. Needed before remapper has much to remap.

### 6. MIDI mappings (128, offset `0x1A5FE`)
External controller → M8 parameter routing.

### 7. Scales (16, offset `0x1AA7E`)
Microtonal scale definitions (`scale.rs`, 109 lines).

### 8. Grooves (32, offset `0xEE`)
Timing-curve definitions.

### 9. Theme (`theme.rs`, 72 lines)
RGB UI colors. Lowest priority — UI-only, doesn't affect sound.

## Phase 3 — Cross-cutting subsystem

### 10. Remapper (`remapper.rs`, 1,018 lines)
Cross-project chain/instrument/phrase/table/EQ renumbering with reference
re-indexing. Solves the "import instrument from song A into song B without
ID collisions" workflow.

Doesn't directly benefit from the descriptor refactor — it's about
traversal logic and ID-collision resolution. But every section it operates
on has to exist first, hence Phase 2 ordering.

**Suggested approach when starting:** annotate reference-bearing
`ByteField`s with a `references=...` kwarg (e.g.
`instrument = ByteField(2, references="instrument")`), then implement
remapper as a generic walker over those annotations rather than the
section-specific logic the Rust crate uses. Smaller surface area,
easier to test.

## Out of scope / not pursued

- **`param_gatherer.rs`** (595 lines) — Rust's generic parameter
  introspection trait. Already solved in pym8 by `iter_fields()` over
  descriptors, which gives any class a generic walk for free.

## Suggested commit cadence

1. HyperSynth + tests + README — one PR
2. Version threading plumbing — one PR
3. EQ (global + per-instrument) + version-aware OFFSETS — one PR (the big
   one)
4. Settings (mixer + MIDI + effects) + cursor abstraction if helpful —
   one PR per settings group, three PRs total
5. Tables — one PR
6. MIDI mappings, scales, grooves, theme — one PR each (small)
7. Remapper — multi-PR Phase 2

Each PR ships with descriptor declarations, M8Project hooks, and a row in
the relevant test fixture (instruments / modulators / sections). The
test-fixture-row discipline keeps cross-cutting coverage automatic.
