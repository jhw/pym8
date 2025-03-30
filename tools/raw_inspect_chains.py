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

def is_empty_chain_step(step_data):
    """Check if a chain step is empty."""
    # A chain step is empty if its phrase value is 0xFF (255)
    return step_data[0] == 0xFF

def main():
    parser = argparse.ArgumentParser(description="Raw inspect chains in an M8 project file")
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
        
        # Get chains offset, step size, and count from config
        chains_offset = config["chains"]["offset"]
        chain_step_size = config["chains"]["step_size"]
        chain_step_count = config["chains"]["step_count"]
        chain_count = config["chains"]["count"]
        
        # Calculate the size of a complete chain
        chain_size = chain_step_size * chain_step_count
        
        # Read the file
        with open(args.file_path, 'rb') as f:
            data = f.read()
        
        # Identify and process non-empty chains
        non_empty_chains = []
        
        for chain_idx in range(chain_count):
            chain_start_offset = chains_offset + (chain_idx * chain_size)
            chain_end_offset = chain_start_offset + chain_size
            
            # Ensure we don't read past the end of the file
            if chain_end_offset > len(data):
                break
                
            chain_data = data[chain_start_offset:chain_end_offset]
            
            # Check if any step in the chain is non-empty
            has_non_empty_steps = False
            non_empty_step_indices = []
            
            for step_idx in range(chain_step_count):
                step_start_offset = step_idx * chain_step_size
                step_end_offset = step_start_offset + chain_step_size
                
                step_data = chain_data[step_start_offset:step_end_offset]
                
                if not is_empty_chain_step(step_data):
                    has_non_empty_steps = True
                    non_empty_step_indices.append(step_idx)
            
            if has_non_empty_steps:
                non_empty_chains.append((chain_idx, chain_data, non_empty_step_indices))
        
        # Display information about found chains
        print(f"Found {len(non_empty_chains)} non-empty chains")
        
        # Iterate through non-empty chains
        for chain_idx, chain_data, non_empty_step_indices in non_empty_chains:
            print(f"\nChain {chain_idx}: {len(non_empty_step_indices)} non-empty steps")
            
            for step_idx in non_empty_step_indices:
                step_start_offset = step_idx * chain_step_size
                step_end_offset = step_start_offset + chain_step_size
                
                step_data = chain_data[step_start_offset:step_end_offset]
                
                # Get phrase index (first byte) and transpose (second byte)
                phrase_idx = step_data[0]
                transpose = step_data[1]
                
                print(f"  Step {step_idx}: Phrase {phrase_idx} (transpose: {transpose})")
            
            # Prompt user
            while True:
                response = input("Dump chain details? (y/n/q): ").lower()
                if response == 'y':
                    print("\n" + "="*50)
                    print(f"Raw binary data for Chain {chain_idx} ({len(chain_data)} bytes):")
                    print(hex_dump(chain_data))
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