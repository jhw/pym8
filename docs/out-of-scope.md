# Out of scope

Things [m8-file-parser](https://github.com/Twinside/m8-file-parser) does that
pym8 does not. None of these block "open a v6.0+ `.m8s` project, edit any
field, write it back" — that path is at parity. The items below are
deliberate scope decisions plus a couple of subtle byte-level divergences
worth recording.

## Out of scope by design

### Pre-v6.0 firmware support

Rust handles v2 / v3 / v4.0 / v4.1 / v5.0 / v6.0 / v6.2 with version-
conditional offsets and field sets. pym8 explicitly targets **v6.0+**:

- v4.0 and v5.0 templates were dropped from `m8/templates/`
- EQ implementation models v4.1+ layout only (32 EQs vs 128 + per-instrument
  not handled)
- Modulator format split (`mod_only2` pre-v3.0 vs `mod_only3` v3.0+) not
  modelled — pym8 only reads the modern path
- Per-instrument `associated_eq` byte position varies pre-v5.0 (Rust uses
  the packed transpose byte in v4.1, byte 62 in v5.0+); pym8 only reads
  byte 62

The plumbing for broader firmware support exists in concept
([plumbing.md](planning/plumbing.md) items 2 and 3 — version-aware OFFSETS,
Reader/Writer cursor abstraction) but isn't built. Both are gated on a
real consumer asking for older-firmware support.

**If revisited:** start with a version-aware OFFSETS selector
(`def offsets(version): return V4_1_OFFSETS if version >= (4,1,0) else
V4_OFFSETS`) and version-conditional reads in section parsers. Reader/Writer
cursor objects become attractive once skip-N-bytes-if-firmware-X logic
proliferates.

### Theme / `.m8c` file format

Rust has `theme.rs` (72 lines) for parsing the M8's separate theme files —
RGB palettes for the UI. pym8 only handles `.m8s` (projects) and `.m8i`
(single-instrument exports). Theme is its own file format, not embedded in
the `Song` struct.

**If revisited:** add a new `m8/api/theme.py` module independent of project
parsing. Small (~13 RGB triples, fixed layout) — half a day of work.

### Display / UI infrastructure

Rust has substantial machinery for *displaying* M8 data in a human-readable
form:

- `param_gatherer.rs` (595 lines) — generic parameter-introspection trait
  with `ParameterGatherer` + `Describable` for pretty-printing, diffing,
  auditing
- FX command name tables per firmware version (`HYPERSYNTH_COMMAND_NAMES`,
  `HYPERSYNTH_COMMAND_NAMES_6_2`, etc.) with formatted output
- `TableView` / `PhraseView` — formatted screen-style printing matching the
  M8's own UI ("N  V  FX1  FX2  FX3" headers, etc.)
- `RemapperDescriptorBuilder` trait for narrating remapper operations

pym8 leaves display to consumers. The closest analogue to `param_gatherer`
is `iter_fields()` in `m8/api/fields.py` — same conceptual capability
(walk every typed parameter generically) but via descriptors rather than a
trait. Building a CLI tool on top of pym8 would mean writing the display
layer yourself.

**If revisited:** the FX command name tables would be the most useful first
piece. The rest is consumer-side work.

## Subtle divergences worth recording

### TranspEq byte packing (instrument byte 13)

Rust models the v6.0+ instrument transpose byte as `(transpose_bool << 7) |
(associated_eq & 0x7F)` via the `TranspEq` struct. On write, Rust packs
both fields back into byte 13 — duplicating `associated_eq` (which is also
stored authoritatively at byte 62 in v5.0+).

pym8 just stores byte 13 as `transpose` (a single byte) and writes
`associated_eq` only at byte 62. The two paths agree for the M8 firmware
(which reads byte 62 in v5.0+) but a Rust reader looking at byte 13's EQ
bits after pym8 wrote the file would see stale data.

**Practical impact:** none on the M8 firmware. Tools comparing files
byte-by-byte across Rust vs pym8 writes will see a difference.

**If revisited:** make `instrument.transpose` a property that reads bit 7
and writes back `(transpose << 7) | (associated_eq & 0x7F)`. Two-line
change in `instrument.py`.

### Remapper: no identical-instrument deduplication

When importing an instrument into a destination project, Rust's allocator
first checks whether a byte-for-byte identical instrument already exists in
the destination — if yes, it reuses that slot. pym8 always allocates a
fresh slot.

**Practical impact:** importing the same instrument from the same source
twice produces two slots in the destination instead of one. Importing into
a destination that happens to already contain an identical instrument also
allocates a fresh slot.

**If revisited:** in `m8.api.remapper.allocate()`, before calling
`_find_free_slot` for an instrument, scan `destination.instruments` for a
byte-for-byte match (accounting for EQ remapping) and reuse the slot if
found. ~30 lines.

### Bytearray slicing vs cursor reader

pym8 uses raw `data[offset:offset+N]` slicing throughout. Rust has explicit
`Reader` / `Writer` cursor objects with `read_string(n)`, `read_bool()`,
`seek(pos)`. Same capability, different style.

The cursor model would be cleaner if pym8 ever needs version-conditional
reads ("skip N bytes if firmware ≥ X"). Today it doesn't, so slicing wins
on readability.

**If revisited:** introduce `m8/api/reader.py` and `m8/api/writer.py`,
migrate one section parser at a time. Probably triggered by the same
firmware-broadening work that would justify version-aware OFFSETS.
