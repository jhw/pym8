#!/usr/bin/env python
"""
Script to inspect FMSYNTHS m8i files.
Iterates through all m8i files in the directory and extracts parameter bytes:
- Instrument ID is the base offset
- Algo is located 18 bytes after the instrument ID
- Shapes are the 4 bytes after algo
- Params 1 are the 8 bytes after shapes (decimal integers)
- Params 2 are the 8 bytes after params 1 (hex)
- Params 3 are the 4 bytes after params 2 (hex)
"""

import os
import sys
import struct
from pathlib import Path

def hexdump(data, offset, length=64):
    """Generate a hexdump of the data starting at offset"""
    result = []
    for i in range(offset, min(offset + length, len(data)), 16):
        # Hex offset
        line = f"{i:08X}  "
        
        # Hex bytes
        hex_part = ""
        for j in range(i, min(i + 16, len(data))):
            hex_part += f"{data[j]:02X} "
        hex_part = hex_part.ljust(49)  # Padding for alignment
        line += hex_part
        
        # ASCII representation
        ascii_part = "|"
        for j in range(i, min(i + 16, len(data))):
            if 32 <= data[j] <= 126:  # Printable ASCII
                ascii_part += chr(data[j])
            else:
                ascii_part += "."
        ascii_part += "|"
        
        line += ascii_part
        result.append(line)
    
    return "\n".join(result)

def read_instrument_file(file_path):
    """Read an M8 instrument file and extract key information"""
    with open(file_path, 'rb') as f:
        data = f.read()
    
    # Read instrument type ID
    instrument_type_id = data[0]
    
    # For these m8i files, the actual name appears to be in the filename
    # Extract it from the file name instead of trying to parse it from the file content
    instrument_name = Path(file_path).stem
    
    # First 8 bytes might be a version identifier ("8VERSION")
    version_str = ""
    for i in range(1, 9):
        if i >= len(data) or data[i] == 0:
            break
        if 32 <= data[i] <= 126:  # Printable ASCII
            version_str += chr(data[i])
    
    # Find instrument ID byte offset
    # The original calculation was: params1_offset - 5 - 18
    # Where params1_offset was 0x18 + 13, so that's 0x18 + 13 - 5 - 18 = 0x0E
    inst_id_offset = 0x0E  # Base offset for instrument ID
    
    if inst_id_offset >= len(data):
        return None  # File is too small
    
    inst_id_byte = data[inst_id_offset]
    inst_id_hex = f"{inst_id_byte:02X}"
    
    # From instrument ID, calculate all other offsets
    algo_offset = inst_id_offset + 18  # 18 bytes after instrument ID
    if algo_offset >= len(data):
        return None  # File is too small
    
    algo_byte = data[algo_offset]
    algo_hex = f"{algo_byte:02X}"
    
    # Shapes are 4 bytes right after algo
    shapes_offset = algo_offset + 1
    if shapes_offset + 4 > len(data):
        return None  # File is too small
    
    shapes_bytes = data[shapes_offset:shapes_offset+4]
    shapes_hex = " ".join([f"{b:02X}" for b in shapes_bytes])
    
    # Params 1 are 8 bytes after shapes
    params1_offset = shapes_offset + 4
    if params1_offset + 8 > len(data):
        return None  # File is too small
    
    params1_bytes = data[params1_offset:params1_offset+8]
    # Format as integers with 2-figure formatting
    params1_hex = " ".join([f"{b:02d}" for b in params1_bytes])
    
    # Params 2 are 8 bytes after params1
    params2_offset = params1_offset + 8
    if params2_offset + 8 > len(data):
        return None  # File is too small
    
    params2_bytes = data[params2_offset:params2_offset+8]
    params2_hex = " ".join([f"{b:02X}" for b in params2_bytes])
    
    # Params 3 are 4 bytes after params2
    params3_offset = params2_offset + 8
    if params3_offset + 4 > len(data):
        return None  # File is too small
    
    params3_bytes = data[params3_offset:params3_offset+4]
    params3_hex = " ".join([f"{b:02X}" for b in params3_bytes])
    
    return {
        'type_id': instrument_type_id,
        'name': instrument_name,
        'version': version_str,
        'inst_id': inst_id_hex,
        'algo': algo_hex,
        'shapes': shapes_hex,
        'params1': params1_hex,
        'params2': params2_hex,
        'params3': params3_hex,
        'file_size': len(data),
        'inst_id_offset': inst_id_offset,
        'algo_offset': algo_offset,
        'shapes_offset': shapes_offset,
        'params1_offset': params1_offset
    }

def main():
    """Main function to inspect FMSYNTHS directory"""
    if len(sys.argv) < 2:
        print("Usage: python inspect_fmsynths.py <FMSYNTHS_directory> [--detailed]")
        return 1
    
    base_dir = Path(sys.argv[1])
    detailed = "--detailed" in sys.argv
    
    if not base_dir.exists():
        print(f"Error: Directory {base_dir} does not exist")
        return 1
    
    print("\nInspecting FMSYNTHS instruments\n")
    print(f"{'File Name':<20} {'ID':<4} {'Algo':<6} {'Shapes':<15} {'Params 1':<25} {'Params 2':<25} {'Params 3':<15}")
    print("-" * 110)
    
    # Find all m8i files in the directory
    m8i_files = list(base_dir.glob("**/*.m8i"))
    
    if not m8i_files:
        print(f"No .m8i files found in {base_dir}")
        return 0
    
    # Process each file
    filtered_files = []
    
    for m8i_file in sorted(m8i_files):
        info = read_instrument_file(m8i_file)
        if not info:
            print(f"Error reading {m8i_file.name}")
            continue
        
        # Only show instruments with ID 0x04
        if info['inst_id'] == "04":
            filtered_files.append((m8i_file, info))
            print(f"{m8i_file.name:<20} {info['inst_id']:<4} {info['algo']:<6} {info['shapes']:<15} {info['params1']:<25} {info['params2']:<25} {info['params3']:<15}")
    
    # Print detailed analysis if requested
    if detailed and filtered_files:
        print("\n" + "=" * 80)
        print("DETAILED ANALYSIS")
        print("=" * 80)
        
        for m8i_file, info in filtered_files:
            with open(m8i_file, 'rb') as f:
                data = f.read()
                
            print(f"\nFile: {m8i_file.name}")
            print(f"Instrument Name: {info['name']}")
            print(f"Type ID: 0x{info['type_id']:02X} ({info['type_id']})")
            print(f"Version: {info['version']}")
            print(f"Instrument ID: {info['inst_id']}")
            print(f"Algo: {info['algo']}")
            print(f"Shapes: {info['shapes']}")
            print(f"Params 1: {info['params1']}")
            print(f"Params 2: {info['params2']}")
            print(f"Params 3: {info['params3']}")
            
            # Show hexdump from before the instrument ID through all the parameters
            context_start = max(0, info['inst_id_offset'] - 4)  # Start 4 bytes before instrument ID
            context_length = (info['params1_offset'] - context_start) + 20  # Include params1, params2, and params3
            print(f"\nHex dump from instrument ID area (offset 0x{context_start:02X}):")
            print(hexdump(data, context_start, context_length))
            
            # Also show hexdump specifically of the instrument ID
            print(f"\nInstrument ID at offset 0x{info['inst_id_offset']:02X}:")
            inst_id_context_start = max(0, info['inst_id_offset'] - 2)
            print(hexdump(data, inst_id_context_start, 6))
            print("")
    
    # Print summary
    print(f"\nTotal instruments: {len(m8i_files)}")
    print(f"Instruments with ID 0x04: {len(filtered_files)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())