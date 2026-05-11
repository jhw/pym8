# pym8 — agent guide

Python port of [m8-file-parser](https://github.com/Twinside/m8-file-parser) (Rust). Reads, writes, and manipulates Dirtywave M8 tracker files (`.m8s` projects, `.m8i` single-instrument exports). Target firmware **6.2+**.

## Code philosophy

- **No backwards compatibility shims.** When refactoring, delete the old code. No `_old`/`_legacy` suffixes, no `# deprecated` markers, no re-exports of moved modules.
- **Simple and focused.** Implement what the task needs; don't speculate on future requirements. Three similar lines beats a premature abstraction.
- **Match the binary spec.** When in doubt about an offset, enum value, or layout, verify against `../m8-file-parser/src/`. That Rust crate is the authoritative reference.

## Architecture

- **Core library:** `m8/api/` — `project.py` (top-level), `instrument.py` (base), `instruments/` (one file per type), `modulator.py`, `phrase.py`, `chain.py`, `song.py`, `fx.py`, `version.py`, `fields.py`.
- **Audio tools:** `m8/tools/` — `chain_builder.py` (sample-chain WAV processing), `wav_slicer.py` (slice-point metadata).
- **Demos:** `demos/<category>/<flavor>.py` — runnable scripts that produce `.m8s` files in `tmp/demos/`.
- **Sync to device:** `tools/sync.py` — one CLI with `status` / `push` / `clean local` / `clean remote` subcommands.

### Instrument and modulator descriptors

Instrument parameters and modulator parameters are declared as **`ByteField`** / **`StringField`** descriptors (see `m8/api/fields.py`). The descriptor *is* the source of truth for offset, default, valid range, and enum binding. The underlying `_data` bytearray stays as the buffer — descriptors are a typed view.

```python
class M8Wavsynth(M8Instrument):
    TYPE_ID = M8InstrumentType.WAVSYNTH
    shape  = ByteField(18, enum=M8WavShape)
    cutoff = ByteField(24, default=0xFF)
    # ...

inst = M8Wavsynth(name="LEAD")
inst.shape = M8WavShape.SAW       # validated, enum-aware
inst.cutoff = 0x40                # range-checked
```

Modulators follow the same pattern with one subclass per type (`M8AHDModulator`, `M8LFOModulator`, etc.). **Changing a modulator's type means replacing the slot** — different types reinterpret bytes 2-5.

`to_dict()` / `from_dict()` walk the descriptor protocol generically; both always serialize enums by name. There is no `enum_mode` flag.

### Two MIDI-ish instrument types — don't confuse them

- **`M8MIDIOut` (type 3)** — pure MIDI output to external gear. 10 CC slots (CCA–CCJ). Port enum is `MIDI_USB | MIDI | USB | INTERNAL`. **This is what MIDI demos use.**
- **`M8External` (type 6)** — audio-input routing with 4 CC slots. Has filter/amp/sends. Use this when you want external audio through M8 effects.

All seven instrument types in `M8InstrumentType` have a concrete subclass. The
"unsupported instrument type" warning path in `M8Instruments.read()` still
exists for future format additions — keep it.

`M8HyperSynth` is the one instrument with a sub-record beyond the standard 215
bytes worth modelling: the 16-row chord matrix at offset 87. It's stored as a
separate Python attribute (`chords`, a `M8HyperSynthChords` list) and merged
into the byte buffer at write time — same pattern as `modulators` at offset 63.
If a future instrument adds another structured sub-record, follow this pattern
rather than trying to express it via descriptors.

## Testing

Tests live in `tests/`, mirroring the `m8/` layout. Use `unittest` (not pytest — there's no pytest dependency). Each test file is named after the module it tests (`tests/api/wavsynth.py`, not `test_wavsynth.py`).

Run the whole suite:

```bash
python -m unittest discover -s tests -p '*.py'
```

Cross-cutting per-type assertions live in `tests/api/instruments.py` (every instrument type passes the same fixture) and `tests/api/modulator.py` (every modulator subclass passes the same fixture). Per-type quirks live in their own file. Avoid duplicating cross-cutting tests when adding a new instrument or modulator type — just add a row to the fixture.

## Demos

Demos are runnable scripts under `demos/`. They produce `.m8s` files in `tmp/demos/<category>/<flavor>/`. Pass `PYTHONPATH=.` if running directly:

```bash
PYTHONPATH=. python demos/acid_303/sampler.py
```

After generating, ship to a connected M8 with:

```bash
python tools/sync.py status   # see what's local vs remote
python tools/sync.py push     # copy tmp/demos → /Volumes/M8/Songs/pym8-demos/
```

Pass `--test` to operate on `tmp/virtual-m8/` instead of `/Volumes/M8/`.

## M8 file format notes

- Binary, little-endian, mostly unsigned 8-bit fields. Tempo is float32. Strings are null-padded (some are 0xFF-tolerant).
- Top-level sections pym8 parses today: metadata, song matrix, chains, phrases, instruments. Other sections (groove, table, effect_settings, midi_mapping, scale, eq) round-trip as raw bytes but aren't editable yet.
- Instruments are 215 bytes each; modulators sit at offset 63 within an instrument block (offset 61 in `.m8i` files, which also reorder LFO bytes).
- Firmware-conditional offsets exist between v4.0 and v4.1 (mostly in unparsed sections — see `m8-file-parser/src/songs.rs`).
