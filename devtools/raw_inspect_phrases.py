#!/usr/bin/env python3
import argparse
import os
import sys
import yaml

def load_format_config():
    """Load the format_config.yaml file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(os.path.dirname(script_dir), 'm8', 'format_config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def hex_dump(data, width=16):
    """Prints data in a readable hex dump format."""
    result = []
    for i in range(0, len(data), width):
        chunk = data[i:i+width]
        hex_values = ' '.join(f"{b:02X}" for b in chunk)
        ascii_values = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        result.append(f"{i:08X}  {hex_values:<{width * 3}} |{ascii_values}|")
    return "\n".join(result)

def is_empty_phrase_step(step_data):
    """Check if a phrase step is empty."""
    # A phrase step is empty if its note, velocity, and instrument values are all 0xFF (255)
    return step_data[0] == 0xFF and step_data[1] == 0xFF and step_data[2] == 0xFF

def main():
    parser = argparse.ArgumentParser(description="Raw inspect phrases in an M8 project file")
    parser.add_argument("file_path", help="Path to the M8 project file (.m8s)")
    
    args = parser.parse_args()
    
    # Check if file exists
    if not os.path.exists(args.file_path):
        print(f"Error: File {args.file_path} does not exist", file=sys.stderr)
        return 1
    
    # Check file extension
    if not args.file_path.lower().endswith(".m8s"):
        print(f"Error: File {args.file_path} does not have .m8s extension", file=sys.stderr)
        return 1
    
    try:
        # Load configuration
        config = load_format_config()
        
        # Get phrases offset, step size, and count from config
        phrases_offset = config["phrases"]["offset"]
        phrase_step_size = config["phrases"]["step_size"]
        phrase_step_count = config["phrases"]["step_count"]
        phrase_count = config["phrases"]["count"]
        
        # Calculate the size of a complete phrase
        phrase_size = phrase_step_size * phrase_step_count
        
        # Read the file
        with open(args.file_path, 'rb') as f:
            data = f.read()
        
        # Identify and process non-empty phrases
        non_empty_phrases = []
        
        for phrase_idx in range(phrase_count):
            phrase_start_offset = phrases_offset + (phrase_idx * phrase_size)
            phrase_end_offset = phrase_start_offset + phrase_size
            
            # Ensure we don't read past the end of the file
            if phrase_end_offset > len(data):
                break
                
            phrase_data = data[phrase_start_offset:phrase_end_offset]
            
            # Check if any step in the phrase is non-empty
            has_non_empty_steps = False
            non_empty_step_indices = []
            
            for step_idx in range(phrase_step_count):
                step_start_offset = step_idx * phrase_step_size
                step_end_offset = step_start_offset + phrase_step_size
                
                step_data = phrase_data[step_start_offset:step_end_offset]
                
                if not is_empty_phrase_step(step_data):
                    has_non_empty_steps = True
                    non_empty_step_indices.append(step_idx)
            
            if has_non_empty_steps:
                non_empty_phrases.append((phrase_idx, phrase_data, non_empty_step_indices))
        
        # Display information about found phrases
        print(f"Found {len(non_empty_phrases)} non-empty phrases")
        
        # Iterate through non-empty phrases
        for phrase_idx, phrase_data, non_empty_step_indices in non_empty_phrases:
            print(f"\nPhrase {phrase_idx}: {len(non_empty_step_indices)} non-empty steps")
            
            for step_idx in non_empty_step_indices:
                step_start_offset = step_idx * phrase_step_size
                step_end_offset = step_start_offset + phrase_step_size
                
                step_data = phrase_data[step_start_offset:step_end_offset]
                
                # Get note (first byte), velocity (second byte), and instrument (third byte)
                note = step_data[0]
                velocity = step_data[1]
                instrument = step_data[2]
                
                # Extract FX data (next 6 bytes for 3 FX pairs)
                fx_data = step_data[3:9]
                fx_info = ""
                for i in range(0, len(fx_data), 2):
                    fx_key = fx_data[i]
                    fx_value = fx_data[i+1]
                    if fx_key != 0xFF:  # If not empty
                        fx_info += f" FX{i//2}: {fx_key}/{fx_value}"
                
                print(f"  Step {step_idx}: Note {note}, Vel {velocity}, Inst {instrument}{fx_info}")
            
            # Prompt user
            while True:
                response = input("Dump phrase details? (y/n/q): ").lower()
                if response == 'y':
                    print("\n" + "="*50)
                    print(f"Raw binary data for Phrase {phrase_idx} ({len(phrase_data)} bytes):")
                    print(hex_dump(phrase_data))
                    print("="*50)
                    break
                elif response == 'n':
                    break
                elif response == 'q':
                    print("Exiting...")
                    return 0
                else:
                    print("Invalid option. Please enter 'y', 'n', or 'q'")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())