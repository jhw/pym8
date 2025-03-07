from m8.api import M8ValidationError
from m8.api.chains import M8Chain, M8ChainStep
from m8.api.instruments.macrosynth import M8MacroSynth
from m8.api.instruments.wavsynth import M8WavSynth
from m8.api.modulators import M8AHDEnvelope
from m8.api.phrases import M8Phrase, M8PhraseStep
from m8.api.project import M8Project
from m8.api.song import M8SongRow
from m8.enums.instruments import M8FilterTypes, M8AmpLimitTypes
from m8.enums.instruments.macrosynth import M8MacroSynthShapes, M8MacroSynthModDestinations
from m8.enums.instruments.wavsynth import M8WavSynthModDestinations
from m8.enums.phrases import M8Notes
from m8.enums.phrases.macrosynth import M8MacroSynthFX
from m8.enums.phrases.wavsynth import M8WavSynthFX

import os
import random

try:
    # Load the base project template
    project = M8Project.read_from_file("templates/DEFAULT401.m8s")
    
    # Configure project metadata
    project.metadata.directory = "/Songs/woldo/"
    project.metadata.name = "PYSYNTHS"
    
    # Create and configure macro synth instrument
    macro_synth = M8MacroSynth(
        name="MACRO01",
        mixer_delay=0xC0,
        mixer_chorus=0xC0,
        mixer_reverb=0x40,
        filter_type=M8FilterTypes.LOWPASS,
        filter_cutoff=0x20,
        filter_resonance=0xC0,
        shape=M8MacroSynthShapes.BUZZ,
        amp_limit=M8AmpLimitTypes.SIN,
        amp_level=0x40
    )
    
    # Add MacroSynth to project and store the returned index
    macro_idx = project.add_instrument(macro_synth)
    
    # Create and configure modulators for MacroSynth
    ahd_mod1 = M8AHDEnvelope(
        destination=M8MacroSynthModDestinations.VOLUME,
        decay=0x40
    )
    macro_synth.set_modulator(ahd_mod1, slot=0)
    
    ahd_mod2 = M8AHDEnvelope(
        destination=M8MacroSynthModDestinations.FILTER_CUTOFF,
        amount=0x80,
        decay=0x40
    )
    macro_synth.set_modulator(ahd_mod2, slot=1)
    
    # Create and configure wavsynth instrument with the same filter/amp/mixer params as macro
    wav_synth = M8WavSynth(
        name="WAVSYN01",
        mixer_delay=0xC0,
        mixer_chorus=0xC0,
        mixer_reverb=0x40,
        filter_type=M8FilterTypes.LOWPASS,
        filter_cutoff=0x20,
        filter_resonance=0xC0,
        amp_limit=M8AmpLimitTypes.SIN,
        amp_level=0x40,
        # WavSynth specific params all at 0x00 except size
        waveform=0x00,
        size=0x20,
        mult=0x00,
        warp=0x00,
        mirror=0x00
    )
    
    # Add WavSynth to project and store the index
    wav_idx = project.add_instrument(wav_synth)
    
    # Create and configure modulators for WavSynth - identical to MacroSynth
    wav_mod1 = M8AHDEnvelope(
        destination=M8WavSynthModDestinations.VOLUME,
        decay=0x40
    )
    wav_synth.set_modulator(wav_mod1, slot=0)
    
    wav_mod2 = M8AHDEnvelope(
        destination=M8WavSynthModDestinations.FILTER_CUTOFF,
        amount=0x80,
        decay=0x40
    )
    wav_synth.set_modulator(wav_mod2, slot=1)
    
    # Create a phrase with alternating notes from both instruments
    phrase = M8Phrase()
    
    # Possible effect values
    fx_values = [0x40, 0x80, 0xC0]
    
    # Create 8 steps with alternating instruments
    for i in range(8):
        # Determine which instrument to use (alternate between macro and wav)
        instr_idx = macro_idx if i % 2 == 0 else wav_idx
        
        # Alternate between C4 and E4
        note = M8Notes.C_4 if i % 4 < 2 else M8Notes.E_4
        
        # Create a step with the note, velocity, and instrument
        step = M8PhraseStep(
            note=note,
            velocity=0x6F,
            instrument=instr_idx
        )
        
        # Add SDL (delay) effect to all steps regardless of instrument
        fx_value = random.choice(fx_values)
        
        if instr_idx == macro_idx:
            # For MacroSynth, add SDL (delay) effect
            step.add_fx(M8MacroSynthFX.SDL, fx_value)
        else:
            # For WavSynth, also add SDL (delay) effect
            step.add_fx(M8WavSynthFX.SDL, fx_value)
        
        # Add the step to the phrase at position i*2
        phrase.set_step(step, i*2)
    
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
    
    print(f"Successfully created project: {filename}")
    
except M8ValidationError as e:
    print(f"Project creation failed: {str(e)}")
