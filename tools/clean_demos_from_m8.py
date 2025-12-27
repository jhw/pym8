#!/usr/bin/env python3

"""
Clean pym8 demo projects from M8 device

This script removes the pym8-demos directory from the M8 device.
Location: /Volumes/M8/Songs/pym8-demos/

Usage:
    python tools/clean_demos_from_m8.py              # Clean all pym8 demos
    python tools/clean_demos_from_m8.py --test       # Test mode (dry run to tmp/virtual-m8)
    python tools/clean_demos_from_m8.py --force      # Skip confirmation prompt

Safety features:
- Confirmation prompt before deletion (unless --force is used)
- Only removes pym8-demos directory (not other M8 content)
- Test mode available for dry runs
"""

import sys
import shutil
import argparse
from pathlib import Path


def confirm_deletion(m8_path, test_mode=False):
    """Ask user to confirm deletion"""
    target_dir = m8_path / "Songs" / "pym8-demos"

    if not target_dir.exists():
        print(f"pym8-demos directory not found on M8: {target_dir}")
        return False

    # Count items to be deleted
    m8s_files = list(target_dir.glob("**/*.m8s"))
    sample_files = list(target_dir.glob("**/samples/*.wav"))
    subdirs = [d for d in target_dir.iterdir() if d.is_dir()]

    print(f"\nFound pym8-demos directory on {'test' if test_mode else 'M8'}:")
    print(f"  Location: {target_dir}")
    print(f"  Subdirectories: {len(subdirs)}")
    print(f"  M8 projects: {len(m8s_files)}")
    print(f"  Sample files: {len(sample_files)}")

    if test_mode:
        print("\n[TEST MODE] Would delete this directory")
        return True

    # Ask for confirmation
    response = input("\nAre you sure you want to delete all pym8 demos? (yes/no): ")
    return response.lower() in ['yes', 'y']


def clean_demos_from_m8(m8_path, test_mode=False, force=False):
    """Remove pym8-demos directory from M8"""
    target_dir = m8_path / "Songs" / "pym8-demos"

    if not target_dir.exists():
        print(f"✓ No pym8-demos found on {'test' if test_mode else 'M8'}: {target_dir}")
        return True

    # Confirm deletion unless forced
    if not force:
        if not confirm_deletion(m8_path, test_mode):
            print("\nDeletion cancelled")
            return False

    # Perform deletion
    if test_mode:
        print(f"\n[TEST MODE] Would delete: {target_dir}")
        return True
    else:
        try:
            print(f"\nDeleting: {target_dir}")
            shutil.rmtree(target_dir)
            print(f"✓ Successfully removed pym8-demos from M8")
            return True
        except Exception as e:
            print(f"✗ Error deleting directory: {e}")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Clean pym8 demo projects from M8 device"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode - dry run using tmp/virtual-m8 instead of /Volumes/M8"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt"
    )

    args = parser.parse_args()

    # Determine M8 path
    if args.test:
        m8_path = Path("tmp/virtual-m8")
        m8_path.mkdir(parents=True, exist_ok=True)
        print(f"[TEST MODE] Using virtual M8 at: {m8_path.absolute()}\n")
    else:
        m8_path = Path("/Volumes/M8")
        if not m8_path.exists():
            print(f"✗ Error: M8 device not found at {m8_path}")
            print("\nIs your M8 device connected and mounted?")
            print("Try:")
            print("  1. Connect M8 via USB")
            print("  2. Make sure it's in disk mode")
            print("  3. Check it appears in /Volumes/")
            print("\nOr use --test flag for dry run")
            return 1

    # Clean demos
    success = clean_demos_from_m8(m8_path, test_mode=args.test, force=args.force)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
