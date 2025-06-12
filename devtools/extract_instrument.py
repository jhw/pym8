#!/usr/bin/env python
"""
Utility to extract the first instrument from an M8 song file (.m8s)
and export it as an instrument file (.m8i).
"""

import os
import sys
import argparse
from pathlib import Path

from m8.api.project import M8Project
from m8.api.instruments import M8Instrument


def extract_first_instrument(input_path, output_dir="tmp"):
    """
    Extract the first instrument from an M8 song file and save it as an M8 instrument file.
    
    Args:
        input_path: Path to the .m8s file
        output_dir: Directory to save the exported .m8i file (defaults to 'tmp/')
        
    Returns:
        Path to the exported .m8i file
    """
    # Check if the input file exists
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} does not exist.")
        sys.exit(1)
    
    # Validate the file has .m8s extension
    if not input_path.lower().endswith(".m8s"):
        print(f"Error: Input file {input_path} must have .m8s extension.")
        sys.exit(1)
    
    # Load the project
    try:
        project = M8Project.read_from_file(input_path)
    except Exception as e:
        print(f"Error loading M8 project file: {e}")
        sys.exit(1)
    
    # Check if the project has at least one instrument
    if len(project.instruments) == 0:
        print("Error: Project does not contain any instruments.")
        sys.exit(1)
    
    # Find instruments with valid types (non-0xFF)
    # In M8 files, empty instruments have type 0xFF
    valid_instruments = []
    for i, instrument in enumerate(project.instruments):
        # Check if it's an M8Block (which would be empty) or if type is 0xFF
        if hasattr(instrument, 'type'):
            type_value = instrument.type.value if hasattr(instrument.type, 'value') else instrument.type
            if isinstance(type_value, int) and type_value != 0xFF:
                valid_instruments.append(i)
    
    if len(valid_instruments) == 0:
        print("Error: Project does not contain any valid instruments (all types are 0xFF).")
        sys.exit(1)
    
    if len(valid_instruments) > 1:
        print(f"Error: Project contains multiple valid instruments at indices: {valid_instruments}")
        print("This tool only supports projects with a single valid instrument at index 0.")
        sys.exit(1)
    
    # Check if the only valid instrument is at index 0
    if valid_instruments[0] != 0:
        print(f"Error: The valid instrument is at index {valid_instruments[0]}, not at index 0.")
        print("This tool only supports projects with a single valid instrument at index 0.")
        sys.exit(1)
    
    # Get the instrument
    instrument = project.instruments[0]
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output file path with same stub as input file
    input_filename = os.path.basename(input_path)
    input_stub = os.path.splitext(input_filename)[0]
    output_path = os.path.join(output_dir, f"{input_stub}.m8i")
    
    # Export the instrument
    try:
        instrument.write_to_file(output_path)
        print(f"Successfully exported instrument to {output_path}")
        return output_path
    except Exception as e:
        print(f"Error exporting instrument: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Extract the first instrument from an M8 song file (.m8s) "
                    "and export it as an instrument file (.m8i)."
    )
    parser.add_argument("input_file", help="Path to the .m8s file")
    parser.add_argument(
        "-o", "--output-dir", 
        default="tmp",
        help="Directory to save the exported .m8i file (defaults to 'tmp/')"
    )
    
    args = parser.parse_args()
    extract_first_instrument(args.input_file, args.output_dir)


if __name__ == "__main__":
    main()