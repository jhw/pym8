import os
from m8 import M8ValidationError, M8IndexError, NULL
from m8.project import M8Project
from m8.instruments.macrosynth import M8MacroSynth
from m8.modulators import M8AHDEnvelope
from m8.phrases import M8Phrase, M8PhraseStep
from m8.chains import M8Chain, M8ChainStep
from m8.song import M8SongRow

try:
    # Load the project
    project = M8Project.read_from_file("templates/DEFAULT401.m8s")
    
    # Set project metadata
    project.metadata.directory = "/Songs/woldo/"
    project.metadata.name = "PYMACRO"
    
    # Create and assign macro synth to first slot
    macro_synth = M8MacroSynth(
        mixer_delay = 0xC0
    )
    project.add_instrument(macro_synth)
    
    # Create and configure AHD envelope modulator with kwargs
    ahd_mod = M8AHDEnvelope(
        destination=0x01,
        decay=0x40
    )
    macro_synth.add_modulator(ahd_mod)
    
    # Create phrase
    phrase = M8Phrase()
    
    # Create steps with note properties and FX command
    for i in range(4):
        step = M8PhraseStep(
            note=0x40,
            velocity=0x40,
            instrument=0  # Set to use the first instrument (our macro synth)
        )
        
        # Add delay volume FX to the step using our new API
        step.add_fx(key=0x2B, value=0x80)  # volume delay
        phrase.set_step(step, i*4)
    
    # Add phrase to project and get its index
    phrase_idx = project.add_phrase(phrase)
    
    # Create chain 
    chain = M8Chain()
    
    # Create chain step and add it to the chain using the new method
    chain_step = M8ChainStep(
        phrase=phrase_idx,  # Use the phrase we created above
        transpose=NULL
    )
    chain.add_step(chain_step)
    
    # Add chain to project and get its index
    chain_idx = project.add_chain(chain)
    
    # Set the first element of the first row in the song to our chain
    project.song[0][0] = chain_idx  # Use the chain we created
    
    # Validate project before saving
    project.validate()
    
    # Save project
    os.makedirs('tmp', exist_ok=True)
    filename = f"tmp/{project.metadata.name.replace(' ', '')}.m8s"
    project.write_to_file(filename)
    
    print(f"Project written to {filename}")
    
except (M8ValidationError, M8IndexError) as e:
    print(f"Project creation failed: {str(e)}")
