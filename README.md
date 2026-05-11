# pym8

A Python library for reading and writing Dirtywave M8 tracker files.

## Overview

pym8 lets you create, read, and edit M8 projects (`.m8s`) and single-instrument exports (`.m8i`) programmatically. The M8 is a portable music tracker/synthesizer by [Dirtywave](https://dirtywave.com/products/m8-tracker). pym8 is a Python port of [m8-file-parser](https://github.com/Twinside/m8-file-parser); target firmware is **6.2+**.

What it covers:
- All seven instrument types (Wavsynth, Macrosynth, Sampler, MIDIOut, FMSynth, HyperSynth, External)
- All six modulator types (AHD, ADSR, Drum, LFO, Trig, Tracking) as distinct classes
- Phrases (notes + FX), chains, song matrix, instrument slots
- 3-band parametric EQ (132 slots, 7 EQ types × 5 stereo modes) — global, effect-section, and per-instrument
- Mixer settings (master volume, 8 track volumes, send levels, DJ filter, limiter, OTT) and effects settings (chorus / delay / reverb knobs, OTT config)
- FX command enums for Sequence, Sampler, Mixer (firmware 6.2), and Modulator FX groups
- Audio helpers: sample-chain WAV builder, slice-point WAV writer

What it doesn't cover yet: groove definitions, scales, MIDI settings, MIDI mappings, themes, tables, project remapping. Those sections survive round-trip as raw bytes but aren't editable from Python.

## Install

```bash
pip install -e .
```

Dependencies (`pydub` for sample tooling, `pyyaml` for the demo preset loader) are declared in `pyproject.toml`.

## Quick start

```python
from m8.api.project import M8Project
from m8.api.instruments.sampler import M8Sampler
from m8.api.phrase import M8Phrase, M8PhraseStep, M8Note
from m8.api.chain import M8Chain, M8ChainStep

project = M8Project.initialise()
project.metadata.name = "MY-SONG"
project.metadata.tempo = 140

# Instrument — parameters are typed descriptor attributes
kick = M8Sampler(name="KICK", sample_path="samples/kick.wav")
kick.delay_send = 0x80
project.instruments[0] = kick

# Phrase — four-on-the-floor
phrase = M8Phrase()
for step in (0, 4, 8, 12):
    phrase[step] = M8PhraseStep(note=M8Note.C_4, velocity=0x6F, instrument=0x00)
project.phrases[0] = phrase

# Chain references the phrase; song row 0 track 0 plays the chain
project.chains[0] = M8Chain()
project.chains[0][0] = M8ChainStep(phrase=0x00, transpose=0x00)
project.song[0][0] = 0x00

project.write_to_file("MY-SONG.m8s")
```

Reading an existing file:

```python
project = M8Project.read_from_file("existing-song.m8s")
print(project.metadata.name, project.metadata.tempo)
for i, inst in enumerate(project.instruments):
    if hasattr(inst, "name"):
        print(f"  {i:02X}: {type(inst).__name__} {inst.name!r}")
```

## Instruments

Parameters are exposed as typed descriptor attributes. Setting an out-of-range value raises `ValueError`; enum-typed fields accept either an enum member or a raw int.

| Class | Type ID | Purpose |
|---|---|---|
| `M8Wavsynth` | 0 | Wavetable synthesizer (70 shapes) |
| `M8Macrosynth` | 1 | Mutable Instruments Braids algorithms (45 shapes) |
| `M8Sampler` | 2 | Sample playback with slicing/looping/pitch modes |
| `M8MIDIOut` | 3 | Pure MIDI output to external gear (10 CC slots) |
| `M8FMSynth` | 4 | 4-operator FM synthesizer |
| `M8HyperSynth` | 5 | 6-oscillator detuned-stack synth with 16-slot chord matrix |
| `M8External` | 6 | Audio-input routing with 4 CC slots |

> **MIDIOut vs External.** `M8MIDIOut` (type 3) is what you want for sequencing external hardware/software synths over MIDI — 10 CC slots, port enum including `INTERNAL`. `M8External` (type 6) routes external *audio* into the M8's effect chain and has a small MIDI CC capability alongside. The MIDI demos in this repo all use `M8MIDIOut`.

### Examples

```python
# Wavsynth
from m8.api.instruments.wavsynth import M8Wavsynth, M8WavShape
w = M8Wavsynth(name="LEAD")
w.shape = M8WavShape.SAW
w.size = 0x80
w.cutoff = 0xA0

# Macrosynth (Braids-based)
from m8.api.instruments.macrosynth import M8Macrosynth, M8MacroShape
m = M8Macrosynth(name="BASS")
m.shape = M8MacroShape.CSAW
m.timbre = 0x60
m.colour = 0x40

# Sampler
from m8.api.instruments.sampler import M8Sampler, M8PlayMode
from m8.api.instrument import M8FilterType
s = M8Sampler(name="SNARE", sample_path="samples/snare.wav")
s.play_mode = M8PlayMode.FWDLOOP
s.filter_type = M8FilterType.LOWPASS
s.cutoff = 0xC0
s.chorus_send = 0x40

# FM synth
from m8.api.instruments.fmsynth import M8FMSynth, M8FMAlgo, M8FMWave
fm = M8FMSynth(name="BELL")
fm.algo = M8FMAlgo.A_B_C_D
fm.op_a_shape = M8FMWave.SIN
fm.op_b_ratio = 0x02

# MIDI out
from m8.api.instruments.midiout import M8MIDIOut, M8MIDIPort
mout = M8MIDIOut(name="TB-03")
mout.port = M8MIDIPort.MIDI
mout.channel = 0
mout.cca_num = 71      # CC for resonance
mout.cca_val = 0x40

# HyperSynth (6-oscillator stack + chord matrix)
from m8.api.instruments.hypersynth import M8HyperSynth, M8Chord
hs = M8HyperSynth(name="STACK")
hs.swarm = 0x80              # spread amount
hs.width = 0x40              # stereo width
hs.default_chord = [0, 4, 7, 0, 0, 0, 0]  # plays a major triad by default
# Slot 0 = root + 5th + octave on oscillators 0, 1, 2
hs.chords[0] = M8Chord(mask=0b00000111, offsets=[0, 7, 12, 0, 0, 0])

# External (audio in)
from m8.api.instruments.external import M8External, M8ExternalPort, M8ExternalInput
ext = M8External(name="GUITAR")
ext.port = M8ExternalPort.MIDI
ext.input = M8ExternalInput.LINE_IN_LR
ext.cutoff = 0xC0
```

## Modulators

Each instrument has 4 modulator slots. Modulators are typed subclasses — to change a slot's type, replace the slot.

```python
from m8.api.modulator import M8AHDModulator, M8LFOModulator, M8LFOShape
from m8.api.instruments.macrosynth import M8MacrosynthModDest

inst = M8Macrosynth(name="LEAD")
inst.modulators[0] = M8AHDModulator(
    destination=M8MacrosynthModDest.VOLUME,
    amount=0xFF,
    attack=0x00,
    decay=0x80,
)
inst.modulators[2] = M8LFOModulator(
    destination=M8MacrosynthModDest.CUTOFF,
    amount=0x60,
    shape=M8LFOShape.SIN,
    freq=0x20,
)
```

The six modulator classes:
- `M8AHDModulator` — Attack / Hold / Decay envelope
- `M8ADSRModulator` — Attack / Decay / Sustain / Release envelope
- `M8DrumModulator` — Peak / Body / Decay
- `M8LFOModulator` — shape / trigger_mode / freq / retrigger
- `M8TrigModulator` — Attack / Hold / Decay / Source
- `M8TrackingModulator` — Source / Low / High values

## EQ

Every project ships 132 EQ slots (1 global + 3 effect-section + 128 per-instrument). Each EQ has three bands (low / mid / high), each band has a filter type, stereo processing mode, frequency, gain, and Q:

```python
from m8.api.project import M8Project
from m8.api.eq import M8EqType, M8EqMode
from m8.api.instruments.wavsynth import M8Wavsynth

project = M8Project.initialise()

# Tweak the global EQ
project.eq[0].low.eq_type = M8EqType.LOWCUT
project.eq[0].mid.q = 0x80
project.eq[0].high.eq_mode = M8EqMode.SIDE

# Bind an instrument to EQ slot 4 (first per-instrument slot)
w = M8Wavsynth(name="EQUALIZED")
w.associated_eq = 4
project.instruments[0] = w

# Frequency and gain are 16-bit packed across two bytes; helpers decode:
print(project.eq[0].mid.frequency())   # Hz
print(project.eq[0].mid.gain_db())     # signed dB
```

Slot convention (matching m8-file-parser):
- `eq[0]` — global / master EQ
- `eq[1..3]` — effect-section EQs (chorus, delay, reverb)
- `eq[4..131]` — per-instrument EQs (referenced by `instrument.associated_eq`)
- `associated_eq = 0xFF` (default) means "no EQ bound to this instrument"

## Mixer and effects settings

```python
project = M8Project.initialise()

# Mixer — master, tracks, sends, DJ filter, limiter, OTT
project.mixer.master_volume = 0xC0
project.mixer.set_track_volume(0, 0xE0)   # 8 tracks; helper preferred over track_volume_0..7
project.mixer.chorus_volume = 0x40
project.mixer.dj_filter = 0xA0
project.mixer.dj_filter_type = 1
project.mixer.limiter_attack = 0x20    # firmware 6.0+
project.mixer.ott_level = 0x80          # firmware 6.2+

# Analog input is stereo by default (analog_mode = 0xFF). Set anything else
# to switch to dual-mono and address each side independently:
if project.mixer.is_analog_stereo:
    project.mixer.analog_l_volume = 0xC0
else:
    project.mixer.analog_l_volume = 0xC0
    project.mixer.analog_r_volume = 0xC0  # really analog_mode used as right-volume byte

# Effects — chorus / delay / reverb knobs + v6.2 shimmer & OTT shaping
project.effects.chorus_mod_depth = 0x40
project.effects.delay_feedback   = 0xA0
project.effects.reverb_size      = 0xC0
project.effects.reverb_shimmer   = 0x30  # firmware 6.2+
```

## FX commands

Phrases carry per-step FX tuples. Enum classes provide readable names:

```python
from m8.api.fx import M8FXTuple, M8SequenceFX, M8SamplerFX

step = M8PhraseStep(note=M8Note.C_4, velocity=0x6F, instrument=0x00)
step.fx[0] = M8FXTuple(key=M8SequenceFX.RET, value=0x40)  # Retrigger
step.fx[1] = M8FXTuple(key=M8SamplerFX.LEN, value=0xC0)   # Sample length
```

Available FX groups:
- `M8SequenceFX` — global timing/control (ARP, RET, HOP, KIL, TPO, …)
- `M8SamplerFX` — sampler-only (VOL, PIT, PLY, CUT, SLI, …)
- `M8ModulatorFX` — per-slot mod params (EA1–EA4, AT1–AT4, …)
- `M8MixerFX` — firmware 6.2 mixer/voice (VMV, XMM, XRH, OTT, …)

## Notes

`M8Note` is generated for C-1 through G-11:

```python
M8Note.C_4   # 36 (0x24)
M8Note.CS_4  # 37 (C♯4)
M8Note.G_11  # 127
```

M8's byte-0 origin is C1, so middle C = 36.

## Audio helpers

```python
# Chain multiple samples into one sliced WAV
from m8.tools.chain_builder import ChainBuilder
builder = ChainBuilder(sample_duration_ms=500, fade_ms=5, target_frame_rate=44100)
wav_data, slice_mapping = builder.build_chain(["kick.wav", "snare.wav", "hat.wav"])

# Add slice points to an existing WAV
from m8.tools.wav_slicer import WAVSlicer
slicer = WAVSlicer()
sliced = slicer.add_slice_points(wav_data, slice_points=[0, 22050, 44100, 66150])
```

## Demos

Runnable scripts under `demos/` produce `.m8s` files in `tmp/demos/`. Each demo demonstrates one library feature:

| Demo | Demonstrates |
|---|---|
| `demos/acid_303_wavsynth.py` | Wavsynth + iterating over instrument slots (16 shape variations) |
| `demos/acid_303_midi.py` | MIDIOut to monophonic external synth with OFF-note insertion |
| `demos/acid_909_sampler.py` | Sampler basics — multi-instrument drum kit |
| `demos/acid_909_chain.py` | Sample chain slicing |
| `demos/acid_909_midi.py` | MIDIOut drum kit (multi-channel) |
| `demos/euclid_sampler.py` | Bjorklund Euclidean rhythms |
| `demos/chords_synth.py` | Macrosynth + modulators + 3-voice polyphony |

Run a demo:

```bash
# Sample-based demos need samples first
PYTHONPATH=. python demos/utils/download_erica_pico_samples.py

PYTHONPATH=. python demos/acid_909_sampler.py
PYTHONPATH=. python demos/chords_synth.py
```

### Shipping demos to the M8

`tools/sync.py` covers the whole loop. Run with no args for status:

```bash
python tools/sync.py                       # status: local vs remote
python tools/sync.py push                  # copy all to /Volumes/M8/...
python tools/sync.py push acid-303         # filter by substring
python tools/sync.py push --test           # use tmp/virtual-m8/ for dry runs
python tools/sync.py clean local           # remove tmp/demos/
python tools/sync.py clean remote          # remove /Volumes/M8/Songs/pym8-demos/
```

`-f` skips per-item prompts. Non-interactive stdin auto-confirms.

## Project layout

```
m8/
├── api/
│   ├── project.py        # M8Project — top-level container
│   ├── instrument.py     # M8Instrument base + M8Instruments collection
│   ├── fields.py         # ByteField / BytesField / StringField descriptors
│   ├── modulator.py      # 6 modulator subclasses + M8Modulators
│   ├── eq.py             # M8EqBand / M8Eq / M8Eqs (3-band parametric)
│   ├── settings.py       # M8MixerSettings / M8EffectsSettings
│   ├── phrase.py         # M8Phrase / M8PhraseStep / M8Note
│   ├── chain.py          # M8Chain / M8ChainStep
│   ├── song.py           # M8SongMatrix (255 rows × 8 tracks)
│   ├── fx.py             # FX tuples + Sequence/Sampler/Mixer/Modulator FX enums
│   ├── metadata.py       # M8Metadata
│   ├── version.py        # M8Version + ordered comparison
│   └── instruments/
│       ├── wavsynth.py    # M8Wavsynth          (type 0)
│       ├── macrosynth.py  # M8Macrosynth        (type 1)
│       ├── sampler.py     # M8Sampler           (type 2)
│       ├── midiout.py     # M8MIDIOut           (type 3) — 10 MIDI CC slots
│       ├── fmsynth.py     # M8FMSynth           (type 4)
│       ├── hypersynth.py  # M8HyperSynth        (type 5) — chord matrix
│       └── external.py    # M8External          (type 6) — audio in + 4 CC slots
├── tools/
│   ├── chain_builder.py  # Sliced sample chain WAV builder
│   └── wav_slicer.py     # WAV slice-point writer
└── templates/            # TEMPLATE-6-2-1.m8s — bundled firmware-6.2 starting point

demos/                    # Runnable scripts by category
tests/                    # Mirrors m8/ layout — unittest
tools/sync.py             # Unified push / clean / status for demos
```

## Development

Run all tests with the stdlib runner:

```bash
python -m unittest discover -s tests -p '*.py'
```

Tests use `unittest` (not pytest). Each test file mirrors the module it covers; cross-cutting per-type tests live in `tests/api/instruments.py` and `tests/api/modulator.py`.

## File format references

- **[m8-file-parser](https://github.com/Twinside/m8-file-parser)** (Rust) — authoritative spec. Offsets, FX command codes, instrument layouts, version-conditional reads. pym8 is a port of this.
- **[m8-js](https://github.com/whitlockjc/m8-js)** — JavaScript implementation. Useful for enum lookups, but it targets firmware 4.0 and is not maintained — don't take binary offsets from it.
- **[m8-files](https://github.com/AlexCharlton/m8-files)** — older Rust parser; predecessor of m8-file-parser.
- **[Dirtywave M8](https://dirtywave.com/products/m8-tracker)** — official hardware.

## License

MIT.

## Credits

Created by jhw (justin.worrall@gmail.com). Heavily indebted to [Twinside](https://github.com/Twinside) for m8-file-parser, [whitlockjc](https://github.com/whitlockjc) for m8-js, [AlexCharlton](https://github.com/AlexCharlton) for m8-files, and [Dirtywave](https://dirtywave.com/) for the M8 itself.
