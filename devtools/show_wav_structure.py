#!/usr/bin/env python3

import sys
import os
import struct
import argparse

def read_file_bytes(filename):
    with open(filename, 'rb') as f:
        return f.read()

def analyze_wav_structure(data):
    """Analyze RIFF/WAVE file structure and return formatted output."""
    if data[:4] != b'RIFF':
        return ["Not a RIFF file"]
    
    result = []
    result.append(f"File size: {len(data)} bytes")
    
    # Parse RIFF header
    riff_size = struct.unpack('<I', data[4:8])[0]
    result.append(f"RIFF header:")
    result.append(f"  ID: 'RIFF'")
    result.append(f"  Size: {riff_size} bytes")
    result.append(f"  Format: '{data[8:12].decode('ascii', errors='replace')}'")
    
    # If not a WAVE file, stop
    if data[8:12] != b'WAVE':
        result.append("Not a WAVE file")
        return result
    
    # Parse chunks
    pos = 12  # Start after RIFF header and WAVE identifier
    chunk_index = 0
    
    result.append("\nChunk structure:")
    while pos < len(data):
        chunk_index += 1
        # Need at least 8 bytes for chunk header
        if pos + 8 > len(data):
            result.append(f"  Incomplete chunk at offset {pos}")
            break
            
        # Get chunk ID and size
        chunk_id = data[pos:pos+4]
        chunk_size = struct.unpack('<I', data[pos+4:pos+8])[0]
        
        try:
            chunk_id_str = chunk_id.decode('ascii', errors='replace')
        except:
            chunk_id_str = str(chunk_id)
        
        # Add chunk info to result
        result.append(f"  Chunk #{chunk_index}: '{chunk_id_str}'")
        result.append(f"    Offset: 0x{pos:08x} ({pos})")
        result.append(f"    Size: {chunk_size} bytes")
        result.append(f"    Data offset: 0x{pos+8:08x} ({pos+8})")
        
        # Add format chunk details if applicable
        if chunk_id == b'fmt ':
            if chunk_size >= 16:
                fmt_chunk = data[pos+8:pos+8+16]
                audio_format = struct.unpack('<H', fmt_chunk[0:2])[0]
                num_channels = struct.unpack('<H', fmt_chunk[2:4])[0]
                sample_rate = struct.unpack('<I', fmt_chunk[4:8])[0]
                byte_rate = struct.unpack('<I', fmt_chunk[8:12])[0]
                block_align = struct.unpack('<H', fmt_chunk[12:14])[0]
                bits_per_sample = struct.unpack('<H', fmt_chunk[14:16])[0]
                
                result.append(f"    Format: {audio_format} ({get_format_name(audio_format)})")
                result.append(f"    Channels: {num_channels}")
                result.append(f"    Sample rate: {sample_rate} Hz")
                result.append(f"    Byte rate: {byte_rate} bytes/sec")
                result.append(f"    Block align: {block_align} bytes")
                result.append(f"    Bits per sample: {bits_per_sample}")
        
        # Add cue chunk details if applicable
        elif chunk_id == b'cue ':
            if chunk_size >= 4:
                cue_point_count = struct.unpack('<I', data[pos+8:pos+12])[0]
                result.append(f"    Cue points: {cue_point_count}")
                
                # Optionally add details for each cue point
                cue_offset = pos + 12
                for i in range(cue_point_count):
                    if cue_offset + 24 <= len(data):
                        cue_id = struct.unpack('<I', data[cue_offset:cue_offset+4])[0]
                        position = struct.unpack('<I', data[cue_offset+4:cue_offset+8])[0]
                        data_chunk_id = data[cue_offset+8:cue_offset+12].decode('ascii', errors='replace')
                        sample_offset = struct.unpack('<I', data[cue_offset+20:cue_offset+24])[0]
                        
                        result.append(f"      Cue #{i+1}:")
                        result.append(f"        ID: {cue_id}")
                        result.append(f"        Position: {position}")
                        result.append(f"        Chunk ID: '{data_chunk_id}'")
                        result.append(f"        Sample Offset: {sample_offset}")
                        
                        cue_offset += 24
        
        # Move to next chunk (add padding byte if chunk size is odd)
        next_pos = pos + 8 + chunk_size
        if chunk_size % 2:
            next_pos += 1
        
        if next_pos <= pos:
            result.append(f"  Error: Invalid chunk size or overflow")
            break
            
        pos = next_pos
    
    return result

def get_format_name(format_code):
    formats = {
        0x0001: "PCM",
        0x0003: "IEEE float",
        0x0006: "A-law",
        0x0007: "μ-law",
        0xFFFE: "Extensible"
    }
    return formats.get(format_code, "Unknown")

def main():
    parser = argparse.ArgumentParser(description='Show WAV file RIFF structure')
    parser.add_argument('files', nargs='+', help='WAV file(s) to analyze')
    args = parser.parse_args()
    
    for filename in args.files:
        if not os.path.exists(filename):
            print(f"Error: File '{filename}' not found")
            continue
            
        print(f"\n=== WAV Structure: {filename} ===")
        
        try:
            data = read_file_bytes(filename)
            structure = analyze_wav_structure(data)
            
            for line in structure:
                print(line)
                
        except Exception as e:
            print(f"Error analyzing file: {str(e)}")

if __name__ == "__main__":
    main()