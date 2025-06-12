#!/usr/bin/env python3
import argparse
import os
import sys
import yaml
import logging
import pandas as pd
from tabulate import tabulate

from m8.api.project import M8Project
from m8.api.chains import M8ChainStep, M8Chain
from m8.api import M8Block

def display_chain_tabular(project, chain, chain_idx):
    """Display chain and phrase data as a pandas DataFrame."""
    # Context management was removed with enum system simplification
    import logging
    logger = logging.getLogger("inspect_chains")
    logger.debug("Inspecting chain with simplified enum system")
    
    # Log information about project instruments
    logger.debug(f"Project has {len(project.instruments)} instruments")
    for i, instr in enumerate(project.instruments):
        if hasattr(instr, 'instrument_type'):
            logger.debug(f"Instrument {i}: type={instr.instrument_type}")
        elif hasattr(instr, 'instrument_type_id'):
            logger.debug(f"Instrument {i}: type_id={instr.instrument_type_id}")
        elif hasattr(instr, 'type'):
            logger.debug(f"Instrument {i}: raw_type={instr.type}")
        elif hasattr(instr, 'data') and len(instr.data) > 0:
            logger.debug(f"Instrument {i}: block_first_byte={instr.data[0]}")
        else:
            logger.debug(f"Instrument {i}: No type information available")
    
    # Load FX config for testing
    fx_config = load_format_config()["fx"]
    logger.debug(f"FX config: {fx_config['fields']['key']}")
    
    # Prepare data for tabular output
    table_data = []
    
    for step_idx, step in enumerate(chain):
        if not step.is_empty():
            phrase_idx = step.phrase
            logger.debug(f"Step {step_idx} references phrase {phrase_idx}")
            if phrase_idx < len(project.phrases):
                phrase = project.phrases[phrase_idx]
                if not phrase.is_empty():
                    logger.debug(f"Phrase {phrase_idx} is valid, serializing")
                    
                    # Get instrument from the first non-empty step in the phrase
                    instrument_id = None
                    for phrase_step in phrase:
                        if not phrase_step.is_empty() and phrase_step.instrument != 0xFF:
                            instrument_id = phrase_step.instrument
                            logger.debug(f"Found instrument {instrument_id} referenced in phrase {phrase_idx}")
                            break
                    
                    # Serialize phrase with simplified enum system
                    logger.debug(f"Serializing phrase {phrase_idx} (instrument: {instrument_id})")
                    phrase_dict = phrase.as_dict()
                    
                    # Extract phrase steps data for tabular view
                    for i, step_data in enumerate(phrase_dict.get('steps', [])):
                        if step_data.get('note') == 0xFF and step_data.get('velocity') == 0xFF:
                            continue  # Skip empty steps
                        
                        row = {
                            'chain_idx': chain_idx,
                            'chain_step': step_idx,
                            'phrase_idx': phrase_idx,
                            'step_idx': i,
                            'note': step_data.get('note'),
                            'velocity': step_data.get('velocity'),
                            'instrument': step_data.get('instrument'),
                        }
                        
                        # Add FX data
                        fx_data = step_data.get('fx', [])
                        for j, fx in enumerate(fx_data[:3]):  # Only include up to 3 FX
                            if not fx.get('key', 0xFF) == 0xFF:  # Only add non-empty FX
                                row[f'fx{j+1}_key'] = fx.get('key')
                                row[f'fx{j+1}_value'] = fx.get('value')
                        
                        table_data.append(row)
    
    # If no data, return early
    if not table_data:
        print(f"No data found for chain {chain_idx}")
        return
        
    # Create pandas DataFrame
    df = pd.DataFrame(table_data)
    
    # Replace 0xFF values with NaN for better readability
    df = df.replace(0xFF, pd.NA)
    
    # Format note values to note names where possible
    if 'note' in df.columns:
        df['note'] = df['note'].apply(lambda x: format_note(x) if pd.notna(x) else pd.NA)
    
    # Format hex values for FX keys
    for col in [c for c in df.columns if 'fx' in c and 'key' in c]:
        df[col] = df[col].apply(lambda x: f"0x{x:02X}" if pd.notna(x) else pd.NA)
    
    # Define column order
    column_order = ['chain_idx', 'chain_step', 'phrase_idx', 'step_idx', 'note', 'velocity', 'instrument']
    fx_columns = [c for c in df.columns if 'fx' in c]
    
    # Sort FX columns to ensure fx1, fx2, fx3 order
    fx_columns.sort()
    
    # Create final column list
    columns = column_order + fx_columns
    
    # Select only columns that exist in the DataFrame
    columns = [c for c in columns if c in df.columns]
    
    # Sort by step_idx for better readability
    df = df.sort_values(['chain_step', 'step_idx'])
    
    # Display the DataFrame
    print(f"\nChain {chain_idx} - Phrase Steps:")
    print(df.to_string(index=False, na_rep='-'))

def format_note(note_value):
    """Convert numeric note value to note name if possible."""
    if note_value is None or pd.isna(note_value):
        return '-'
        
    # If already a string, return it
    if isinstance(note_value, str):
        return note_value
        
    # Notes mapping (0 = C-0, 12 = C-1, etc.)
    note_names = ['C-', 'C#', 'D-', 'D#', 'E-', 'F-', 'F#', 'G-', 'G#', 'A-', 'A#', 'B-']
    
    if 0 <= note_value <= 127:
        octave = note_value // 12
        note = note_value % 12
        return f"{note_names[note]}{octave}"
    else:
        return f"0x{note_value:02X}"  # Use hex for out-of-range values

def main():
    parser = argparse.ArgumentParser(description="Inspect chains and their phrases in an M8 project file")
    parser.add_argument("file_path", help="Path to the M8 project file (.m8s)")
    
    args = parser.parse_args()
    
    # Set up logging - quiet by default, can enable with environment variable
    logging_level = logging.WARNING
    if os.environ.get("M8_DEBUG"):
        logging_level = logging.DEBUG
        
    logging.basicConfig(level=logging_level)
    logging.getLogger("m8.api").setLevel(logging_level)
    logging.getLogger("inspect_chains").setLevel(logging_level)
    
    if not os.path.exists(args.file_path):
        print(f"Error: File {args.file_path} does not exist", file=sys.stderr)
        return 1
    
    if not args.file_path.lower().endswith(".m8s"):
        print(f"Error: File {args.file_path} does not have .m8s extension", file=sys.stderr)
        return 1
    
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
                    display_chain_tabular(project, chain, idx)
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