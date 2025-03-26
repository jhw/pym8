#!/usr/bin/env python3
import argparse
import os
import sys
import yaml
import logging

from m8.api.project import M8Project
from m8.api.chains import M8ChainStep, M8Chain
from m8.api import M8Block

def hex_dump(data, width=16):
    result = []
    for i in range(0, len(data), width):
        chunk = data[i:i+width]
        hex_values = ' '.join(f"{b:02X}" for b in chunk)
        ascii_values = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        result.append(f"{i:08X}  {hex_values:<{width * 3}} |{ascii_values}|")
    return "\n".join(result)

def display_chain(project, chain, chain_idx, output_format):
    if output_format == "yaml":
        # NOTE: This attempt to fix FX serialization doesn't work yet
        # There appears to be a deeper issue with context lifecycle management
        # Despite setting project on context manager here, FX keys still appear as 
        # numeric values instead of string enums (e.g., "7" instead of "VOL")
        # TODO: Investigate context propagation between project load and serialization
        from m8.api.utils.enums import M8InstrumentContext
        context = M8InstrumentContext.get_instance()
        context.set_project(project)
        
        chain_dict = chain.as_dict()
        chain_dict["index"] = chain_idx
        
        phrases = []
        for step in chain:
            if not step.is_empty():
                phrase_idx = step.phrase
                if phrase_idx < len(project.phrases):
                    phrase = project.phrases[phrase_idx]
                    if not phrase.is_empty():
                        phrase_dict = phrase.as_dict()
                        phrase_dict["index"] = phrase_idx
                        phrases.append(phrase_dict)
        
        result = {
            "chain": chain_dict,
            "referenced_phrases": phrases
        }
        
        print(yaml.dump(result, sort_keys=False, default_flow_style=False))
    else:
        raw_data = chain.write()
        print(f"Chain {chain_idx} - Raw binary data ({len(raw_data)} bytes):")
        print(hex_dump(raw_data))

def main():
    parser = argparse.ArgumentParser(description="Inspect chains and their phrases in an M8 project file")
    parser.add_argument("file_path", help="Path to the M8 project file (.m8s)")
    parser.add_argument("--format", "-f", choices=["yaml", "bytes"], default="yaml", 
                        help="Output format (yaml or bytes, default: yaml)")
    
    args = parser.parse_args()
    
    logging.getLogger("m8.api").setLevel(logging.ERROR)
    
    if not os.path.exists(args.file_path):
        print(f"Error: File {args.file_path} does not exist", file=sys.stderr)
        return 1
    
    if not args.file_path.lower().endswith(".m8s"):
        print(f"Warning: File {args.file_path} does not have .m8s extension", file=sys.stderr)
    
    try:
        project = M8Project.read_from_file(args.file_path)
        
        non_empty_chains = []
        for idx, chain in enumerate(project.chains):
            if not chain.is_empty():
                non_empty_chains.append((idx, chain))
        
        if not non_empty_chains:
            print("No non-empty chains found in the project", file=sys.stderr)
            return 1
        
        print(f"Found {len(non_empty_chains)} non-empty chains")
        
        for idx, chain in non_empty_chains:
            non_empty_steps = sum(1 for step in chain if not step.is_empty())
            print(f"\nChain {idx}: {non_empty_steps} non-empty steps")
            
            for step_idx, step in enumerate(chain):
                if not step.is_empty():
                    phrase_idx = step.phrase
                    phrase = project.phrases[phrase_idx] if phrase_idx < len(project.phrases) else None
                    is_valid = phrase is not None and not phrase.is_empty()
                    status = "valid" if is_valid else "empty/invalid"
                    print(f"  Step {step_idx}: Phrase {phrase_idx} (transpose: {step.transpose}) - {status}")
            
            while True:
                response = input("Dump chain details? (y/n/q): ").lower()
                if response == 'y':
                    print("\n" + "="*50)
                    display_chain(project, chain, idx, args.format)
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