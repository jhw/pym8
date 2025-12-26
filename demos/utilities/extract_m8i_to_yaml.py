#!/usr/bin/env python3
"""Extract M8i instrument files to YAML parameter files.

This utility reads .m8i instrument files from a directory and exports their
parameters to YAML files using the to_dict() method. Optionally filters by
instrument type.

Usage:
    python extract_m8i_to_yaml.py [--type TYPE_ID]

Options:
    --type TYPE_ID    Only process instruments of this type (e.g., 4 for FM Synth)

The script expects:
    Input: tmp/dw01-synthdrums/m8i/*.m8i
    Output: tmp/dw01-synthdrums/yaml/*.yaml
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from m8.api.instrument import M8Instrument
import yaml


def extract_instrument_to_yaml(m8i_path, output_dir, instrument_type_filter=None):
    """Extract a single M8i file to YAML.

    Args:
        m8i_path: Path to .m8i file
        output_dir: Directory to write YAML files
        instrument_type_filter: If set, only process instruments of this type

    Returns:
        True if processed, False if skipped
    """
    try:
        # Read the instrument
        instrument = M8Instrument.read_from_file(m8i_path)

        # Check type filter
        if instrument_type_filter is not None:
            instrument_type = instrument._data[0]  # Type at offset 0
            if instrument_type != instrument_type_filter:
                return False

        # Get instrument parameters as dict with enum names
        params = instrument.to_dict(enum_mode='name')

        # Create output filename (replace .m8i with .yaml)
        input_filename = os.path.basename(m8i_path)
        output_filename = input_filename.replace('.m8i', '.yaml')
        output_path = os.path.join(output_dir, output_filename)

        # Write YAML file
        os.makedirs(output_dir, exist_ok=True)
        with open(output_path, 'w') as f:
            yaml.dump(params, f, default_flow_style=False, sort_keys=False)

        print(f"Extracted: {input_filename} -> {output_filename}")
        return True

    except Exception as e:
        print(f"Error processing {m8i_path}: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Extract M8i instrument files to YAML parameter files'
    )
    parser.add_argument(
        '--type',
        type=int,
        default=None,
        help='Only process instruments of this type (e.g., 4 for FM Synth)'
    )
    parser.add_argument(
        '--input-dir',
        default='tmp/dw01-synthdrums/m8i',
        help='Input directory containing .m8i files'
    )
    parser.add_argument(
        '--output-dir',
        default='tmp/dw01-synthdrums/yaml',
        help='Output directory for YAML files'
    )

    args = parser.parse_args()

    # Resolve paths relative to repo root
    repo_root = Path(__file__).parent.parent.parent
    input_dir = repo_root / args.input_dir
    output_dir = repo_root / args.output_dir

    # Check input directory exists
    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        return 1

    # Find all .m8i files
    m8i_files = sorted(input_dir.glob('*.m8i'))

    if not m8i_files:
        print(f"No .m8i files found in {input_dir}")
        return 1

    print(f"Found {len(m8i_files)} .m8i files in {input_dir}")
    if args.type is not None:
        print(f"Filtering for instrument type: {args.type}")
    print()

    # Process each file
    processed_count = 0
    skipped_count = 0

    for m8i_path in m8i_files:
        if extract_instrument_to_yaml(str(m8i_path), str(output_dir), args.type):
            processed_count += 1
        else:
            skipped_count += 1

    print()
    print(f"Processed: {processed_count} files")
    if skipped_count > 0:
        print(f"Skipped: {skipped_count} files (type filter)")
    print(f"Output directory: {output_dir}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
