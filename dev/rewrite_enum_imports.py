#!/usr/bin/env python3
"""
Script to rewrite import paths from m8.api.utils.enums to m8.core.enums
"""

import os
import re
import sys
from pathlib import Path

def rewrite_imports_in_file(file_path):
    """Replace m8.api.utils.enums with m8.core.enums in a file."""
    # Read the file content
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Patterns to replace
    patterns = [
        (r'from m8\.api\.utils\.enums import', r'from m8.core.enums import'),
        (r'from m8\.api\.utils import enums', r'from m8.core import enums'),
        (r'import m8\.api\.utils\.enums', r'import m8.core.enums'),
        (r'm8\.api\.utils\.enums', r'm8.core.enums')  # For other references
    ]
    
    original_content = content
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # Only write back if changes were made
    if content != original_content:
        print(f"Updating imports in {file_path}")
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

def process_directory(directory):
    """Process all Python files in a directory recursively."""
    changed_files = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if rewrite_imports_in_file(file_path):
                    changed_files += 1
    
    return changed_files

def main():
    # Define directories to process
    m8_dir = Path('/Users/jhw/work/pym8/m8')
    tests_dir = Path('/Users/jhw/work/pym8/tests')
    
    if not m8_dir.exists() or not tests_dir.exists():
        print("Error: Required directories not found.")
        return 1
    
    # Process both directories
    print("Processing m8 directory...")
    m8_changes = process_directory(m8_dir)
    print(f"Updated {m8_changes} files in m8 directory.")
    
    print("\nProcessing tests directory...")
    tests_changes = process_directory(tests_dir)
    print(f"Updated {tests_changes} files in tests directory.")
    
    print(f"\nTotal: Updated {m8_changes + tests_changes} files.")
    return 0

if __name__ == "__main__":
    sys.exit(main())