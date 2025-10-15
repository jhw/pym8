#!/usr/bin/env python

"""
Test script to create a project with sampler and export to M8S format.
Used for comparing outputs between different versions.
"""

from m8.api.project import M8Project
from m8.api.sampler import M8Sampler

def create_test_project():
    """Create a simple project with a sampler instrument"""

    # Initialize project from template
    project = M8Project.initialise()

    # Set basic metadata
    project.metadata.name = "TESTPROJ"
    project.metadata.tempo = 120

    # Create a NEW sampler instrument with default parameters
    # This should apply non-zero defaults
    sampler = M8Sampler(
        name="SAMP01",
        sample_path="test/sample.wav"
    )

    # Print sampler parameter values to verify defaults
    print("Sampler parameter values after creation:")
    if hasattr(sampler, 'get'):
        # v0.4.6+ uses low-level buffer access
        print(f"  FINETUNE (offset 17): 0x{sampler.get(17):02X} (expected 0x80)")
        print(f"  LENGTH (offset 22): 0x{sampler.get(22):02X} (expected 0xFF)")
        print(f"  CUTOFF (offset 25): 0x{sampler.get(25):02X} (expected 0xFF)")
        print(f"  PAN (offset 29): 0x{sampler.get(29):02X} (expected 0x80)")
        print(f"  DRY (offset 30): 0x{sampler.get(30):02X} (expected 0xC0)")
    else:
        # v0.4.4 uses properties
        print(f"  FINETUNE: 0x{sampler.finetune:02X} (expected 0x80)")
        print(f"  LENGTH: 0x{sampler.length:02X} (expected 0xFF)")
        print(f"  CUTOFF: 0x{sampler.cutoff:02X} (expected 0xFF)")
        print(f"  PAN: 0x{sampler.pan:02X} (expected 0x80)")
        print(f"  DRY: 0x{sampler.dry:02X} (expected 0xC0)")

    # Add sampler to instrument slot 0
    project.instruments[0] = sampler

    return project

def main():
    """Main export function"""

    print("Creating test project with sampler...")
    project = create_test_project()

    # Write M8S file
    output_path = "test_output.m8s"
    print(f"Exporting to {output_path}...")

    m8s_data = project.write()

    with open(output_path, 'wb') as f:
        f.write(m8s_data)

    print(f"✓ Export complete: {output_path}")
    print(f"  File size: {len(m8s_data)} bytes")

if __name__ == '__main__':
    main()
