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
        # Set up and log details about the context manager
        import logging
        logger = logging.getLogger("inspect_chains")
        logger.debug("Setting up context for chain serialization")
        
        from m8.core.enums import M8InstrumentContext, serialize_param_enum_value
        from m8.config import load_format_config
        
        # Get the context manager
        context = M8InstrumentContext.get_instance()
        logger.debug(f"Initial context state: project={context.project is not None}, "
                  f"current_instrument_id={context.current_instrument_id}, "
                  f"current_instrument_type_id={context.current_instrument_type_id}")
        
        # Set the project on the context manager
        logger.debug(f"Setting project on context manager: {project}")
        context.set_project(project)
        
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
        
        chain_dict = chain.as_dict()
        chain_dict["index"] = chain_idx
        
        phrases = []
        logger.debug("Processing chain steps to serialize phrases")
        for step_idx, step in enumerate(chain):
            if not step.is_empty():
                phrase_idx = step.phrase
                logger.debug(f"Step {step_idx} references phrase {phrase_idx}")
                if phrase_idx < len(project.phrases):
                    phrase = project.phrases[phrase_idx]
                    if not phrase.is_empty():
                        logger.debug(f"Phrase {phrase_idx} is valid, serializing")
                        
                        # Get instrument from the first non-empty step in the phrase
                        # Chain steps don't have instrument references, only phrase steps do
                        instrument_id = None
                        for phrase_step in phrase:
                            if not phrase_step.is_empty() and phrase_step.instrument != 0xFF:
                                instrument_id = phrase_step.instrument
                                logger.debug(f"Found instrument {instrument_id} referenced in phrase {phrase_idx}")
                                break
                                
                        if instrument_id is not None and instrument_id != 0xFF:
                            # Log instrument context setup
                            logger.debug(f"Creating context for instrument {instrument_id}")
                            
                            # Get the instrument from the project
                            if instrument_id < len(project.instruments):
                                instrument = project.instruments[instrument_id]
                                logger.debug(f"Found instrument: {instrument.__class__.__name__}")
                                
                                # Check if it has type information
                                if hasattr(instrument, 'instrument_type'):
                                    instrument_type = instrument.instrument_type
                                    logger.debug(f"Instrument type: {instrument_type}")
                                
                                # Get instrument type id
                                instrument_type_id = context.get_instrument_type_id(instrument_id)
                                logger.debug(f"Got instrument_type_id: {instrument_type_id}")
                                
                                # Important: Set context for serialization
                                if instrument_type_id is not None:
                                    with context.with_instrument(instrument_id=instrument_id, 
                                                            instrument_type_id=instrument_type_id):
                                        logger.debug("Serializing phrase with instrument context")
                                        phrase_dict = phrase.as_dict()
                                        phrase_dict["index"] = phrase_idx
                                        phrases.append(phrase_dict)
                                else:
                                    logger.warning("Failed to get instrument type ID, serializing without context")
                                    phrase_dict = phrase.as_dict()
                                    phrase_dict["index"] = phrase_idx
                                    phrases.append(phrase_dict)
                            else:
                                logger.warning(f"Invalid instrument ID {instrument_id}, serializing without context")
                                phrase_dict = phrase.as_dict()
                                phrase_dict["index"] = phrase_idx
                                phrases.append(phrase_dict)
                        else:
                            logger.debug("No instrument reference found in phrase, serializing without context")
                            phrase_dict = phrase.as_dict()
                            phrase_dict["index"] = phrase_idx
                            phrases.append(phrase_dict)
        
        result = {
            "chain": chain_dict,
            "referenced_phrases": phrases
        }
        
        # Custom representer function to format integers as hex
        def represent_int_as_hex(dumper, data):
            if isinstance(data, int):
                # Format as 0xNN
                return dumper.represent_scalar('tag:yaml.org,2002:str', f"0x{data:02X}")
            return dumper.represent_scalar('tag:yaml.org,2002:int', str(data))
            
        # Add the representer to the YAML dumper
        yaml.add_representer(int, represent_int_as_hex)
        
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
