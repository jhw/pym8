from m8.api import M8ValidationError
from m8.api.chains import M8Chain, M8ChainStep
from m8.api.instruments.sampler import M8Sampler
from m8.api.modulators import M8AHDEnvelope
from m8.api.phrases import M8Phrase, M8PhraseStep
from m8.api.project import M8Project
from m8.api.song import M8SongRow
from m8.enums.instruments import M8FilterTypes, M8LimitTypes
from m8.enums.instruments.sampler import M8SamplerPlayMode, M8SamplerModDestinations
from m8.enums.phrases import M8Notes
from m8.enums.phrases.sampler import M8SamplerFX

import os
import random

try:
    # Load the base project template
    project = M8Project.read_from_file("templates/DEFAULT401.m8s")
    
    # Configure project metadata
    project.metadata.directory = "/Songs/woldo/"
    project.metadata.name = "PYSAMPLER"
    
    # Create and configure a sampler instrument with custom parameters
    sample_num = random.randint(1, 32)
    sample_path = f"/Samples/woldo/waveforms/erica pico/ERICA PICO {sample_num:02d}.wav"
    
    sampler = M8Sampler(
        # Play mode set to Forward/Ping-Pong (0x04) as requested
        play_mode=M8SamplerPlayMode.FWD_PP,
        # Slice parameter set to 0x03 as requested
        slice=0x03,
        start=0x00,
        loop_start=0x00,
        length=0xFF,
        degrade=0x00,
        # Filter parameters
        filter=M8FilterTypes.LOWPASS,
        cutoff=0x20,
        res=0xC0,
        # Amp parameters
        amp=0x40,
        limit=M8LimitTypes.SIN,
        # Mixer parameters
        pan=0x80,
        dry=0xC0,
        chorus=0xC0,
        delay=0xC0,
        reverb=0x40,
        # Sample path
        sample_path=sample_path
    )
    
    # Add Sampler to project and store the index
    sampler_idx = project.add_instrument(sampler)
    
    # Create and configure modulators for Sampler
    volume_mod = M8AHDEnvelope(
        destination=M8SamplerModDestinations.VOLUME,
        decay=0x40
    )
    sampler.set_modulator(volume_mod, slot=0)
    
    cutoff_mod = M8AHDEnvelope(
        destination=M8SamplerModDestinations.CUTOFF,
        amount=0x80,
        decay=0x40
    )
    sampler.set_modulator(cutoff_mod, slot=1)
    
    # Create a phrase with a single note using the sampler
    phrase = M8Phrase()
    
    # Create a step with a C4 note
    step = M8PhraseStep(
        note=M8Notes.C_4,
        velocity=0x6F,
        instrument=sampler_idx
    )
    
    # Add a delay effect to the step
    step.add_fx(M8SamplerFX.SDL, 0x80)
    
    # Add the step to the phrase at position 0
    phrase.set_step(step, 0)
    
    # Add phrase to project
    phrase_idx = project.add_phrase(phrase)
    
    # Create a chain with our phrase
    chain = M8Chain()
    chain_step = M8ChainStep(
        phrase=phrase_idx,
        transpose=0x0
    )
    chain.add_step(chain_step)
    
    # Add chain to project and assign to first song position
    chain_idx = project.add_chain(chain)
    project.song[0][0] = chain_idx
    
    # Validate and save the project
    project.validate()
    
    # Write the project to a file
    os.makedirs('tmp', exist_ok=True)
    filename = f"tmp/{project.metadata.name.replace(' ', '')}"
    project.write_to_file(f"{filename}.m8s")
    project.write_to_json_file(f"{filename}.json")
    
    # Successfully created project
    print(f"Successfully created project: {filename}")
    
    # Read the project back and check instrument types
    reload_project = M8Project.read_from_file(f"{filename}.m8s")
    
    # Verify the instrument was reloaded with correct type
    print(f"Reloaded instrument: Sampler (type={reload_project.instruments[sampler_idx].type})")
    print(f"Play mode: {reload_project.instruments[sampler_idx].synth.play_mode}")
    print(f"Slice: {reload_project.instruments[sampler_idx].synth.slice}")
    
except M8ValidationError as e:
    print(f"Project creation failed: {str(e)}")
