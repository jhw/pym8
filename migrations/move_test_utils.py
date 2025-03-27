#!/usr/bin/env python
"""
Migration script to move tests/api/utils to tests/core/utils to mirror the m8/core/utils structure.
"""

import os
import re
import shutil
import sys
from pathlib import Path

def main():
    """Main function to execute the migration."""
    # Get the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Define the source and destination directories
    source_dir = project_root / "tests" / "api" / "utils"
    dest_dir = project_root / "tests" / "core" / "utils"
    
    # Create destination directory if it doesn't exist
    os.makedirs(dest_dir, exist_ok=True)
    
    # Verify source directory exists
    if not source_dir.exists():
        print(f"Error: Source directory '{source_dir}' does not exist.")
        return 1
    
    # Create __init__.py in destination if it doesn't exist
    init_path = dest_dir / "__init__.py"
    if not init_path.exists():
        with open(init_path, "w") as f:
            f.write('"""Test utilities for the M8 core modules."""\n')
    
    # List of files to exclude from migration (already migrated, or special cases)
    exclude_files = [
        # If there are any files to exclude, list them here
        # e.g., "already_migrated.py",
    ]
    
    # File counter
    moved_files = 0
    
    # Move all Python files from source to destination
    for file_path in source_dir.glob("*.py"):
        if file_path.name == "__init__.py" or file_path.name in exclude_files:
            continue
            
        dest_file = dest_dir / file_path.name
        
        # Copy the file
        print(f"Moving {file_path} to {dest_file}")
        shutil.copy2(file_path, dest_file)
        moved_files += 1
    
    # Update import references in all test files
    updated_files = 0
    pattern = r'from tests\.api\.utils'
    replacement = r'from tests.core.utils'
    
    for py_file in project_root.glob("tests/**/*.py"):
        with open(py_file, "r") as f:
            content = f.read()
        
        # Replace import statements
        updated_content = re.sub(pattern, replacement, content)
        
        # If content was changed, write it back
        if updated_content != content:
            with open(py_file, "w") as f:
                f.write(updated_content)
            print(f"Updated imports in {py_file}")
            updated_files += 1
    
    # If all files were moved successfully, we can now delete the source files
    for file_path in source_dir.glob("*.py"):
        if file_path.name == "__init__.py" or file_path.name in exclude_files:
            continue
        
        print(f"Deleting original file {file_path}")
        file_path.unlink()
    
    # Keep the __init__.py in source with a redirect notice
    init_source = source_dir / "__init__.py"
    with open(init_source, "w") as f:
        f.write('"""Redirected to tests.core.utils - use that package instead."""\n\n')
        f.write('# For backward compatibility\n')
        f.write('from tests.core.utils import *\n')
    
    print(f"\nMigration completed: {moved_files} files moved, {updated_files} files updated.")
    print("\nTo complete the migration:")
    print("1. Run the test suite to verify everything works")
    print("2. Remove the tests/api/utils directory if all tests pass")
    print("   (You can run: rm -rf tests/api/utils)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())