#!/usr/bin/env python3
import argparse
import os
import sys
import yaml

def load_format_config():
    """Load the format_config.yaml file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(os.path.dirname(script_dir), 'm8', 'format_config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

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
    """Read a fixed-length string from binary data."""
    # Extract the bytes for the string
    string_bytes = data[offset:offset+length]
    # Convert to string and strip any null bytes
    result = ''
    for b in string_bytes:
        if b == 0:
            break
        result += chr(b)
    return result

def main():
    parser = argparse.ArgumentParser(description="Raw inspect a single M8 instrument file (.m8i)")
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
        # Load configuration
        config = load_format_config()
        
        # Get version and metadata offsets from config
        version_offset = config["version"]["offset"]
        metadata_offset = config["metadata"]["offset"]
        instrument_block_size = config["instruments"]["block_size"]
        
        # Read the file
        with open(args.file_path, 'rb') as f:
            data = f.read()
        
        # Extract instrument data from the file
        instrument_data = data[metadata_offset:metadata_offset + instrument_block_size]
        
        # Get instrument type and name
        type_offset = config["instruments"]["common_fields"]["type"]["offset"]
        name_offset = config["instruments"]["common_fields"]["name"]["offset"]
        name_size = config["instruments"]["common_fields"]["name"]["size"]
        
        instrument_type = instrument_data[type_offset]
        instrument_name = read_fixed_string(instrument_data, name_offset, name_size)
        
        # Print basic info and hex dump
        print(f"Instrument: {instrument_name} (Type: {instrument_type})")
        print(f"Raw binary data ({len(instrument_data)} bytes):")
        print(hex_dump(instrument_data))
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())