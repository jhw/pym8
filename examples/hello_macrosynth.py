from m8.api import M8ValidationError
from m8.api.chains import M8Chain, M8ChainStep
from m8.api.instruments.macrosynth import M8MacroSynth
from m8.api.modulators import M8AHDEnvelope
from m8.api.phrases import M8Phrase, M8PhraseStep
from m8.api.project import M8Project
from m8.api.song import M8SongRow
from m8.enums.instruments import M8FilterTypes, M8AmpLimitTypes
from m8.enums.instruments.macrosynth import M8MacroSynthShapes, M8MacroSynthModDestinations
from m8.enums.phrases import M8Notes
from m8.enums.phrases.macrosynth import M8MacroSynthFX

import os
import random

try:
    # Load the base project template
    project = M8Project.read_from_file("templates/DEFAULT401.m8s")
    
    # Configure project metadata
    project.metadata.directory = "/Songs/woldo/"
    project.metadata.name = "PYMACRO"
    
    # Create and configure macro synth instrument
    macro_synth = M8MacroSynth(
        mixer_delay=0xC0,
        mixer_chorus=0xC0,
        mixer_reverb=0x40,
        filter_type=M8FilterTypes.LOWPASS,
        filter_cutoff=0x20,
        filter_resonance=0xC0,
        shape=0x00,
        amp_limit=M8AmpLimitTypes.SIN,
        amp_level=0x40
    )
    
    # Add instrument to project and store the returned index
    instrument_idx = project.add_instrument(macro_synth)
    
    # Create and configure first AHD envelope modulator
    ahd_mod1 = M8AHDEnvelope(  # Using generic class
        destination=M8MacroSynthModDestinations.VOLUME,
        decay=0x40
    )
    macro_synth.set_modulator(ahd_mod1, slot=0)
    
    # Create and configure second AHD envelope modulator
    ahd_mod2 = M8AHDEnvelope(  # Using generic class
        destination=M8MacroSynthModDestinations.FILTER_CUTOFF,
        amount=0x80,
        decay=0x40  # Same decay as first modulator
    )
    macro_synth.set_modulator(ahd_mod2, slot=1)
    
    # Create a basic phrase with repeating notes
    phrase = M8Phrase()
    
    # Possible SDL FX values
    sdl_values = [0x00, 0x40, 0x80, 0xC0]
    
    for i in range(4):
        # Create a step with a note, velocity, and instrument
        step = M8PhraseStep(
            note=M8Notes.C_4,
            velocity=0x6F,
            instrument=instrument_idx  # Use the stored instrument index
        )
        
        # Add an SDL (delay) FX to the step with a random value
        # SDL is defined in M8MacroSynthFX enum
        sdl_value = random.choice(sdl_values)
        step.add_fx(M8MacroSynthFX.SDL, sdl_value)
        
        # Add the step to the phrase at position i*4
        phrase.set_step(step, i*4)
    
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
    os.makedirs('tmp', exist_ok=True)
    filename = f"tmp/{project.metadata.name.replace(' ', '')}"
    project.write_to_file(f"{filename}.m8s")
    project.write_to_json_file(f"{filename}.json")
    
except M8ValidationError as e:
    print(f"Project creation failed: {str(e)}")
