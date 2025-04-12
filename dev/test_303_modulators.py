#!/usr/bin/env python3

import os
import sys
import tempfile
import yaml
import logging

from m8.api.project import M8Project
from m8.api.instruments.sampler import M8Sampler
from m8.api.phrases import M8Phrase, M8PhraseStep
from m8.api.chains import M8Chain, M8ChainStep
from m8.api.modulators import M8Modulator

def create_and_test_303_project():
    """
    Creates a 303-style project with specific modulator decay parameters,
    saves it to a file, reads it back, and verifies the parameters were preserved.
    """
    print("=== Creating 303-style project with specific modulator decay parameters ===\n")
    
    # Create a temporary directory for the output file
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "HELLO-303.m8s")
        
        # Initialize a new project
        print("Initializing project...")
        project = M8Project.initialise()
        project.metadata.name = "HELLO-303"
        
        # Create a sampler instrument with all params via constructor
        print("Creating sampler instrument...")
        sampler = M8Sampler(
            name="VCO",
            sample_path="/Samples/Chains/erica-pico-vco.wav",
            slice=0x01,         # FILE mode
            filter="LOWPASS",   # Using string value for low-pass filter
            cutoff=0x20,
            res=0xB0,
            amp=0x20,
            chorus=0xC0,        
            delay=0x80
        )
        
        # Add AHD envelope with destination volume
        print("Adding volume AHD envelope modulator with decay=0x80...")
        vol_env = M8Modulator(
            modulator_type="AHD_ENVELOPE", 
            destination="VOLUME",
            amount=0xFF,
            attack=0x00,
            hold=0x00,
            decay=0x80
        )
        sampler.add_modulator(vol_env)
        
        # Add second AHD envelope with destination cutoff
        print("Adding cutoff AHD envelope modulator with decay=0x40...")
        cutoff_env = M8Modulator(
            modulator_type="AHD_ENVELOPE",
            destination="CUTOFF",
            amount=0x80,
            attack=0x00,
            hold=0x00,
            decay=0x40
        )
        sampler.add_modulator(cutoff_env)
        
        # Verify modulator parameters before saving
        print("\n=== Original modulators ===")
        print_modulator_params(vol_env, "Volume Envelope")
        print_modulator_params(cutoff_env, "Cutoff Envelope")
        
        # Add the instrument to the project
        project.instruments[0x00] = sampler
        
        # Create a basic phrase, chain, and song to complete the project
        create_basic_song_structure(project)
        
        # Save the project
        print(f"\nSaving project to {output_path}...")
        project.write_to_file(output_path)
        
        # Now read the project back
        print(f"Reading project from {output_path}...")
        read_project = M8Project.read_from_file(output_path)
        
        # Get the instrument and modulators
        read_sampler = read_project.instruments[0x00]
        read_vol_env = read_sampler.modulators[0]
        read_cutoff_env = read_sampler.modulators[1]
        
        # Verify modulator parameters after reading
        print("\n=== Modulators after serialization and deserialization ===")
        print_modulator_params(read_vol_env, "Volume Envelope")
        print_modulator_params(read_cutoff_env, "Cutoff Envelope")
        
        # Check if the parameters match
        print("\n=== Parameter verification ===")
        verify_modulator_params(vol_env, read_vol_env, "Volume Envelope")
        verify_modulator_params(cutoff_env, read_cutoff_env, "Cutoff Envelope")
        
        print("\n=== Test completed ===")

def print_modulator_params(modulator, label):
    """Print modulator parameters in a readable format."""
    # Custom representer function to format integers as hex
    def represent_int_as_hex(dumper, data):
        if isinstance(data, int):
            return dumper.represent_scalar('tag:yaml.org,2002:str', f"0x{data:02X}")
        return dumper.represent_scalar('tag:yaml.org,2002:int', str(data))
        
    # Add the representer to the YAML dumper
    yaml.add_representer(int, represent_int_as_hex)
    
    mod_dict = modulator.as_dict()
    print(f"{label}:")
    print(f"  Type: {mod_dict['type']}")
    print(f"  Destination: {mod_dict['destination']}")
    print(f"  Amount: {mod_dict.get('amount')}")
    print(f"  Attack: {mod_dict.get('attack')}")
    print(f"  Hold: {mod_dict.get('hold')}")
    print(f"  Decay: {mod_dict.get('decay')}")
    print()

def verify_modulator_params(original, read, label):
    """Compare and verify modulator parameters."""
    original_dict = original.as_dict()
    read_dict = read.as_dict()
    
    # Check key parameters
    type_match = original_dict["type"] == read_dict["type"]
    dest_match = original_dict["destination"] == read_dict["destination"]
    amount_match = original_dict.get("amount") == read_dict.get("amount")
    attack_match = original_dict.get("attack") == read_dict.get("attack")
    hold_match = original_dict.get("hold") == read_dict.get("hold")
    decay_match = original_dict.get("decay") == read_dict.get("decay")
    
    print(f"{label}:")
    print(f"  Type match: {'✓' if type_match else '✗'}")
    print(f"  Destination match: {'✓' if dest_match else '✗'}")
    print(f"  Amount match: {'✓' if amount_match else '✗'}")
    print(f"  Attack match: {'✓' if attack_match else '✗'}")
    print(f"  Hold match: {'✓' if hold_match else '✗'}")
    print(f"  Decay match: {'✓' if decay_match else '✗'}")
    print(f"  Overall: {'✓ (PASS)' if all([type_match, dest_match, amount_match, attack_match, hold_match, decay_match]) else '✗ (FAIL)'}")
    print()

def create_basic_song_structure(project):
    """Create a basic phrase, chain, and song structure."""
    # Create a phrase with C1 notes every fourth beat
    phrase = M8Phrase()
    
    # Add steps at positions 0, 4, 8, 12
    for step_pos in [0, 4, 8, 12]:
        step = M8PhraseStep(
            note="C_1",  # C1 note
            velocity=0x6F,
            instrument=0x00  # Use instrument slot 00
        )
        phrase[step_pos] = step
    
    # Add the phrase to the project at index 00
    project.phrases[0x00] = phrase
    
    # Create a chain with transpose 10
    chain = M8Chain()
    chain_step = M8ChainStep(
        phrase=0x00,
        transpose=0x10
    )
    chain.add_step(chain_step)
    
    # Add the chain to the project at index 00
    project.chains[0x00] = chain
    
    # Add chain reference to song position (0,0)
    project.song[0][0] = 0x00

if __name__ == "__main__":
    create_and_test_303_project()