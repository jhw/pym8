#!/usr/bin/env python3

import os
import sys
import tempfile
from m8.api.modulators import M8Modulator, BLOCK_SIZE
from m8.config import get_modulator_type_field_def
from m8.api import project

def debug_modulator_params():
    """
    Debug script to demonstrate modulator parameter read/write inconsistency.
    This specifically focuses on the AHD_ENVELOPE modulator's decay parameter,
    which has offset 4 but gets lost during binary serialization/deserialization.
    """
    print(f"Modulator block size: {BLOCK_SIZE} bytes\n")
    
    # Create a temporary path for the binary data
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp_path = temp.name

    try:
        # Part 1: Create different AHD envelopes with varying parameters
        print("=== Creating modulators with specific parameter values ===")
        modulators = []
        
        # Create modulators with different parameter settings
        # Use numeric values for destination (0x1 = VOLUME)
        # to avoid enum conversion issues
        
        # Modulator 1: Default values for hold (0x00) and decay (default 0x80)
        mod1 = M8Modulator(
            modulator_type="AHD_ENVELOPE",
            destination=0x1,  # VOLUME = 0x1
            amount=0xFF,
            attack=0x00
        )
        modulators.append(("Default", mod1))
        
        # Modulator 2: Custom decay value (0x40)
        mod2 = M8Modulator(
            modulator_type="AHD_ENVELOPE",
            destination=0x1,  # VOLUME = 0x1
            amount=0xFF,
            attack=0x00,
            decay=0x40
        )
        modulators.append(("Custom decay", mod2))
        
        # Modulator 3: Custom hold value (0x80)
        mod3 = M8Modulator(
            modulator_type="AHD_ENVELOPE",
            destination=0x1,  # VOLUME = 0x1
            amount=0xFF,
            attack=0x00,
            hold=0x80
        )
        modulators.append(("Custom hold", mod3))
        
        # Modulator 4: Both custom decay (0x40) and hold (0x80)
        mod4 = M8Modulator(
            modulator_type="AHD_ENVELOPE",
            destination=0x1,  # VOLUME = 0x1
            amount=0xFF,
            attack=0x00,
            hold=0x80,
            decay=0x40
        )
        modulators.append(("Custom hold & decay", mod4))
        
        # Part 2: Show parameter values and their offsets from format config
        print("\n=== Parameter offsets in configuration ===")
        # Get the decay parameter definition from config
        decay_field_def = get_modulator_type_field_def("AHD_ENVELOPE", "decay")
        hold_field_def = get_modulator_type_field_def("AHD_ENVELOPE", "hold")
        
        print(f"decay parameter offset: {decay_field_def['offset']}")
        print(f"hold parameter offset: {hold_field_def['offset']}")
        print(f"Logical position of decay in block: 2 + {decay_field_def['offset']} = {2 + decay_field_def['offset']}")
        print(f"Logical position of hold in block: 2 + {hold_field_def['offset']} = {2 + hold_field_def['offset']}")
        print(f"Block size: {BLOCK_SIZE}")
        
        # Part 3: Test binary serialization and deserialization
        print("\n=== Testing binary round trip for each modulator ===")
        for name, mod in modulators:
            # Show original parameter values
            print(f"\nModulator: {name}")
            print(f"Original values:")
            print(f"  decay = 0x{mod.params.decay:02X}")
            print(f"  hold = 0x{mod.params.hold:02X}")
            
            # Write to binary
            binary = mod.write()
            print(f"Binary data: {' '.join([f'0x{b:02X}' for b in binary])}")
            
            # Show which position contains which value
            print(f"Binary data by position:")
            print(f"  Position 0 (type & dest): 0x{binary[0]:02X}")
            print(f"  Position 1 (amount): 0x{binary[1]:02X}")
            print(f"  Position 2 (typically attack): 0x{binary[2]:02X}")
            print(f"  Position 3 (typically hold): 0x{binary[3]:02X}")
            print(f"  Position 4 (would be decay): 0x{binary[4]:02X}")
            print(f"  Position 5 (last byte): 0x{binary[5]:02X}")
            
            # Now read back from binary
            new_mod = M8Modulator()
            new_mod.read(binary)
            
            # Show values after reading
            print(f"Values after roundtrip:")
            print(f"  decay = 0x{new_mod.params.decay:02X}")
            print(f"  hold = 0x{new_mod.params.hold:02X}")
            
            # Check if values were preserved
            decay_preserved = mod.params.decay == new_mod.params.decay
            hold_preserved = mod.params.hold == new_mod.params.hold
            
            print(f"Values preserved?")
            print(f"  decay: {'YES' if decay_preserved else 'NO - LOST DURING ROUNDTRIP'}")
            print(f"  hold: {'YES' if hold_preserved else 'NO - LOST DURING ROUNDTRIP'}")
            
        # Part 4: Show impact in a project context
        print("\n=== Testing in project context ===")
        # Initialize a project
        test_project = project.M8Project.initialise()
        
        # Create a direct byte buffer with all modulators
        with open(temp_path, 'wb') as f:
            # Write all modulators to one file
            for _, mod in modulators:
                binary = mod.write()
                f.write(binary)
        
        # Read back and verify
        with open(temp_path, 'rb') as f:
            data = f.read()
            
        print(f"Read {len(data)} bytes from combined file")
        
        # Process each modulator block
        for i in range(len(modulators)):
            name, orig_mod = modulators[i]
            start = i * BLOCK_SIZE
            block_data = data[start:start + BLOCK_SIZE]
            
            # Read modulator from binary
            mod = M8Modulator()
            mod.read(block_data)
            
            print(f"\nModulator {i+1} ({name}):")
            print(f"  Original decay: 0x{orig_mod.params.decay:02X}")
            print(f"  Read decay:     0x{mod.params.decay:02X}")
            print(f"  Original hold:  0x{orig_mod.params.hold:02X}")
            print(f"  Read hold:      0x{mod.params.hold:02X}")
            
            # Show binary data for debugging
            print(f"  Binary:         {' '.join([f'0x{b:02X}' for b in block_data])}")
            
            # Check status
            if orig_mod.params.decay != mod.params.decay:
                print("  ⚠️ DECAY VALUE LOST IN BINARY SERIALIZATION")
            if orig_mod.params.hold != mod.params.hold:
                print("  ⚠️ HOLD VALUE LOST IN BINARY SERIALIZATION")
            
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
            
    print("\n=== Conclusion ===")
    print("The problem is due to parameter offsets in the format config that exceed")
    print("the block size. The decay parameter has offset 4, which would place it")
    print("at position 6 (2+4), but the block size is only 6 bytes, so it gets lost.")
    print("While binary is written with all parameters, when reading it back,")
    print("the decay parameter isn't found at its expected position.")

if __name__ == "__main__":
    debug_modulator_params()