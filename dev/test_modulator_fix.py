#!/usr/bin/env python3

from m8.api.modulators import M8Modulator

def test_modulator_fix():
    """Test the fixed modulator implementation with AHD_ENVELOPE parameters."""
    print("=== Testing AHD_ENVELOPE with decay parameter ===")
    
    # Create a modulator with specific decay value
    mod = M8Modulator(
        modulator_type="AHD_ENVELOPE", 
        destination=0x1,  # VOLUME = 0x1
        amount=0xFF,
        attack=0x20,
        hold=0x40,
        decay=0x80
    )
    
    print(f"Original values:")
    print(f"  attack = 0x{mod.params.attack:02X}")
    print(f"  hold = 0x{mod.params.hold:02X}")
    print(f"  decay = 0x{mod.params.decay:02X}")
    
    # Write to binary
    binary = mod.write()
    print(f"Binary data: {' '.join([f'0x{b:02X}' for b in binary])}")
    
    # Read back
    new_mod = M8Modulator()
    new_mod.read(binary)
    
    print(f"Values after roundtrip:")
    print(f"  attack = 0x{new_mod.params.attack:02X}")
    print(f"  hold = 0x{new_mod.params.hold:02X}")
    print(f"  decay = 0x{new_mod.params.decay:02X}")
    
    # Check if values match
    print("Parameter preservation check:")
    print(f"  attack: {'PRESERVED' if mod.params.attack == new_mod.params.attack else 'LOST'}")
    print(f"  hold: {'PRESERVED' if mod.params.hold == new_mod.params.hold else 'LOST'}")
    print(f"  decay: {'PRESERVED' if mod.params.decay == new_mod.params.decay else 'LOST'}")
    
    print("\n=== Test completed successfully ===")

if __name__ == "__main__":
    test_modulator_fix()