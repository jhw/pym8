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

### 2. ~~Version threading (plumbing)~~ **— done**
`version` now flows from `M8Project.read()` into `M8Instruments.read()`
into each subclass's `read()`. `M8HyperSynth.read()` threads it through
to super. `read_from_file()` (.m8i) threads the file-byte-10 version
directly into subclass.read instead of overwriting after.

### 3. ~~EQ (`eq.rs`, 217 lines)~~ **— done (v6.0+ layout)**
- 7 EQ types: LowCut, LowShelf, Bell, BandPass, HiShelf, HiCut, AllPass
  (`M8EqType`)
- 5 stereo modes: Stereo / Mid / Side / L / R (`M8EqMode`)
- 6-byte `M8EqBand` with packed type/mode byte + 16-bit freq + signed
  16-bit gain + Q
- 18-byte `M8Eq` = 3 bands (low / mid / high)
- 132-entry `M8Eqs` at offset 0x1AD5E (v6.0+ layout). Exactly fills
  the bundled template to EOF.
- **Per-instrument `associated_eq` byte** added to `M8Instrument` base
  at offset 62 (just before modulators). 0xFF = no EQ bound.

Pre-v6 layouts (v4.0 with 32 EQs, v4.1 transpose-byte-packed EQ index)
are explicitly out of scope — pym8 targets v6.0+.

The version-conditional OFFSETS pattern hasn't yet earned its keep
since we only target one firmware family. Add the `def
offsets(version)` selector if/when older-firmware support becomes a
real ask.

### 4. ~~Mixer / MIDI / Effects settings~~ (`settings.rs`, 328 lines) **— done**
Three structs at three different file offsets:
- `M8MixerSettings` (32 bytes at file 206) — `m8/api/settings.py`
- `M8MidiSettings` (27 bytes at file 160) — `m8/api/midi_settings.py`
- `M8EffectsSettings` (26 bytes at file 107969) — `m8/api/settings.py`

`M8Metadata` was truncated from 147 → 146 bytes (the bogus `key` byte
at metadata-relative offset 146 was actually pointing at
`MidiSettings.receive_sync` — pre-existing bug). The real musical-key
byte at file 187 is exposed as `project.key` (top-level on M8Project) but
written specially by `M8Project` (it isn't part of the contiguous
metadata block).

The cursor-style Reader/Writer abstraction from plumbing.md item 3
**still hasn't earned its keep** — the settings classes are flat
descriptor-over-bytearray records with no version-conditional reads
(all "v6.0+" fields are present unconditionally in our target firmware,
just unused / zeroed in pre-v6 files). Defer.

### 5. ~~Tables (256 entries, offset `0xBA3E`)~~ **— done**
`m8/api/table.py`: `M8TableStep` (8 bytes — transpose + velocity + 3 FX
tuples), `M8Table` (16 steps = 128 bytes), `M8Tables` (256 tables =
32 768 bytes = 0x8000). Each step's three FX tuples reuse the existing
`M8FXTuples` class (same 2-byte key+value layout as phrase FX).

Reference-bearing: each step's FX commands can target instruments,
tables, or EQs (via the relevant FX command codes). The remapper will
need a generic traversal that walks `project.tables[*][*].fx[*]` along
with phrases/chains/etc. — see Phase 3.

### 6. ~~MIDI mappings (128, offset `0x1A5FE`)~~ **— done**
External controller → M8 parameter routing. 128 × 7 bytes via
`m8/api/midi_mapping.py` (`M8MidiMapping` / `M8MidiMappings`).

### 7. ~~Scales (16, offset `0x1AA7E`)~~ **— done**
Microtonal scale definitions. 16 × 46 bytes (Rust's spec covers the
first 42; trailing 4 bytes are reserved, preserved verbatim) via
`m8/api/scale.py` (`M8Scale` / `M8Scales`). Per-note enabled bitmap +
(semitone, cents) offsets + 16-byte scale name.

### 8. ~~Grooves (32, offset `0xEE`)~~ **— done**
Timing-curve definitions. 32 × 16 bytes via `m8/api/groove.py`
(`M8Groove` / `M8Grooves`). Step values are timing offsets; 0xFF
terminates the active portion of the pattern.

### 9. ~~Theme (`theme.rs`, 72 lines)~~ **— out of scope**
Theme is not part of the `.m8s` Song struct in m8-file-parser — it
lives in a separate `.m8c` file format. Not modelling for pym8; if
someone wants `.m8c` support later it'd be a new module not tied to
project parsing.

## Phase 3 — Cross-cutting subsystem

### 10. ~~Remapper~~ **— done** (`m8/api/remapper.py`, 4 commits)
Cross-project chain/instrument/phrase/table/EQ renumbering with reference
re-indexing. Solves the "import instrument from song A into song B
without ID collisions" workflow.

Implemented in four commits on `feat/remapper`:

1. **Walker** — `walk_dependencies(project, *, chains=, instruments=,
   tables=, eqs=) → Mappings`. Closure of all transitively referenced
   slots starting from seed sets. Models the firmware-6 implicit
   "instrument N owns table N" convention; handles cycles in table-to-
   table references.

2. **Allocator** — `allocate(source, destination, mappings) → Remapping`.
   Per-slot-kind from→to dicts. Prefer-same-index optimization with
   fall-through to next-free; raises `NoFreeSlotError` when destination
   is full of some kind. Tables 0..127 piggyback on their owning
   instrument's destination slot.

3. **Apply** — `apply(source, destination, mappings, remap)`. Copies
   mapped source slots to destination with all references rewritten:
   chain step `.phrase`, phrase step `.instrument`, FX values for
   INS/NXT/TBL/TBX/EQM/EQI, instrument `.associated_eq`. Source is
   never mutated.

4. **Public API + demo** — `Remapper(source, destination, *, chains=,
   ...)` inspectable class and `move_chains(src, dst, chain_ids)`
   one-shot. `demos/remap_merge.py` builds two source projects (drum
   kit + bass line, both using slot 0 for chain/phrase/instrument) and
   merges them into a single project with the remapper resolving every
   collision.

Implementation differs from the Rust crate in two ways:
- Smaller surface (~470 lines vs 1,018) — pym8 doesn't model
  RemapperDescriptorBuilder / move-kind enum / pretty-printing. Add if
  someone needs them.
- No identical-instrument-deduplication optimization (Rust scans the
  destination for an instrument matching the source's exact bytes and
  reuses that slot if found). pym8 always allocates a fresh slot. Easy
  to add later if collisions stop fitting; for now, find-next-free is
  simpler and matches user expectations.

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
