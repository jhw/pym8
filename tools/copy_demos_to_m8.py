#!/usr/bin/env python3

"""
Copy demo projects to M8 device

This script copies demo projects from tmp/demos/ to the M8 device.
Demos are copied to /Volumes/M8/Songs/pym8-demos/

Usage:
    python tools/copy_demos_to_m8.py              # Copy all demos
    python tools/copy_demos_to_m8.py --test       # Test mode (dry run to tmp/virtual-m8)
    python tools/copy_demos_to_m8.py sampler_demo # Copy specific demo
"""

import sys
import shutil
import argparse
from pathlib import Path


def find_demos(demo_name=None):
    """Find demo directories to copy"""
    demos_dir = Path("tmp/demos")

    if not demos_dir.exists():
        raise FileNotFoundError(f"Demos directory not found: {demos_dir}")

    # Find all demo directories
    demo_dirs = [d for d in demos_dir.iterdir() if d.is_dir()]

    if not demo_dirs:
        raise FileNotFoundError(f"No demo directories found in {demos_dir}")

    # Filter to specific demo if requested
    if demo_name:
        demo_dirs = [d for d in demo_dirs if d.name == demo_name]
        if not demo_dirs:
            raise FileNotFoundError(f"Demo '{demo_name}' not found in {demos_dir}")

    return demo_dirs


def copy_demo_to_m8(demo_dir, m8_path, test_mode=False):
    """Copy a single demo to M8"""

    # Create target directory on M8
    target_dir = m8_path / "Songs" / "pym8-demos" / demo_dir.name

    # Create target directories
    target_dir.mkdir(parents=True, exist_ok=True)
    target_samples_dir = target_dir / "samples"
    target_samples_dir.mkdir(exist_ok=True)

    # Find M8 project file
    m8s_files = list(demo_dir.glob("*.m8s"))
    if not m8s_files:
        print(f"  Warning: No .m8s file found in {demo_dir.name}, skipping...")
        return False

    m8s_file = m8s_files[0]

    # Copy M8 project file
    target_m8s = target_dir / m8s_file.name
    print(f"  Copying {m8s_file.name} to {target_dir}")
    shutil.copy2(m8s_file, target_m8s)

    # Copy samples
    samples_dir = demo_dir / "samples"
    if samples_dir.exists():
        for sample_file in samples_dir.glob("*.wav"):
            target_sample = target_samples_dir / sample_file.name
            print(f"  Copying {sample_file.name} to {target_samples_dir}")
            shutil.copy2(sample_file, target_sample)
    else:
        print(f"  Note: No samples directory found in {demo_dir.name}")

    return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Copy demo projects to M8 device")
    parser.add_argument("demo", nargs="?", help="Specific demo to copy (optional)")
    parser.add_argument("--test", action="store_true",
                       help="Test mode: copy to tmp/virtual-m8 instead of real M8")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be copied without actually copying")
    args = parser.parse_args()

    # Set up M8 path
    if args.test:
        m8_path = Path("tmp/virtual-m8")
        m8_path.mkdir(exist_ok=True, parents=True)
        print(f"TEST MODE: Using {m8_path} instead of real M8 device")
    else:
        m8_path = Path("/Volumes/M8")
        if not m8_path.exists():
            print("Error: M8 not found at /Volumes/M8")
            print("Please ensure the M8 is connected and mounted.")
            sys.exit(1)

    # Find demos to copy
    try:
        demo_dirs = find_demos(args.demo)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"\nFound {len(demo_dirs)} demo(s) to copy")
    print(f"Destination: {m8_path}/Songs/pym8-demos/\n")

    # Copy each demo
    copied_count = 0
    for demo_dir in demo_dirs:
        print(f"Copying demo: {demo_dir.name}")

        if args.dry_run:
            print(f"  [DRY RUN] Would copy {demo_dir.name}")
            # Still count as copied for summary
            copied_count += 1
            continue

        try:
            if copy_demo_to_m8(demo_dir, m8_path, args.test):
                copied_count += 1
                print(f"  ✓ Copied {demo_dir.name}")
        except Exception as e:
            print(f"  ✗ Error copying {demo_dir.name}: {e}")

    # Print summary
    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Successfully copied {copied_count}/{len(demo_dirs)} demo(s)")

    if not args.test and not args.dry_run:
        print("\nDemos are now available on your M8 in:")
        print("  Songs/pym8-demos/")


if __name__ == '__main__':
    main()
