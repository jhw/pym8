#!/usr/bin/env python3
"""Demo: merge two source projects into one destination via the remapper.

Builds two small "source" projects in memory:
  - Source A: a drum kit on chain 0 (Wavsynth kick + snare)
  - Source B: a bass line on chain 0 (Wavsynth saw lead)

Both source projects use slot 0 for their chain, slot 0 for their first
instrument, etc. — they'd collide on a naive byte-copy. The remapper
allocates collision-free destination slots, rewrites every reference,
and the merged project plays both alongside each other.

Output: tmp/demos/remap_merge/MERGED.m8s
"""
from pathlib import Path

from m8.api.chain import M8ChainStep
from m8.api.instruments.wavsynth import M8Wavsynth, M8WavShape
from m8.api.modulator import M8AHDModulator
from m8.api.phrase import M8Note, M8PhraseStep
from m8.api.project import M8Project
from m8.api.remapper import Remapper


PROJECT_NAME = "MERGED"
OUTPUT_DIR = Path("tmp/demos/remap_merge")
BPM = 128


def build_drum_kit():
    """Source A: a 2-instrument drum kit on chain 0.

    Layout:
      instrument 0: kick (square)
      instrument 1: snare (noise)
      phrase 0: 4-on-the-floor kick + backbeat snare
      chain 0: phrase 0
    """
    p = M8Project.initialise()
    p.metadata.name = "DRUMS"
    p.metadata.tempo = BPM

    kick = M8Wavsynth(name="KICK")
    kick.shape = M8WavShape.PULSE50
    kick.pitch = 0x18
    kick.cutoff = 0xC0
    # Short decay envelope on volume — makes it a thump rather than a tone
    kick.modulators[0] = M8AHDModulator(
        destination=1,  # VOLUME
        amount=0xFF,
        attack=0x00, hold=0x00, decay=0x18,
    )
    p.instruments[0] = kick

    snare = M8Wavsynth(name="SNARE")
    snare.shape = M8WavShape.NOISE
    snare.cutoff = 0x80
    snare.modulators[0] = M8AHDModulator(
        destination=1, amount=0xFF, attack=0x00, hold=0x00, decay=0x28,
    )
    p.instruments[1] = snare

    phrase = p.phrases[0]
    for step in (0, 4, 8, 12):
        phrase[step] = M8PhraseStep(
            note=M8Note.C_4, velocity=0x7F, instrument=0,
        )
    for step in (4, 12):
        phrase[step] = M8PhraseStep(
            note=M8Note.E_4, velocity=0x7F, instrument=1,
        )

    p.chains[0][0] = M8ChainStep(phrase=0, transpose=0)
    return p


def build_bassline():
    """Source B: a single-instrument bass line on chain 0.

    Layout:
      instrument 0: bass (saw)
      phrase 0: a simple two-note pattern
      chain 0: phrase 0
    """
    p = M8Project.initialise()
    p.metadata.name = "BASS"
    p.metadata.tempo = BPM

    bass = M8Wavsynth(name="BASS")
    bass.shape = M8WavShape.SAW
    bass.cutoff = 0x70
    bass.resonance = 0x60
    bass.pitch = 0x00
    p.instruments[0] = bass

    phrase = p.phrases[0]
    notes = [(0, M8Note.C_2), (4, M8Note.C_2), (8, M8Note.GS_2), (12, M8Note.C_2)]
    for step_idx, note in notes:
        phrase[step_idx] = M8PhraseStep(note=note, velocity=0x7F, instrument=0)

    p.chains[0][0] = M8ChainStep(phrase=0, transpose=0)
    return p


def merge(drums, bass):
    """Import drums on track 0 and bass on track 1 of a fresh project."""
    merged = M8Project.initialise()
    merged.metadata.name = PROJECT_NAME
    merged.metadata.tempo = BPM

    # Import drum chain 0 — walker pulls phrase 0 and instruments 0+1.
    # Allocator finds them collision-free destination slots (the fresh
    # merged project has everything empty, so they'll land at 0, 0, 0+1).
    drum_remap = Remapper(drums, merged, chains={0})
    drum_remap.apply()
    drum_chain_dst = drum_remap.remap.out_chain(0)

    print(f"drums imported:")
    print(f"  chain 0 -> {drum_chain_dst}")
    print(f"  phrase  -> {drum_remap.remap.phrases}")
    print(f"  instr   -> {drum_remap.remap.instruments}")

    # Now import bass chain 0. Slots 0 (chain), 0 (phrase), 0 (instrument)
    # are taken by the drums — the remapper will find alternates.
    bass_remap = Remapper(bass, merged, chains={0})
    bass_remap.apply()
    bass_chain_dst = bass_remap.remap.out_chain(0)

    print(f"bass imported:")
    print(f"  chain 0 -> {bass_chain_dst}")
    print(f"  phrase  -> {bass_remap.remap.phrases}")
    print(f"  instr   -> {bass_remap.remap.instruments}")

    # Wire up the song matrix: drums on track 0, bass on track 1, repeated
    # for 8 rows so there's something to play.
    for row in range(8):
        merged.song[row][0] = drum_chain_dst
        merged.song[row][1] = bass_chain_dst

    return merged


def main():
    print("Building source projects...")
    drums = build_drum_kit()
    bass = build_bassline()

    print("\nMerging via Remapper...\n")
    merged = merge(drums, bass)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{PROJECT_NAME}.m8s"
    merged.write_to_file(str(out_path))

    print(f"\n✓ Wrote {out_path}")
    print(f"  song matrix: drums on track 0, bass on track 1, 8 rows")
    print(f"  ship to your M8 with: python tools/sync.py push remap-merge")


if __name__ == "__main__":
    main()
