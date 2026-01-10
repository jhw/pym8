#!/usr/bin/env python
"""
MIDI Chord Demo - Kraftwerk "Computer World" style triads

Creates an M8 project that plays 4 chord triads through External MIDI instruments.
Designed for Roland JU-06A or similar polyphonic synthesizer.

Structure:
- 3 chains (00, 01, 02) on song row 0 (one for each voice of the triad)
- Each chain has 4 phrases (one per chord)
- 3 External instruments (configurable MIDI channel via --midi-channel, default: 1)

Chord progression (Am - F - C - G):
- Phrase 00/04/08: Am (A3, C4, E4)
- Phrase 01/05/09: F  (F3, A3, C4)
- Phrase 02/06/0A: C  (C4, E4, G4)
- Phrase 03/07/0B: G  (G3, B3, D4)

================================================================================
ROLAND JU-06A SETUP INSTRUCTIONS
================================================================================

Before running this demo, configure your JU-06A as follows:

1. SET MIDI CLOCK TO EXTERNAL (USB)
   --------------------------------
   The JU-06A must sync to MIDI clock from the M8, not its internal clock.

   - Hold down the ARPEGGIO [ON/OFF] button
   - While holding, press button [3] (Clock Source)
   - Turn the [VALUE] knob to select "USb" (USB) if connected via USB,
     or "MId" (MIDI) if using 5-pin DIN MIDI cable
   - Press ARPEGGIO [ON/OFF] again to confirm and exit

   Clock source options:
     At  = AUTO (syncs automatically if clock detected - default)
     Int = INTERNAL (ignores external clock)
     MId = MIDI (sync to MIDI IN connector)
     USb = USB (sync to USB port)

2. SET MIDI CHANNEL TO 1
   ----------------------
   The demo sends notes on MIDI channel 1. The JU-06A must receive on the
   same channel.

   - Hold down the ARPEGGIO [ON/OFF] button
   - While holding, press button [2] (MIDI Channel)
   - Turn the [VALUE] knob to select "1"
   - Press ARPEGGIO [ON/OFF] again to confirm and exit

3. SELECT A PATTERN
   ------------------
   The JU-06A has 8 banks with 8 patches each. Patterns are stored per-patch.

   - Press BANK [1]-[4] to select banks 1-4
   - Press the same BANK button again to toggle to banks 5-8
     (e.g., press [1] twice to switch between bank 1 and bank 5)
   - Press PATCH [1]-[8] to select a patch within the current bank

   Alternative: Hold [START] and turn [VALUE] knob to scroll through patterns.

4. CLEAR THE CURRENT PATTERN
   --------------------------
   The JU-06A's internal sequencer should be empty, otherwise it will play
   its own notes on top of what the M8 sends.

   - Press the [EDIT] button to enter edit mode
   - Any lit buttons indicate notes on those steps
   - Turn off all lit buttons
   - Press [EDIT] again to exit edit mode

Reference: Roland JU-06A Owner's Manual (PDF)
         https://static.roland.com/assets/media/pdf/JU-06A_eng02_W.pdf
================================================================================
"""

import argparse
from pathlib import Path

from m8.api.project import M8Project
from m8.api.instruments.external import M8External, M8ExternalParam, M8ExternalPort
from m8.api.phrase import OFF_NOTE

# Configuration
PROJECT_NAME = "MIDI-CHORD"
OUTPUT_DIR = Path("tmp/demos/chords/midi")

# MIDI note values
A3 = 57
B3 = 59
C4 = 60
D4 = 62
E4 = 64
F3 = 53
G3 = 55
G4 = 67

# Chord definitions (root, third, fifth)
CHORDS = [
    (A3, C4, E4),   # Am
    (F3, A3, C4),   # F
    (C4, E4, G4),   # C
    (G3, B3, D4),   # G
]


def create_external_instrument(name, midi_channel=1):
    """Create an External instrument configured for MIDI output."""
    inst = M8External()
    inst.name = name
    inst.set(M8ExternalParam.PORT, M8ExternalPort.MIDI)  # Hardware MIDI output
    inst.set(M8ExternalParam.CHANNEL, midi_channel)
    inst.set(M8ExternalParam.BANK, 0)
    inst.set(M8ExternalParam.PROGRAM, 0)
    return inst


def main():
    parser = argparse.ArgumentParser(description="MIDI Chord Demo - Kraftwerk style triads")
    parser.add_argument(
        "--midi-channel", "-c",
        type=int,
        default=1,
        choices=range(1, 17),
        metavar="1-16",
        help="MIDI channel for external instruments (default: 1)"
    )
    args = parser.parse_args()

    # Initialize project from template
    project = M8Project.initialise()

    # Create 3 External instruments (one per voice/chain)
    voice_names = ["ROOT", "3RD", "5TH"]
    for i, name in enumerate(voice_names):
        inst = create_external_instrument(f"CHORD-{name}", midi_channel=args.midi_channel)
        project.instruments[i] = inst

    # Create phrases
    # Chain 00 (voice 1 - root): phrases 00-03, instrument 00
    # Chain 01 (voice 2 - third): phrases 04-07, instrument 01
    # Chain 02 (voice 3 - fifth): phrases 08-0B, instrument 02

    for chord_idx, chord in enumerate(CHORDS):
        root, third, fifth = chord

        # Phrase for voice 1 (root note) - uses instrument 00
        phrase_v1 = chord_idx  # 00, 01, 02, 03
        project.phrases[phrase_v1][0].note = root
        project.phrases[phrase_v1][0].instrument = 0
        project.phrases[phrase_v1][0].velocity = 0x7F
        project.phrases[phrase_v1][8].note = OFF_NOTE  # Note off at step 8

        # Phrase for voice 2 (third) - uses instrument 01
        phrase_v2 = chord_idx + 4  # 04, 05, 06, 07
        project.phrases[phrase_v2][0].note = third
        project.phrases[phrase_v2][0].instrument = 1
        project.phrases[phrase_v2][0].velocity = 0x7F
        project.phrases[phrase_v2][8].note = OFF_NOTE

        # Phrase for voice 3 (fifth) - uses instrument 02
        phrase_v3 = chord_idx + 8  # 08, 09, 0A, 0B
        project.phrases[phrase_v3][0].note = fifth
        project.phrases[phrase_v3][0].instrument = 2
        project.phrases[phrase_v3][0].velocity = 0x7F
        project.phrases[phrase_v3][8].note = OFF_NOTE

    # Create chains
    # Chain 00: phrases 00, 01, 02, 03 (root notes)
    for i in range(4):
        project.chains[0][i].phrase = i

    # Chain 01: phrases 04, 05, 06, 07 (thirds)
    for i in range(4):
        project.chains[1][i].phrase = i + 4

    # Chain 02: phrases 08, 09, 0A, 0B (fifths)
    for i in range(4):
        project.chains[2][i].phrase = i + 8

    # Set up song row 0 with all three chains
    project.song[0][0] = 0  # Track 1: root notes
    project.song[0][1] = 1  # Track 2: thirds
    project.song[0][2] = 2  # Track 3: fifths

    # Write the project
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{PROJECT_NAME}.m8s"
    project.validate()
    project.write_to_file(str(output_path))

    print("MIDI Chord Demo - Kraftwerk 'Computer World' Style")
    print("=" * 50)
    print()
    print("Project written to:", output_path)
    print()
    print(f"Instruments (all on MIDI Ch {args.midi_channel}):")
    for i in range(3):
        inst = project.instruments[i]
        print(f"  {i:02X}: {inst.name}")
    print()
    print("Chord Progression (Am - F - C - G):")
    chord_names = ["Am", "F", "C", "G"]
    for name, chord in zip(chord_names, CHORDS):
        print(f"  {name}: {chord[0]} {chord[1]} {chord[2]} (MIDI notes)")
    print()
    print("Song Structure:")
    print("  Row 0: Chain 00 (roots) | Chain 01 (thirds) | Chain 02 (fifths)")
    print()
    print("Each chain plays 4 phrases (one per chord).")
    print("Notes trigger at step 0, note-off at step 8.")


if __name__ == "__main__":
    main()
