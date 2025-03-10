from m8.api import M8ValidationError
from m8.api.chains import M8Chain, M8ChainStep
from m8.api.instruments.macrosynth import M8MacroSynth
from m8.api.instruments.wavsynth import M8WavSynth
from m8.api.instruments.sampler import M8Sampler
from m8.api.modulators import M8AHDEnvelope
from m8.api.phrases import M8Phrase, M8PhraseStep
from m8.api.project import M8Project
from m8.api.song import M8SongRow
from m8.enums import M8FilterTypes, M8LimitTypes, M8Notes
from m8.enums.macrosynth import M8MacroSynthShapes, M8MacroSynthModDestinations,  M8MacroSynthFX
from m8.enums.wavsynth import M8WavSynthModDestinations, M8WavSynthFX
from m8.enums.sampler import M8SamplerPlayMode, M8SamplerModDestinations, M8SamplerFX

import os
import random

try:
    # Load the base project template
    project = M8Project.read_from_file("m8/templates/DEFAULT401.m8s")
    
    # Create the project from the template
    
    # Configure project metadata
    project.metadata.directory = "/Songs/woldo/"
    project.metadata.name = "PYSYNTHS"
    
    # Create instruments for our project
    
    # Create and configure macro synth instrument
    macro_synth = M8MacroSynth(
        delay=0xC0,
        chorus=0xC0,
        reverb=0x40,
        filter=M8FilterTypes.LOWPASS,
        cutoff=0x20,
        res=0xC0,  # renamed from resonance
        shape=M8MacroSynthShapes.BUZZ,
        limit=M8LimitTypes.SIN,
        amp=0x40
    )
    
    # Add MacroSynth to project and store the returned index
    macro_idx = project.add_instrument(macro_synth)
    
    # Use the returned index for MacroSynth
    
    # Create and configure modulators for MacroSynth
    ahd_mod1 = M8AHDEnvelope(
        destination=M8MacroSynthModDestinations.VOLUME,
        decay=0x40
    )
    macro_synth.set_modulator(ahd_mod1, slot=0)
    
    ahd_mod2 = M8AHDEnvelope(
        destination=M8MacroSynthModDestinations.CUTOFF,  # Keep original destination (0x07)
        amount=0x80,
        decay=0x40
    )
    macro_synth.set_modulator(ahd_mod2, slot=1)
    
    # Create and configure wavsynth instrument with the same filter/amp/mixer params as macro
    wav_synth = M8WavSynth(
        delay=0xC0,
        chorus=0xC0,
        reverb=0x40,
        filter=M8FilterTypes.LOWPASS,
        cutoff=0x20,
        res=0xC0,  # renamed from resonance
        limit=M8LimitTypes.SIN,
        amp=0x40,
        # WavSynth specific params all at 0x00 except size
        shape=0x00,
        size=0x20,
        mult=0x00,
        warp=0x00,
        scan=0x00
    )
    
    # Add WavSynth to project and store the index
    wav_idx = project.add_instrument(wav_synth)
    
    # Use the returned index for WavSynth
    
    # Create and configure modulators for WavSynth - identical to MacroSynth
    wav_mod1 = M8AHDEnvelope(
        destination=M8WavSynthModDestinations.VOLUME,
        decay=0x40
    )
    wav_synth.set_modulator(wav_mod1, slot=0)
    
    wav_mod2 = M8AHDEnvelope(
        destination=M8WavSynthModDestinations.CUTOFF,  # Keep original destination (0x07)
        amount=0x80,
        decay=0x40
    )
    wav_synth.set_modulator(wav_mod2, slot=1)
    
    # Create and configure a sampler instrument with the same filter/amp/mixer params
    sample_num = random.randint(1, 32)
    sample_path = f"/Samples/woldo/waveforms/erica pico/ERICA PICO {sample_num:02d}.wav"
    
    sampler = M8Sampler(
        delay=0xC0,
        chorus=0xC0,
        reverb=0x40,
        filter=M8FilterTypes.LOWPASS,
        cutoff=0x20,
        res=0xC0,  # renamed from resonance
        limit=M8LimitTypes.SIN,
        amp=0x40,
        # Sampler specific params
        play_mode=M8SamplerPlayMode.FWD,
        slice=0x00,
        start=0x00,
        loop_start=0x00,
        length=0xFF,
        degrade=0x00,
        sample_path=sample_path
    )
    
    # Add Sampler to project and store the index
    sampler_idx = project.add_instrument(sampler)
    
    # Create and configure modulators for Sampler - identical to the other synths
    sampler_mod1 = M8AHDEnvelope(
        destination=M8SamplerModDestinations.VOLUME,
        decay=0x40
    )
    sampler.set_modulator(sampler_mod1, slot=0)
    
    sampler_mod2 = M8AHDEnvelope(
        destination=M8SamplerModDestinations.CUTOFF,
        amount=0x80,
        decay=0x40
    )
    sampler.set_modulator(sampler_mod2, slot=1)
    
    # Create a phrase with alternating notes from the three instruments
    phrase = M8Phrase()
    
    # Possible effect values
    fx_values = [0x40, 0x80, 0xC0]
    
    # Create 16 steps with rotating instruments (macro, wav, sampler)
    for i in range(16):
        # Determine which instrument to use (rotate between macro, wav, and sampler)
        if i % 3 == 0:
            instr_idx = macro_idx
        elif i % 3 == 1:
            instr_idx = wav_idx
        else:
            instr_idx = sampler_idx
        
        # Alternate between C4, E4, and G4
        note = M8Notes.C_4 if i % 3 == 0 else (M8Notes.E_4 if i % 3 == 1 else M8Notes.G_4)
        
        # Create a step with the note, velocity, and instrument
        step = M8PhraseStep(
            note=note,
            velocity=0x6F,
            instrument=instr_idx
        )
        
        # Add SDL (delay) effect based on instrument type
        fx_value = random.choice(fx_values)
        
        if instr_idx == macro_idx:
            # For MacroSynth, add SDL (delay) effect
            step.add_fx(M8MacroSynthFX.SDL, fx_value)
        elif instr_idx == wav_idx:
            # For WavSynth, add SDL (delay) effect
            step.add_fx(M8WavSynthFX.SDL, fx_value)
        else:
            # For Sampler, add SDL (delay) effect
            step.add_fx(M8SamplerFX.SDL, fx_value)
        
        # Add the step to the phrase at position i
        # (limited to positions 0-15 as there are only 16 steps in a phrase)
        phrase.set_step(step, i)
    
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
    
    # Verify instruments were reloaded with correct types
    print(f"Reloaded instruments: MacroSynth (type={reload_project.instruments[macro_idx].type}), "
          f"WavSynth (type={reload_project.instruments[wav_idx].type}), "
          f"Sampler (type={reload_project.instruments[sampler_idx].type})")
    
except M8ValidationError as e:
    print(f"Project creation failed: {str(e)}")
