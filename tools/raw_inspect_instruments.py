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

def is_empty_instrument(data):
    """Check if an instrument block is empty (all zeros, type 255, or no valid type)."""
    # Check if the first few bytes are all zeros
    if all(b == 0 for b in data[:10]):
        return True
    
    # Check if the instrument type is 255 (0xFF) - empty/unused
    if data[0] == 0xFF:
        return True
        
    return False

def main():
    parser = argparse.ArgumentParser(description="Raw inspect instruments in an M8 project file")
    parser.add_argument("file_path", help="Path to the M8 project file (.m8s)")
    
    args = parser.parse_args()
    
    # Check if file exists
    if not os.path.exists(args.file_path):
        print(f"Error: File {args.file_path} does not exist", file=sys.stderr)
        return 1
    
    # Check file extension
    if not args.file_path.lower().endswith(".m8s"):
        print(f"Error: File {args.file_path} does not have .m8s extension", file=sys.stderr)
        return 1
    
    try:
        # Load configuration
        config = load_format_config()
        
        # Get instruments offset and block size from config
        instruments_offset = config["instruments"]["offset"]
        instrument_block_size = config["instruments"]["block_size"]
        instrument_count = config["instruments"]["count"]
        
        # Read the file
        with open(args.file_path, 'rb') as f:
            data = f.read()
        
        # Identify and process non-empty instruments
        non_empty_instruments = []
        
        for idx in range(instrument_count):
            start_offset = instruments_offset + (idx * instrument_block_size)
            end_offset = start_offset + instrument_block_size
            
            # Ensure we don't read past the end of the file
            if end_offset > len(data):
                break
                
            instrument_data = data[start_offset:end_offset]
            
            # Skip empty instruments
            if is_empty_instrument(instrument_data):
                continue
            
            # Get instrument type and name
            type_offset = config["instruments"]["common_fields"]["type"]["offset"]
            name_offset = config["instruments"]["common_fields"]["name"]["offset"]
            name_size = config["instruments"]["common_fields"]["name"]["size"]
            
            instrument_type = instrument_data[type_offset]
            instrument_name = read_fixed_string(instrument_data, name_offset, name_size)
            
            non_empty_instruments.append((idx, instrument_type, instrument_name, instrument_data))
        
        # Display information about found instruments
        print(f"Found {len(non_empty_instruments)} non-empty instruments")
        
        # Iterate through non-empty instruments
        for idx, instrument_type, instrument_name, instrument_data in non_empty_instruments:
            print(f"\nInstrument {idx}: {instrument_name} (Type: {instrument_type})")
            
            # Prompt user
            while True:
                response = input("Dump instrument details? (y/n/q): ").lower()
                if response == 'y':
                    print("\n" + "="*50)
                    print(f"Raw binary data ({len(instrument_data)} bytes):")
                    print(hex_dump(instrument_data))
                    print("="*50)
                    break
                elif response == 'n':
                    break
                elif response == 'q':
                    print("Exiting...")
                    return 0
                else:
                    print("Invalid option. Please enter 'y', 'n', or 'q'")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())