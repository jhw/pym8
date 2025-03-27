#!/usr/bin/env python3
import argparse
import os
import sys
from m8.config import get_offset

def hex_dump(data, width=16):
    """Prints data in a readable hex dump format."""
    result = []
    for i in range(0, len(data), width):
        chunk = data[i:i+width]
        hex_values = ' '.join(f"{b:02X}" for b in chunk)
        ascii_values = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        result.append(f"{i:08X}  {hex_values:<{width * 3}} |{ascii_values}|")
    return "\n".join(result)

def read_fixed_string(data, offset, length):
    """Read a fixed-length string from binary data and trim trailing nulls."""
    string_bytes = data[offset:offset + length]
    # Trim null bytes
    null_pos = string_bytes.find(0)
    if null_pos != -1:
        string_bytes = string_bytes[:null_pos]
    return string_bytes.decode('utf-8', errors='replace')

def display_instrument_info(data):
    """Display basic instrument info without using the M8Instrument class."""
    # Instrument type is at offset 0
    type_id = data[0]
    
    # Name is at offset 1, length 12 bytes
    name = read_fixed_string(data, 1, 12)
    
    print(f"Instrument Type ID: 0x{type_id:02X} ({type_id})")
    print(f"Instrument Name: {name}")
    print(f"Raw binary data ({len(data)} bytes):")
    print(hex_dump(data))

def main():
    parser = argparse.ArgumentParser(description="Dump a single M8 instrument file (.m8i)")
    parser.add_argument("file_path", help="Path to the M8 instrument file (.m8i)")
    
    args = parser.parse_args()
    
    # Check if file exists
    if not os.path.exists(args.file_path):
        print(f"Error: File {args.file_path} does not exist", file=sys.stderr)
        return 1
    
    # Check file extension
    if not args.file_path.lower().endswith(".m8i"):
        print(f"Error: File {args.file_path} does not have .m8i extension", file=sys.stderr)
        return 1
    
    try:
        # Read the entire file
        with open(args.file_path, "rb") as f:
            file_data = f.read()
            
        # Get the metadata offset (where the instrument data starts)
        metadata_offset = get_offset("metadata")
        
        # Extract instrument data starting from metadata offset
        instrument_data = file_data[metadata_offset:]
        
        # Display the instrument info
        display_instrument_info(instrument_data)
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())