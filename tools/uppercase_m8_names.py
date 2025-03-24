#!/usr/bin/env python3
"""
Tool to recursively find and convert lowercase M8 instrument and modulator names to uppercase.
Only converts strings within quotes (single or double) and only for known M8 types.
"""

import os
import re
import sys
from pathlib import Path

# Instrument types from format_config.yaml
INSTRUMENT_TYPES = [
    "WAVSYNTH",
    "MACROSYNTH",
    "SAMPLER"
]

# Modulator types from format_config.yaml
MODULATOR_TYPES = [
    "AHD_ENVELOPE",
    "ADSR_ENVELOPE",
    "DRUM_ENVELOPE",
    "LFO", 
    "TRIGGER_ENVELOPE",
    "TRACKING_ENVELOPE"
]

# All names to look for
ALL_M8_NAMES = INSTRUMENT_TYPES + MODULATOR_TYPES

def create_pattern():
    """Create regex pattern to match quoted lowercase M8 names."""
    # Create alternation of all names
    names_pattern = "|".join([name.lower() for name in ALL_M8_NAMES])
    
    # Match either single or double quoted strings containing these names
    pattern = fr'(["\'])({names_pattern})(["\'])'
    
    return re.compile(pattern)

def process_file(file_path, pattern, dry_run=True):
    """Process a single file, converting lowercase M8 names to uppercase."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check if the file contains any of our targets
        if not any(name.lower() in content for name in ALL_M8_NAMES):
            return False, 0
            
        # Function to replace matches with uppercase version
        def replace_match(match):
            open_quote = match.group(1)
            m8_name = match.group(2).upper()
            close_quote = match.group(3)
            return f"{open_quote}{m8_name}{close_quote}"
            
        # Apply the replacement
        new_content, count = re.subn(pattern, replace_match, content)
        
        if count > 0 and not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
        return count > 0, count
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, 0

def process_directory(directory, pattern, dry_run=True):
    """Recursively process all Python files in a directory."""
    changes = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                changed, count = process_file(file_path, pattern, dry_run)
                
                if changed:
                    changes.append((file_path, count))
                    
    return changes

def main():
    """Main function to run the script."""
    if len(sys.argv) < 2:
        print("Usage: python uppercase_m8_names.py [--dry-run] directory1 [directory2 ...]")
        sys.exit(1)
        
    args = sys.argv[1:]
    dry_run = False
    
    if args[0] == '--dry-run':
        dry_run = True
        args = args[1:]
        
    if not args:
        print("Please specify at least one directory to process.")
        sys.exit(1)
        
    pattern = create_pattern()
    changes_by_dir = {}
    
    # Process each directory
    for directory in args:
        if not os.path.isdir(directory):
            print(f"Warning: {directory} is not a valid directory. Skipping.")
            continue
            
        changes = process_directory(directory, pattern, dry_run)
        changes_by_dir[directory] = changes
        
    # Print summary
    total_files = 0
    total_changes = 0
    
    print("\nSummary of changes:")
    print("==================\n")
    
    for directory, changes in changes_by_dir.items():
        if changes:
            print(f"Directory: {directory}")
            for file_path, count in changes:
                rel_path = os.path.relpath(file_path, directory)
                print(f"  {rel_path}: {count} replacements")
                total_files += 1
                total_changes += count
                
    print(f"\nTotal: {total_files} files modified, {total_changes} replacements")
    
    if dry_run:
        print("\nThis was a dry run. No changes were made.")
        print("Run without --dry-run to apply changes.")

if __name__ == "__main__":
    main()