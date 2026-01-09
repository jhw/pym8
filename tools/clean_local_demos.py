#!/usr/bin/env python3

"""
Clean locally generated demo projects

This script removes the tmp/demos directory containing generated demo projects.

Usage:
    python tools/clean_local_demos.py          # Clean all local demos
    python tools/clean_local_demos.py --force  # Skip confirmation prompt

Safety features:
- Confirmation prompt before deletion (unless --force is used)
- Only removes tmp/demos directory
"""

import sys
import shutil
import argparse
from pathlib import Path


DEMOS_DIR = Path("tmp/demos")


def confirm_deletion():
    """Ask user to confirm deletion"""
    if not DEMOS_DIR.exists():
        print(f"Demos directory not found: {DEMOS_DIR}")
        return False

    # Count items to be deleted
    m8s_files = list(DEMOS_DIR.glob("**/*.m8s"))
    sample_files = list(DEMOS_DIR.glob("**/*.wav"))
    subdirs = [d for d in DEMOS_DIR.rglob("*") if d.is_dir()]

    print(f"\nFound demos directory:")
    print(f"  Location: {DEMOS_DIR.absolute()}")
    print(f"  Subdirectories: {len(subdirs)}")
    print(f"  M8 projects: {len(m8s_files)}")
    print(f"  Sample files: {len(sample_files)}")

    # Ask for confirmation
    response = input("\nAre you sure you want to delete all local demos? (yes/no): ")
    return response.lower() in ['yes', 'y']


def clean_local_demos(force=False):
    """Remove tmp/demos directory"""
    if not DEMOS_DIR.exists():
        print(f"No demos directory found: {DEMOS_DIR}")
        return True

    # Confirm deletion unless forced
    if not force:
        if not confirm_deletion():
            print("\nDeletion cancelled")
            return False

    # Perform deletion
    try:
        print(f"\nDeleting: {DEMOS_DIR}")
        shutil.rmtree(DEMOS_DIR)
        print(f"Successfully removed {DEMOS_DIR}")
        return True
    except Exception as e:
        print(f"Error deleting directory: {e}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Clean locally generated demo projects"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt"
    )

    args = parser.parse_args()
    success = clean_local_demos(force=args.force)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
