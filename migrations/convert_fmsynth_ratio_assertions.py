#!/usr/bin/env python3
"""
Migration script to convert FMSynth ratio/ratio_fine assertion values from hex to decimal.

This script scans test files for assertions checking ratio/ratio_fine values in serialized output
and converts the expected values from hexadecimal to decimal representation.
"""

import os
import re
import sys
from pathlib import Path

# Directory containing the test files
TEST_DIRS = [
    "tests/api/instruments",
    "tests/examples"
]

# Patterns to match assertions about ratio/ratio_fine values with hex literals
RATIO_PATTERNS = [
    # Match direct parameter assertions like self.assertEqual(params.ratio1, 0x08)
    r'(self\.assertEqual\(.*?\.ratio(?:_fine)?\d+\s*,\s*)(0x[0-9a-fA-F]+)(\s*\))',
    
    # Match dictionary assertions like self.assertEqual(result["ratio1"], 0x08)
    r'(self\.assertEqual\(.*?\[[\"\']ratio(?:_fine)?\d+[\"\']\]\s*,\s*)(0x[0-9a-fA-F]+)(\s*\))',
    
    # Match operators assertions like self.assertEqual(result["operators"][0]["ratio"], 0x08)
    r'(self\.assertEqual\(.*?operators.*?\[[\'\"]ratio(?:_fine)?[\'\"]\]\s*,\s*)(0x[0-9a-fA-F]+)(\s*\))',
    
    # Match binary content assertions like self.assertEqual(binary[23], 0x08)  # ratio1
    r'(self\.assertEqual\(.*?binary\[\d+\]\s*,\s*)(0x[0-9a-fA-F]+)(\s*\).*?ratio)'
]

def convert_hex_to_decimal(match):
    """Convert hex literal to decimal in the matched assertion."""
    prefix, hex_value, suffix = match.groups()
    # Convert hex to decimal
    decimal_value = int(hex_value, 16)
    # Return the updated assertion
    return f"{prefix}{decimal_value}{suffix}"

def process_file(file_path):
    """Process a single file, converting ratio assertions from hex to decimal."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Apply each pattern in turn
    replaced_content = content
    found_match = False
    
    for pattern in RATIO_PATTERNS:
        # Apply the current pattern
        new_content = re.sub(pattern, convert_hex_to_decimal, replaced_content)
        if new_content != replaced_content:
            found_match = True
            replaced_content = new_content
    
    # Only write back if changes were made
    if found_match:
        print(f"Converting ratio assertions in {file_path}")
        with open(file_path, 'w') as f:
            f.write(replaced_content)
        return True
    return False

def preview_changes(file_path):
    """Preview the changes that would be made to a file without writing them."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Apply each pattern in turn and collect changes
    replacements = []
    replaced_content = content
    
    for pattern in RATIO_PATTERNS:
        # For each match, store the old and new content
        for match in re.finditer(pattern, replaced_content):
            old_text = match.group(0)
            new_text = convert_hex_to_decimal(match)
            replacements.append((old_text, new_text))
        
        # Apply the pattern
        replaced_content = re.sub(pattern, convert_hex_to_decimal, replaced_content)
    
    return replacements

def main():
    """Main function to run the migration."""
    # Check for command line arguments
    preview_mode = "--preview" in sys.argv
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Track statistics
    total_files = 0
    modified_files = 0
    preview_changes_found = False
    
    # Process all Python files in test directories
    for test_dir in TEST_DIRS:
        test_path = project_root / test_dir
        for root, _, files in os.walk(test_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    total_files += 1
                    
                    if preview_mode:
                        # Just preview changes without writing
                        changes = preview_changes(file_path)
                        if changes:
                            preview_changes_found = True
                            print(f"\nIn {file_path}:")
                            for old, new in changes:
                                print(f"  - {old.strip()} -> {new.strip()}")
                    else:
                        # Apply changes
                        if process_file(file_path):
                            modified_files += 1
    
    if preview_mode:
        if preview_changes_found:
            print("\nPreview complete. Run without --preview to apply changes.")
        else:
            print("\nNo changes to preview.")
    else:
        print(f"\nMigration complete: {modified_files} files modified out of {total_files} files scanned.")
        
        if modified_files > 0:
            print("\nSuggested next steps:")
            print("1. Run tests to verify the changes work correctly")
            print("2. Review the changes with 'git diff'")
            print("3. If everything looks good, commit the changes")

if __name__ == "__main__":
    main()