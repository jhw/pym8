# Plumbing TODO

Three items called out as not yet plumbed in the descriptor-refactor base.
None block current functionality.

## 1. ~~Version threading through `M8Project.read()`~~ — **done**

Threaded only along the path Phase-2 work actually needs:
`M8Project.read() → M8Instruments.read() → subclass.read()`. The other
section readers (metadata / song / chains / phrases) accept whatever
data slice they're given without taking a version parameter — none of
them have firmware-conditional logic.

Per-section settings readers (`M8MidiSettings.read`,
`M8MixerSettings.read`, `M8EffectsSettings.read`, `M8Eqs.read`) accept
`version=None` for forward-compat but ignore it (their byte layout is
flat for the v6.0+ firmware pym8 targets).

`M8HyperSynth.read()` threads version through to `super()`;
`read_from_file()` (.m8i) threads file-byte-10 version into subclass
read directly.

## 2. Version-aware OFFSETS — **gated on broader firmware support**

m8-file-parser has `V4_OFFSETS` and `V4_1_OFFSETS` (firmware 4.0 vs
v4.1+) and picks at runtime. pym8 currently targets v6.0+ only — the
v4.0 and v5.0 templates were dropped, the EQ implementation declared
v6.0+ layout exclusively, and settings classes assume unconditional
field presence.

The point of version-aware OFFSETS would be to **broaden** firmware
support. As long as pym8's scope stays v6.0+, this is overhead without
a consumer. Add when (and if) supporting v4.0 / v4.1 / v5.0 files
becomes an actual ask.

## 3. Reader/Writer abstraction — **gated on conditional reads**

Rust has cursor objects (`reader.read_string(n)`, `writer.seek()`).
pym8 slices bytearrays directly.

This was supposed to start paying off "when bytearray slicing hurts."
Through HyperSynth, EQ, Mixer / MIDI / Effects settings, slicing
didn't hurt — every read is a clean fixed-width slice at a fixed
offset, no version-conditional skip-N-bytes logic. The cursor model
would matter if pym8 started doing `if version >= X: skip N more bytes
and read this extra field`, which it doesn't (see item 2).

Add when (and if) version-conditional reads land. Still deferred.

## Remapper (Phase 3)

`m8-file-parser/src/remapper.rs` (1,018 lines) is about cross-section
reference tracking — chain → phrase → instrument → table → EQ, with
ID-collision resolution when importing across projects. The descriptor
framework doesn't directly help here; remapper's value-add is the
traversal logic and rename-on-import semantics.

The typed-field model **indirectly** helps because each `ByteField`
could carry a "this is an instrument reference" annotation, which would
let remapper enumerate references generically. But that annotation pass
and the traversal subsystem are independent of getting sections parsed.

**Treat remapper as Phase 3:** after sections are in place to be
remapped (specifically, tables — every other reference-bearing section
is already parsed). See [roadmap.md](roadmap.md) for sequencing.
