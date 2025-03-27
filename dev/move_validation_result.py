#!/usr/bin/env python3
"""
Script to move M8ValidationResult from m8/api/__init__.py to m8/core/validation.py
and update all import references in the codebase.
"""
import os
import re
import sys

# The directories to search
DIRS = ['m8', 'tests']

def extract_validation_result_code():
    """Extract the M8ValidationResult class definition from m8/api/__init__.py."""
    with open('m8/api/__init__.py', 'r') as f:
        content = f.read()
    
    # Regular expression to match the class definition
    pattern = r'class M8ValidationResult:.*?def log_errors.*?logger\.error\(error\)\n'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        return match.group(0)
    else:
        raise ValueError("Could not find M8ValidationResult class in m8/api/__init__.py")

def remove_validation_result_from_api_init(validation_code):
    """Remove the M8ValidationResult class from m8/api/__init__.py."""
    with open('m8/api/__init__.py', 'r') as f:
        content = f.read()
    
    # Replace the validation code with an empty string
    new_content = content.replace(validation_code, '')
    
    # Add import for M8ValidationResult from core.validation
    import_section_end = content.find('# exceptions')
    if import_section_end > 0:
        insert_point = content.find(')', import_section_end) + 1
        import_statement = '\nfrom m8.core.validation import M8ValidationResult'
        
        # Insert the import statement after the last import
        new_content = new_content[:insert_point] + import_statement + new_content[insert_point:]
    
    with open('m8/api/__init__.py', 'w') as f:
        f.write(new_content)

def create_core_validation_module(validation_code):
    """Create the m8/core/validation.py module with the M8ValidationResult class."""
    # Create the module content
    content = f"""\"\"\"
Validation utilities for the M8 library.

This module provides tools for validating M8 data structures and tracking validation errors.
\"\"\"

import logging

{validation_code}
"""
    
    # Write the module
    with open('m8/core/validation.py', 'w') as f:
        f.write(content)

def update_import_references():
    """Update all import references from m8.api import M8ValidationResult to m8.core.validation import M8ValidationResult."""
    files_updated = 0
    
    for dir_name in DIRS:
        for root, _, files in os.walk(dir_name):
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    file_path = os.path.join(root, file)
                    
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Replace different import patterns
                    updated_content = content
                    
                    # Pattern 1: from m8.api import ..., M8ValidationResult, ...
                    updated_content = re.sub(
                        r'from m8\.api import (.*?)M8ValidationResult(.*?)',
                        r'from m8.api import \1\2',
                        updated_content
                    )
                    
                    # Add the new import if needed
                    if "M8ValidationResult" in updated_content and "from m8.core.validation import M8ValidationResult" not in updated_content:
                        # Find the import section
                        import_section = re.search(r'(from .*? import .*?\n)+', updated_content)
                        if import_section:
                            import_end = import_section.end()
                            updated_content = updated_content[:import_end] + "from m8.core.validation import M8ValidationResult\n" + updated_content[import_end:]
                    
                    # Check if content was actually changed
                    if updated_content != content:
                        with open(file_path, 'w') as f:
                            f.write(updated_content)
                        files_updated += 1
                        print(f"Updated {file_path}")
    
    return files_updated

def main():
    """Main function to execute the script."""
    print("Moving M8ValidationResult from m8/api/__init__.py to m8/core/validation.py...")
    
    try:
        # Extract the validation code
        validation_code = extract_validation_result_code()
        print("Successfully extracted M8ValidationResult class definition")
        
        # Create the core/validation.py module
        create_core_validation_module(validation_code)
        print("Created m8/core/validation.py")
        
        # Remove the validation code from api/__init__.py
        remove_validation_result_from_api_init(validation_code)
        print("Removed M8ValidationResult from m8/api/__init__.py")
        
        # Update import references in all files
        files_updated = update_import_references()
        print(f"Updated import references in {files_updated} files")
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())