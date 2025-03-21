#!/usr/bin/env python3
import argparse
import os
import sys
import yaml

from m8.api.project import M8Project
from m8.api.instruments import M8Instrument
from m8.api import M8Block

def hex_dump(data, width=16):
    """Prints data in a readable hex dump format."""
    result = []
    for i in range(0, len(data), width):
        chunk = data[i:i+width]
        hex_values = ' '.join(f"{b:02X}" for b in chunk)
        ascii_values = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        result.append(f"{i:08X}  {hex_values:<{width * 3}} |{ascii_values}|")
    return "\n".join(result)

def main():
    parser = argparse.ArgumentParser(description="Inspect an instrument in an M8 project file")
    parser.add_argument("file_path", help="Path to the M8 project file (.m8s)")
    parser.add_argument("--index", "-i", type=int, default=0, help="Instrument index (0-63, default: 0)")
    parser.add_argument("--format", "-f", choices=["yaml", "bytes"], default="yaml", 
                        help="Output format (yaml or bytes, default: yaml)")
    
    args = parser.parse_args()
    
    # Check if file exists
    if not os.path.exists(args.file_path):
        print(f"Error: File {args.file_path} does not exist", file=sys.stderr)
        return 1
    
    # Check file extension
    if not args.file_path.lower().endswith(".m8s"):
        print(f"Warning: File {args.file_path} does not have .m8s extension", file=sys.stderr)
    
    try:
        # Load project
        project = M8Project.read_from_file(args.file_path)
        
        # Check instrument index
        if args.index < 0 or args.index >= len(project.instruments):
            print(f"Error: Instrument index {args.index} out of range (0-{len(project.instruments)-1})", 
                  file=sys.stderr)
            return 1
        
        # Get the instrument
        instrument = project.instruments[args.index]
        
        # Check if it's an empty slot
        if isinstance(instrument, M8Block):
            print(f"Instrument at index {args.index} is empty", file=sys.stderr)
            return 1
        
        # Output based on format
        if args.format == "yaml":
            # Convert to dict and output as YAML
            instrument_dict = instrument.as_dict()
            print(yaml.dump(instrument_dict, sort_keys=False, default_flow_style=False))
        else:  # bytes format
            # Get raw binary data
            raw_data = instrument.write()
            print(f"Instrument: {instrument.name} (Type: {instrument.type}, Index: {args.index})")
            print(f"Raw binary data ({len(raw_data)} bytes):")
            print(hex_dump(raw_data))
            
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())