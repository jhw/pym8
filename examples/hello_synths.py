# hello_world.py
from m8.api.project import M8Project
from m8.api.chains import M8Chain, M8ChainStep
from m8.api.phrases import M8Phrase, M8PhraseStep
from m8.api.instruments.wavsynth import M8WavSynth
from m8.api.instruments.macrosynth import M8MacroSynth
from m8.enums.phrases import M8Notes

# Create a new project
project = M8Project()

# Set project metadata
project.metadata.name = "PYSYNTHS"
project.metadata.tempo = 120.0

# Create a WavSynth instrument
wavsynth = M8WavSynth(
    synth_shape=0x06,  # SINE
    synth_size=0x80,
    synth_mult=0x80,
    synth_warp=0x0,
    synth_scan=0x0,
    filter_type=0x01,  # LOWPASS
    filter_cutoff=0xC0,
    filter_resonance=0x40,
    amp_level=0xC0,
    mixer_pan=0x80,  # Center
    mixer_dry=0xC0,
    mixer_reverb=0x40,
)

# Create a MacroSynth instrument
macrosynth = M8MacroSynth(
    synth_shape=0x06,  # SINE_TRIANGLE
    synth_timbre=0x80,
    synth_color=0x80,
    synth_degrade=0x0,
    synth_redux=0x0,
    filter_type=0x01,  # LOWPASS
    filter_cutoff=0xC0,
    filter_resonance=0x40,
    amp_level=0xC0,
    mixer_pan=0x80,  # Center
    mixer_dry=0xC0,
    mixer_reverb=0x40,
)

# Add instruments to the project
wavsynth_slot = project.add_instrument(wavsynth)
macrosynth_slot = project.add_instrument(macrosynth)

# Create a phrase with alternating instruments
phrase = M8Phrase()

# Add a pattern of notes alternating between instruments
notes = [
    M8Notes.C_4, M8Notes.E_4, M8Notes.G_4, M8Notes.C_5,
    M8Notes.C_4, M8Notes.E_4, M8Notes.G_4, M8Notes.C_5
]

# Add notes to the phrase, alternating between instruments
for i, note in enumerate(notes):
    step = M8PhraseStep(
        note=note,
        velocity=0xC0,
        # Use WavSynth for first 4 notes, MacroSynth for last 4
        instrument=wavsynth_slot if i < 4 else macrosynth_slot
    )
    phrase.set_step(step, i)

# Add the phrase to the project
phrase_slot = project.add_phrase(phrase)

# Create a chain that plays our phrase
chain = M8Chain()
chain_step = M8ChainStep(phrase=phrase_slot, transpose=0)
chain.set_step(chain_step, 0)

# Add the chain to the project
chain_slot = project.add_chain(chain)

# Add the chain to the song at position 0,0
project.song.steps[0][0] = chain_slot

# Save the project
os.makedirs('tmp', exist_ok=True)
project.write_to_file("tmp/PYSYNTHS.m8s")
