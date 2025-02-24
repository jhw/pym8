from enum import IntEnum

def generate_notes_enum():
    # Define all notes without the # symbol
    raw_note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    enum_names = ['C', 'C_SHARP', 'D', 'D_SHARP', 'E', 'F', 'F_SHARP', 'G', 'G_SHARP', 'A', 'A_SHARP', 'B']
    
    enum_values = {}
    note_value = 0
    
    # Generate note values starting with C_1 (0x00)
    for octave in range(1, 10):  # From octave 1 to 9
        for i, enum_name in enumerate(enum_names):
            # Create the enum key with octave
            key = f"{enum_name}_{octave}"
            enum_values[key] = note_value
            note_value += 1
            
            # Stop at G_9 if that's the highest note
            if octave == 9 and enum_name == 'G':
                break
    
    return IntEnum('M8Notes', enum_values)

# Create the enum
M8Notes = generate_notes_enum()

