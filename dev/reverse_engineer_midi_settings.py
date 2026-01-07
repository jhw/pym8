#!/usr/bin/env python
"""
Reverse engineer MIDI settings location in M8 project files.

Based on m8-file-parser MidiSettings struct:
- receive_sync (bool)
- receive_transport (u8)
- send_sync (bool)
- send_transport (u8)
- record_note_channel (u8)
- record_note_velocity (bool)
- record_note_delay_kill_commands (u8)
- control_map_channel (u8)
- song_row_cue_channel (u8)
- track_input_channel [u8; 8]
- track_input_instrument [u8; 8]
- track_input_program_change (bool)
- track_input_mode (u8)

MIDI settings should be after metadata (offset 14, size 147) = starts at 161
"""

import sys
from pathlib import Path

# Known offsets
METADATA_OFFSET = 14
METADATA_SIZE = 147
MIDI_SETTINGS_EXPECTED_OFFSET = METADATA_OFFSET + METADATA_SIZE  # 161

# Read template file
template_path = Path(__file__).parent.parent / "m8/templates/TEMPLATE-6-2-1.m8s"

with open(template_path, 'rb') as f:
    data = f.read()

print(f"File size: {len(data)} bytes")
print(f"Expected MIDI settings offset: {MIDI_SETTINGS_EXPECTED_OFFSET}")
print()

# Show bytes around the expected MIDI settings location
start = MIDI_SETTINGS_EXPECTED_OFFSET
print(f"Bytes at offset {start} (0x{start:X}):")
for i in range(0, 64, 16):
    offset = start + i
    hex_str = ' '.join(f'{b:02X}' for b in data[offset:offset+16])
    print(f"  {offset:3d} (0x{offset:02X}): {hex_str}")

print()
print("Expected structure (from m8-file-parser):")
print("  0: receive_sync (bool)")
print("  1: receive_transport (u8) - 0=OFF, 1=PATTERN, 2=SONG")
print("  2: send_sync (bool)")
print("  3: send_transport (u8) - 0=OFF, 1=PATTERN, 2=SONG")
print("  4: record_note_channel (u8)")
print("  5: record_note_velocity (bool)")
print("  6: record_note_delay_kill_commands (u8)")
print("  7: control_map_channel (u8)")
print("  8: song_row_cue_channel (u8)")
print("  9-16: track_input_channel [u8; 8]")
print("  17-24: track_input_instrument [u8; 8]")
print("  25: track_input_program_change (bool)")
print("  26: track_input_mode (u8)")
print()

# Analyze the bytes
midi_data = data[start:start+64]
print("Parsed values:")
print(f"  receive_sync:        {midi_data[0]} ({'ON' if midi_data[0] else 'OFF'})")
print(f"  receive_transport:   {midi_data[1]} ({['OFF', 'PATTERN', 'SONG'][midi_data[1]] if midi_data[1] < 3 else 'UNKNOWN'})")
print(f"  send_sync:           {midi_data[2]} ({'ON' if midi_data[2] else 'OFF'})")
print(f"  send_transport:      {midi_data[3]} ({['OFF', 'PATTERN', 'SONG'][midi_data[3]] if midi_data[3] < 3 else 'UNKNOWN'})")
print(f"  record_note_channel: {midi_data[4]}")
print(f"  record_note_velocity:{midi_data[5]} ({'ON' if midi_data[5] else 'OFF'})")
print(f"  record_delay_kill:   {midi_data[6]}")
print(f"  control_map_channel: {midi_data[7]}")
print(f"  song_row_cue_channel:{midi_data[8]}")
print(f"  track_input_channel: {list(midi_data[9:17])}")
print(f"  track_input_instr:   {list(midi_data[17:25])}")
print(f"  track_input_pc:      {midi_data[25]} ({'ON' if midi_data[25] else 'OFF'})")
print(f"  track_input_mode:    {midi_data[26]}")
