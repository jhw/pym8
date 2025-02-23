from m8 import NULL
from m8.api import M8ValidationError, M8IndexError
from m8.api.chains import M8Chain, M8ChainStep
from m8.api.instruments.macrosynth import M8MacroSynth
from m8.api.modulators import M8AHDEnvelope
from m8.api.phrases import M8Phrase, M8PhraseStep
from m8.api.project import M8Project
from m8.api.song import M8SongRow
from m8.enums.instruments import M8FilterTypes, M8AmpLimitTypes
from m8.enums.instruments.macrosynth import M8MacroSynthShapes

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
        shape=random.choice(list(M8MacroSynthShapes)),
        amp_limit=M8AmpLimitTypes.SIN,
        amp_level=0x40
    )
    
    # Add instrument to first slot
    project.add_instrument(macro_synth)
    
    # Create and configure first AHD envelope modulator
    ahd_mod1 = M8AHDEnvelope(
        destination=0x01,
        decay=0x40
    )
    macro_synth.set_modulator(ahd_mod1, slot=0)
    
    # Create and configure second AHD envelope modulator
    ahd_mod2 = M8AHDEnvelope(
        destination=0x07,
        amount=0xA0,
        decay=0x40  # Same decay as first modulator
    )
    macro_synth.set_modulator(ahd_mod2, slot=1)
    
    # Create a basic phrase with repeating notes
    phrase = M8Phrase()
    for i in range(4):
        step = M8PhraseStep(
            note=0x24,  # C-4
            velocity=0x6F,
            instrument=0  # Reference our macro synth in the first slot
        )
        phrase.set_step(step, i*4)
    
    # Add phrase to project
    phrase_idx = project.add_phrase(phrase)
    
    # Create a chain with our phrase
    chain = M8Chain()
    chain_step = M8ChainStep(
        phrase=phrase_idx,
        transpose=NULL
    )
    chain.add_step(chain_step)
    
    # Add chain to project and assign to first song position
    chain_idx = project.add_chain(chain)
    project.song[0][0] = chain_idx
    
    # Validate and save the project
    project.validate()
    os.makedirs('tmp', exist_ok=True)
    filename = f"tmp/{project.metadata.name.replace(' ', '')}.m8s"
    project.write_to_file(filename)
    
    print(f"Project successfully written to {filename}")
    
except (M8ValidationError, M8IndexError) as e:
    print(f"Project creation failed: {str(e)}")
