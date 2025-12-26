#!/usr/bin/env python
"""
Create a test FM synth to verify parameter mapping.

This creates an FM synth with very specific, distinctive parameter values
that should be easy to verify on the M8 hardware.

PARAMETER SETTINGS (for user verification on M8):
==================================================

COMMON PARAMETERS:
- Name: "FMTEST"
- Transpose: 0x00 (0)
- Table Tick: 0x01 (1)
- Volume: 0x80 (128)
- Pitch: 0x00 (0)
- Fine Tune: 0x80 (128, centered)

FM ALGORITHM:
- Algo: 0x07 (A>B + C>D) - Two independent pairs

OPERATORS (A, B, C, D):
- Operator A:
  - Shape: 0x00 (SIN)
  - Ratio: 01.10 (ratio=1, ratio_fine=10)
  - Level: 0xA0 (160)
  - Feedback: 0xA1 (161)

- Operator B:
  - Shape: 0x06 (TRI)
  - Ratio: 02.20 (ratio=2, ratio_fine=20)
  - Level: 0xB0 (176)
  - Feedback: 0xB1 (177)

- Operator C:
  - Shape: 0x07 (SAW)
  - Ratio: 03.30 (ratio=3, ratio_fine=30)
  - Level: 0xC0 (192)
  - Feedback: 0xC1 (193)

- Operator D:
  - Shape: 0x08 (SQR)
  - Ratio: 04.40 (ratio=4, ratio_fine=40)
  - Level: 0xD0 (208)
  - Feedback: 0xD1 (209)

FILTER:
- Filter Type: 0x01 (LOWPASS)
- Cutoff: 0x77 (119)
- Resonance: 0x88 (136)

MIXER:
- Amp: 0x33 (51)
- Limiter: 0x01 (SIN)
- Pan: 0x80 (128, centered)
- Dry: 0xCC (204)
- Chorus Send: 0x55 (85)
- Delay Send: 0x66 (102)
- Reverb Send: 0x99 (153)

OPERATOR MODULATION ROUTING (operator MOD table):
- Operator A mod_a: 0x01 (1/LEV - Modulator 1 → Level)
- Operator B mod_a: 0x06 (2/RAT - Modulator 2 → Ratio)
- Operator C mod_a: 0x0B (3/PIT - Modulator 3 → Pitch)
- Operator D mod_a: 0x10 (4/FBK - Modulator 4 → Feedback)
- All mod_b: 0x00 (OFF)

MOD1-4 AMOUNTS (separate from operator table):
- MOD1: 0x80 (128)
- MOD2: 0x80 (128)
- MOD3: 0x80 (128)
- MOD4: 0x80 (128)

M8 MODULATORS (modulator destinations):
- Modulator 1: destination = 0x01 (VOLUME)
- Modulator 2: destination = 0x02 (PITCH)
- Modulator 3: destination = 0x07 (CUTOFF)
- Modulator 4: destination = 0x09 (AMP)

Output: tmp/FMSYNTH-TEST.m8s
"""

from pathlib import Path
from m8.api.project import M8Project
from m8.api.instruments.fmsynth import (
    M8FMSynth, M8FMSynthParam, M8FMAlgo, M8FMWave, M8FMSynthModDest, M8FMOperatorModDest
)
from m8.api.instrument import M8FilterType, M8LimiterType

OUTPUT_DIR = Path("tmp")
PROJECT_NAME = "FMSYNTH-TEST"

def create_test_fmsynth():
    """Create FM synth with distinctive parameter values."""
    print("Creating test FM synth...")
    print()

    # Create FM synth
    fmsynth = M8FMSynth(name="FMTEST")

    # Common parameters
    fmsynth.set(M8FMSynthParam.TRANSPOSE, 0x00)
    fmsynth.set(M8FMSynthParam.TABLE_TICK, 0x01)
    fmsynth.set(M8FMSynthParam.VOLUME, 0x80)
    fmsynth.set(M8FMSynthParam.PITCH, 0x00)
    fmsynth.set(M8FMSynthParam.FINE_TUNE, 0x80)

    # Algorithm - A>B + C>D (two pairs)
    fmsynth.set(M8FMSynthParam.ALGO, M8FMAlgo.A_B_C_D_TWO_PAIR)
    print(f"Algorithm: {M8FMAlgo.A_B_C_D_TWO_PAIR.name} (0x{M8FMAlgo.A_B_C_D_TWO_PAIR:02X})")

    # Operator A
    fmsynth.set(M8FMSynthParam.OP_A_SHAPE, M8FMWave.SIN)
    fmsynth.set(M8FMSynthParam.OP_A_RATIO, 1)
    fmsynth.set(M8FMSynthParam.OP_A_RATIO_FINE, 10)
    fmsynth.set(M8FMSynthParam.OP_A_LEVEL, 0xA0)
    fmsynth.set(M8FMSynthParam.OP_A_FEEDBACK, 0xA1)
    print(f"Operator A: shape=SIN, ratio=01.10, level=0xA0, feedback=0xA1")

    # Operator B
    fmsynth.set(M8FMSynthParam.OP_B_SHAPE, M8FMWave.TRI)
    fmsynth.set(M8FMSynthParam.OP_B_RATIO, 2)
    fmsynth.set(M8FMSynthParam.OP_B_RATIO_FINE, 20)
    fmsynth.set(M8FMSynthParam.OP_B_LEVEL, 0xB0)
    fmsynth.set(M8FMSynthParam.OP_B_FEEDBACK, 0xB1)
    print(f"Operator B: shape=TRI, ratio=02.20, level=0xB0, feedback=0xB1")

    # Operator C
    fmsynth.set(M8FMSynthParam.OP_C_SHAPE, M8FMWave.SAW)
    fmsynth.set(M8FMSynthParam.OP_C_RATIO, 3)
    fmsynth.set(M8FMSynthParam.OP_C_RATIO_FINE, 30)
    fmsynth.set(M8FMSynthParam.OP_C_LEVEL, 0xC0)
    fmsynth.set(M8FMSynthParam.OP_C_FEEDBACK, 0xC1)
    print(f"Operator C: shape=SAW, ratio=03.30, level=0xC0, feedback=0xC1")

    # Operator D
    fmsynth.set(M8FMSynthParam.OP_D_SHAPE, M8FMWave.SQR)
    fmsynth.set(M8FMSynthParam.OP_D_RATIO, 4)
    fmsynth.set(M8FMSynthParam.OP_D_RATIO_FINE, 40)
    fmsynth.set(M8FMSynthParam.OP_D_LEVEL, 0xD0)
    fmsynth.set(M8FMSynthParam.OP_D_FEEDBACK, 0xD1)
    print(f"Operator D: shape=SQR, ratio=04.40, level=0xD0, feedback=0xD1")

    # Filter
    fmsynth.set(M8FMSynthParam.FILTER_TYPE, M8FilterType.LOWPASS)
    fmsynth.set(M8FMSynthParam.CUTOFF, 0x77)
    fmsynth.set(M8FMSynthParam.RESONANCE, 0x88)
    print(f"Filter: type=LOWPASS, cutoff=0x77, resonance=0x88")

    # Mixer
    fmsynth.set(M8FMSynthParam.AMP, 0x33)
    fmsynth.set(M8FMSynthParam.LIMIT, M8LimiterType.SIN)
    fmsynth.set(M8FMSynthParam.PAN, 0x80)
    fmsynth.set(M8FMSynthParam.DRY, 0xCC)
    fmsynth.set(M8FMSynthParam.CHORUS_SEND, 0x55)
    fmsynth.set(M8FMSynthParam.DELAY_SEND, 0x66)
    fmsynth.set(M8FMSynthParam.REVERB_SEND, 0x99)
    print(f"Mixer: amp=0x33, limit=SIN, pan=0x80, dry=0xCC")
    print(f"Sends: chorus=0x55, delay=0x66, reverb=0x99")

    # Operator modulation routing (mod_a for each operator)
    # Set distinctive values: A=MOD1_LEV, B=MOD2_RAT, C=MOD3_PIT, D=MOD4_FBK
    fmsynth.set(M8FMSynthParam.OP_A_MOD_A, M8FMOperatorModDest.MOD1_LEV)
    fmsynth.set(M8FMSynthParam.OP_B_MOD_A, M8FMOperatorModDest.MOD2_RAT)
    fmsynth.set(M8FMSynthParam.OP_C_MOD_A, M8FMOperatorModDest.MOD3_PIT)
    fmsynth.set(M8FMSynthParam.OP_D_MOD_A, M8FMOperatorModDest.MOD4_FBK)
    print(f"Operator mod_a: A=1/LEV, B=2/RAT, C=3/PIT, D=4/FBK")

    # Leave mod_b at default (OFF)
    print(f"Operator mod_b: all OFF (default)")

    # Set MOD1-4 amounts to 0x80 (to verify they work)
    fmsynth.set(M8FMSynthParam.MOD1_VALUE, 0x80)
    fmsynth.set(M8FMSynthParam.MOD2_VALUE, 0x80)
    fmsynth.set(M8FMSynthParam.MOD3_VALUE, 0x80)
    fmsynth.set(M8FMSynthParam.MOD4_VALUE, 0x80)
    print(f"MOD1-4 amounts: all 0x80 (128)")

    # Modulators - set destinations only (leave amounts at 0)
    fmsynth.modulators[0].destination = M8FMSynthModDest.VOLUME
    fmsynth.modulators[1].destination = M8FMSynthModDest.PITCH
    fmsynth.modulators[2].destination = M8FMSynthModDest.CUTOFF
    fmsynth.modulators[3].destination = M8FMSynthModDest.AMP
    print(f"M8 Modulators: 1=VOLUME, 2=PITCH, 3=CUTOFF, 4=AMP")

    return fmsynth


def main():
    """Create project and save to file."""
    print("=" * 70)
    print(f"Creating {PROJECT_NAME}.m8s")
    print("=" * 70)
    print()

    # Create project
    project = M8Project.initialise()
    project.metadata.name = PROJECT_NAME
    project.metadata.tempo = 120.0
    project.metadata.directory = "/Songs/pym8-tests/"

    # Create test FM synth
    fmsynth = create_test_fmsynth()

    # Add to project as instrument 0x00
    project.instruments[0x00] = fmsynth

    # Save to file
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / f"{PROJECT_NAME}.m8s"

    print()
    print(f"Saving to: {output_path}")
    project.write_to_file(str(output_path))

    print()
    print("=" * 70)
    print("✓ File created successfully!")
    print("=" * 70)
    print()
    print("VERIFICATION CHECKLIST:")
    print("-" * 70)
    print("Load this file on your M8 and verify instrument 0x00:")
    print()
    print("1. Name should be: FMTEST")
    print("2. Algorithm should be: [A>B]+[C>D] (0x07)")
    print("3. Operator shapes: A=SIN, B=TRI, C=SAW, D=SQR")
    print("4. Operator ratios: A=01.10, B=02.20, C=03.30, D=04.40")
    print("5. Operator levels: A=0xA0, B=0xB0, C=0xC0, D=0xD0")
    print("6. Operator feedback: A=0xA1, B=0xB1, C=0xC1, D=0xD1")
    print("7. Filter: LOWPASS, cutoff=0x77, res=0x88")
    print("8. Mixer: amp=0x33, limit=SIN, pan=0x80, dry=0xCC")
    print("9. Sends: chorus=0x55, delay=0x66, reverb=0x99")
    print("10. Operator MOD table: A=1/LEV, B=2/RAT, C=3/PIT, D=4/FBK (second slot all --)")
    print("11. MOD1-4 amounts: all 0x80 (128)")
    print("12. M8 Mod destinations: 1=VOLUME, 2=PITCH, 3=CUTOFF, 4=AMP")
    print()
    print("Report any mismatches and I'll adjust the parameter offsets!")
    print("=" * 70)


if __name__ == '__main__':
    main()
