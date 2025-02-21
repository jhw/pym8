import os
from m8 import M8ValidationError, NULL
from m8.project import M8Project
from m8.instruments.macrosynth import M8MacroSynth
from m8.modulators import M8AHDEnvelope
from m8.phrases import M8Phrase, M8PhraseStep, M8FXTuples, M8FXTuple
from m8.chains import M8Chain, M8ChainStep
from m8.song import M8SongRow

try:
    # Load the project
    project = M8Project.read_from_file("templates/DEFAULT-4-0-1.m8s")
    
    # Set project metadata
    project.metadata.directory = "/Songs/woldo/"
    project.metadata.name = "HELLO_MACRO"
    
    # Create and assign macro synth to first slot
    macro_synth = M8MacroSynth(
        mixer_delay = 0xC0
    )
    project.instruments[0] = macro_synth
    
    # Create and configure AHD envelope modulator with kwargs
    ahd_mod = M8AHDEnvelope(
        destination=0x01,
        decay=0x40
    )
    macro_synth.modulators[0] = ahd_mod
    
    # Create phrase and configure first step with kwargs
    phrase = M8Phrase()
    
    # Create a step with note properties and FX command
    for i in range(4):
        step = M8PhraseStep(
            note=0x40,
            velocity=0x40,
            instrument=0  # Set to use the first instrument (our macro synth)
        )
        
        # Add delay volume FX to the step
        # We'll use the first FX slot for this
        delay_fx = M8FXTuple(key=0x2B, value=0x80)  # volume delay?
        step.fx[0] = delay_fx
        
        # Assign step to every 4th position
        phrase[i*4] = step
        
    # Assign phrase to first slot
    project.phrases[0] = phrase
    
    # Create chain and set first step to use phrase 0
    chain = M8Chain()
    chain_step = M8ChainStep(
        phrase=0,  # Use the phrase we created above (index 0)
        transpose=NULL
    )
    chain[0] = chain_step
    
    # Assign chain to first slot
    project.chains[0] = chain
    
    # Set the first element of the first row in the song to chain 0
    project.song[0][0] = 0  # Use the chain we created (index 0)
    
    # Validate project before saving
    project.validate()
    
    # Save project
    os.makedirs('tmp', exist_ok=True)
    filename = f"tmp/{project.metadata.name.replace(' ', '')}.m8s"
    project.write_to_file(filename)
    
    print(f"Project written to {filename}")
    
except M8ValidationError as e:
    print(f"Project validation failed: {str(e)}")
