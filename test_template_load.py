#!/usr/bin/env python

"""
Test script to verify non-zero defaults are applied when loading from templates.
This is the actual bug scenario - loading instruments from a template file.
"""

from m8.api.project import M8Project

def test_template_loading():
    """Load a project from template and check if defaults are applied"""

    print("Loading project from template...")
    project = M8Project.initialise()

    # Check instrument 0 - should be an empty slot with defaults
    # The template has empty instrument slots (type=0x00)
    inst = project.instruments[0]

    print(f"\nInstrument 0 type: {inst.write()[0]}")

    if hasattr(inst, 'get'):
        print("\nInstrument 0 parameter values after loading template:")
        print(f"  Type (offset 0): 0x{inst.get(0):02X}")
        print(f"  FINETUNE (offset 17): 0x{inst.get(17):02X} (expected 0x80 if sampler)")
        print(f"  LENGTH (offset 22): 0x{inst.get(22):02X} (expected 0xFF if sampler)")
        print(f"  CUTOFF (offset 25): 0x{inst.get(25):02X} (expected 0xFF if sampler)")
        print(f"  PAN (offset 29): 0x{inst.get(29):02X} (expected 0x80 if sampler)")
        print(f"  DRY (offset 30): 0x{inst.get(30):02X} (expected 0xC0 if sampler)")
    else:
        print("\nNo get() method - using older API")

    # Now let's check a slot that we know should be empty
    # and see if it would have correct defaults if we were to use it
    output_path = "test_template_load.m8s"
    print(f"\nWriting project to {output_path}...")
    m8s_data = project.write()

    with open(output_path, 'wb') as f:
        f.write(m8s_data)

    # Read the bytes directly
    inst_offset = 80446  # Instrument 0 offset
    print(f"\nDirect byte inspection of written file (Instrument 0):")
    print(f"  Type (offset 0): 0x{m8s_data[inst_offset]:02X}")
    print(f"  FINETUNE (offset 17): 0x{m8s_data[inst_offset + 17]:02X}")
    print(f"  LENGTH (offset 22): 0x{m8s_data[inst_offset + 22]:02X}")
    print(f"  CUTOFF (offset 25): 0x{m8s_data[inst_offset + 25]:02X}")
    print(f"  PAN (offset 29): 0x{m8s_data[inst_offset + 29]:02X}")
    print(f"  DRY (offset 30): 0x{m8s_data[inst_offset + 30]:02X}")

if __name__ == '__main__':
    test_template_loading()
