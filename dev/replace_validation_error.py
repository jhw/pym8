#!/usr/bin/env python3
"""
Replaces references to M8ValidationError with M8ValidationResult in all Python files.
Also updates test assertions with self.assertRaises(M8ValidationError) to use result validation.
"""
import os
import re
import sys

# The directories to search
DIRS = ['m8', 'tests']

def process_file(file_path):
    """Process a single Python file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace import statements
    new_content = re.sub(
        r'from m8\.api import (.*?)M8ValidationError(.*?)',
        r'from m8.api import \1M8ValidationResult\2',
        content
    )
    
    # Replace class references (not in import statements)
    new_content = re.sub(
        r'(?<!from\s)(?<!import\s)M8ValidationError',
        r'ValueError',
        new_content
    )
    
    # Replace validation methods that raised exceptions
    pattern = r'(\s+)def validate_[^(]+\([^)]*\):\s+([^r]+?)raise M8ValidationError\(\s*f?"([^"]+)"'
    replacement = r'\1def validate_\2result = M8ValidationResult(context="validation")\n\1result.add_error(f"\3")\n\1return result'
    new_content = re.sub(pattern, replacement, new_content, flags=re.DOTALL)
    
    # Save if changed
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        return True
    return False

def main():
    """Main function to scan directories and process files."""
    count = 0
    for dir_name in DIRS:
        for root, _, files in os.walk(dir_name):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    if process_file(file_path):
                        count += 1
                        print(f"Updated {file_path}")
    
    print(f"Updated {count} files total")

if __name__ == '__main__':
    main()