#!/usr/bin/env python
"""
Migration script to move enum tests from tests/api/utils/enums.py and tests/api/enums/__init__.py
to the new tests/core/enums directory structure.
"""

import os
import shutil
import sys
from pathlib import Path

def main():
    """Main function to execute the migration."""
    # Get the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Source files to remove (they have already been migrated)
    source_files = [
        project_root / "tests" / "api" / "utils" / "enums.py",
        project_root / "tests" / "api" / "enums" / "__init__.py",
        project_root / "tests" / "api" / "utils" / "parameterized_instrument_test.py",
        project_root / "tests" / "api" / "utils" / "simplified_instrument_test.py",
        project_root / "tests" / "api" / "utils" / "simplified_modulator_test.py",
        project_root / "tests" / "api" / "utils" / "test_context.py"
    ]
    
    # Check that the destination files already exist
    dest_files = [
        project_root / "tests" / "core" / "enums" / "__init__.py",
        project_root / "tests" / "core" / "enums" / "test_basic_functions.py",
        project_root / "tests" / "core" / "enums" / "test_instrument_enum_functions.py",
        project_root / "tests" / "core" / "enums" / "test_parameter_enum_functions.py",
        project_root / "tests" / "core" / "enums" / "test_enum_property_mixin.py",
        project_root / "tests" / "core" / "enums" / "test_parameterized_instrument.py",
        project_root / "tests" / "core" / "enums" / "test_simplified_instrument.py",
        project_root / "tests" / "core" / "enums" / "test_simplified_modulator.py",
        project_root / "tests" / "core" / "enums" / "test_context.py"
    ]
    
    # Verify all destination files exist
    missing_files = [str(f) for f in dest_files if not f.exists()]
    if missing_files:
        print("Error: The following destination files do not exist:")
        for f in missing_files:
            print(f"  - {f}")
        print("Migration aborted. Please ensure all destination files exist before removing source files.")
        return 1
    
    # Create destination directory if it doesn't exist (should already exist)
    os.makedirs((project_root / "tests" / "core" / "enums").as_posix(), exist_ok=True)
    
    # Remove source files
    print("Removing source files:")
    for source_file in source_files:
        if source_file.exists():
            print(f"  - {source_file}")
            os.remove(source_file)
        else:
            print(f"  - {source_file} (not found, skipping)")
    
    # Remove empty directory if it exists
    enum_dir = project_root / "tests" / "api" / "enums"
    if enum_dir.exists() and not any(enum_dir.iterdir()):
        print(f"Removing empty directory: {enum_dir}")
        shutil.rmtree(enum_dir)
    
    print("\nMigration completed successfully.")
    print("\nTest files have been moved from:")
    print("  - tests/api/utils/enums.py")
    print("  - tests/api/enums/__init__.py")
    print("to:")
    print("  - tests/core/enums/*")
    
    # Remind user to run tests
    print("\nPlease run tests to verify the migration:")
    print("  python run_tests.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())