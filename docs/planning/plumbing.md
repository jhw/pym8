# Plumbing TODO

Three items called out as not yet plumbed in the descriptor-refactor base.
None block current functionality; each becomes load-bearing as parity work
with [m8-file-parser](https://github.com/Twinside/m8-file-parser) starts.

## 1. Version threading through `M8Project.read()` — do early

Right now version is read at byte 10 and stored on the project, but
`M8Metadata.read()`, `M8Instruments.read()`, etc. don't receive it. The
moment we add EQ or Settings — where firmware version changes offsets and
field presence — version needs to flow into the section reader signatures
(or be reachable via a project reference).

**Recommended approach:** add a `version` parameter to each section's
`read()` (default to the current shipped version), and route it from
`M8Project.read()`. Even with no consumer today, this stabilises the
signatures so the first version-conditional reader doesn't trigger a
signature churn pass.

**Status:** ~30-minute refactor. Belongs on the descriptor foundation
branch, not bolted on with the first feature.

## 2. Version-aware OFFSETS — defer until first conflict

m8-file-parser has `V4_OFFSETS` and `V4_1_OFFSETS` and picks at runtime
(`songs.rs:50-78`). For every section pym8 currently parses, both Rust
offset sets are **identical** — there's nothing to branch on yet. Adding
`def offsets(version): return V4_1_OFFSETS if version >= (4,1,0) else
V4_OFFSETS` today would be a function that always returns the same value.

The right moment to add this is when implementing EQ, which is the first
section where the offsets actually diverge:
- v4.0: 32 EQs
- v4.1+: 128 EQs + per-instrument-EQ at offset `+0x165` inside the
  instrument block

**Status:** defer. Add alongside EQ implementation when there's a real
branch to write.

## 3. Reader/Writer abstraction — defer until bytearray slicing hurts

Rust has explicit cursor objects: `reader.read_string(n)`, `reader.read()`,
`reader.read_bool()`, `writer.seek()` (`m8-file-parser/src/reader.rs`,
`writer.rs`). pym8 slices `bytearray` directly.

The cursor model becomes attractive when reads start being conditional
("read N bytes only if firmware ≥ X"), since slice arithmetic with branches
gets fiddly. Today nothing reads conditionally, so adding the abstraction
now is infrastructure without a user.

**Status:** defer. Add when implementing settings or EQ if the bytearray
slicing starts hurting; otherwise leave alone.

## Remapper is a separate problem (Phase 2)

`m8-file-parser/src/remapper.rs` (1,018 lines) is about cross-section
reference tracking — chain → phrase → instrument → table → EQ, with
ID-collision resolution when importing across projects. The descriptor
framework doesn't directly help here; remapper's value-add is the
traversal logic and rename-on-import semantics.

The typed-field model **indirectly** helps because each `ByteField` could
carry a "this is an instrument reference" annotation, which would let
remapper enumerate references generically. But that annotation pass and
the traversal subsystem are independent of getting sections parsed.

**Treat remapper as Phase 2:** after sections are in place to be remapped.
See [roadmap.md](roadmap.md) for sequencing.
