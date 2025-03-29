#!/usr/bin/env python3
import argparse
import os
import sys

from m8.api.version import M8Version
from m8.config import get_offset


def main():
    parser = argparse.ArgumentParser(description="Extract and display version from an M8 project file")
    parser.add_argument("file_path", help="Path to the M8 project file (.m8s)")
    
    args = parser.parse_args()
    
    # Check if file exists
    if not os.path.exists(args.file_path):
        raise FileNotFoundError(f"File {args.file_path} does not exist")
    
    # Check file extension
    if not args.file_path.lower().endswith(".m8s"):
        raise ValueError(f"File {args.file_path} does not have .m8s extension")
    
    # Get version offset from config
    version_offset = get_offset("version")
    
    # Read just enough bytes for the version
    with open(args.file_path, "rb") as f:
        # M8Version.write() returns 4 bytes
        version_data = f.read(version_offset + 4)
        
        if len(version_data) < version_offset + 1:
            raise ValueError(f"File is too small to contain version information")
            
        # Extract version information (offset + 4 bytes)
        version = M8Version.read(version_data[version_offset:])
        
        # Display version information
        print(f"M8 Version: {version}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)