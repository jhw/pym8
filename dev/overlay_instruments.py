#!/usr/bin/env python

import os
import sys
import json
from m8.api.project import M8Project

def compare_bytes(data1, data2, offset=0, length=None):
    """Compare two byte arrays starting at offset, up to length or min length."""
    if length is None:
        length = min(len(data1), len(data2) - offset)
    else:
        length = min(length, len(data1), len(data2) - offset)
    
    if length <= 0:
        return 0, 0
    
    matches = 0
    for i in range(length):
        if i < len(data1) and offset + i < len(data2):
            if data1[i] == data2[offset + i]:
                matches += 1
    
    return matches, length

def find_best_offset(source_data, target_data):
    """Find the best offset to overlay source_data onto target_data."""
    best_offset = 0
    best_match_percent = 0
    
    for offset in range(len(target_data) - 1):
        matches, total = compare_bytes(source_data, target_data, offset)
        if total > 0:
            match_percent = (matches / total) * 100
            print(offset, match_percent)
            if match_percent > best_match_percent:
                best_match_percent = match_percent
                best_offset = offset
    
    return best_offset, best_match_percent

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <path_to_m8s_file> <path_to_m8i_file>")
        sys.exit(1)
    
    m8s_path = sys.argv[1]
    m8i_path = sys.argv[2]
    
    if not os.path.exists(m8s_path):
        print(f"Error: File not found: {m8s_path}")
        sys.exit(1)
    
    if not os.path.exists(m8i_path):
        print(f"Error: File not found: {m8i_path}")
        sys.exit(1)
    
    # Load the M8S file and get the first instrument data
    project = M8Project.read_from_file(m8s_path)
    
    if not project.instruments or len(project.instruments) == 0:
        print("No instruments found in the project")
        sys.exit(1)
    
    # Get raw instrument data from the first instrument
    m8s_instr_data = project.instruments[0].write()
    
    # Read the M8I file directly
    with open(m8i_path, "rb") as f:
        m8i_data = f.read()
    
    # Find the best offset
    best_offset, match_percent = find_best_offset(m8s_instr_data, m8i_data)
    
    print(f"Best offset: {best_offset} (0x{best_offset:X})")
    print(f"Match percentage: {match_percent:.2f}%")

if __name__ == "__main__":
    main()
