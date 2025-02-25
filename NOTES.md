### m8i files and JSON serialisation 25/02/25

- you might want to load trash80's synth drums and create patterns with thos
- for this you would need to load m8i files
- but you might also want to serialise those instruments to json / deserialise from json
- in the interests of transparency and of instrument modification

---

- this all starts with as_dict/as_list
- but you need to roll back enum and hex support into a new json layer which implements then as part of JSON encoders/decoders
- this layer will also need the ability to create classes from json
- and for that to work you probably need factory functions embedded in the relevat api classes

---

- roll back as_dict hex and enum support
- roll back array as_list indexation support
- check as_dict/as_list code still works but is as generic as possible
- consider renaming read as read_m8s
- new JSON serialisation layer with encoders and decoders
- factory deserialisation functions for all api classes
- convert hello macrosynth to print json

---

- extend instrument with read_m8i functions
- extend instrument with read/write_json functions

### macrosynth enums 22/02/25

- /M8/enums/instruments/macrosynth/M8MacroSynthShapes
- /M8/enums/instruments/M8FilterTypes
- /M8/enums/instruments/M8AmpLimitTypes
- /M8/enums/instruments/macrosynth/M8MacroSynthModDestinations

---

- implement above enums in M8/enums 
- include enum refs in instrument, modulator field map definitions
- refactor volume to use mod destination enum
- add low pass filter to instrument 
- add second AHD modulator for filter cutoff 
- add instrument shape
- add instrument (amp) level and limit 
- add instrument chorus
- run hello macrosynth
- check inspect_m8s shows enum keys where applicable 

### m8macro.m8s 21/02/25

```
Instrument 0: {'synth': {'type': 1, 'name': '', 'transpose': 4, 'eq': 1, 'table_tick': 1, 'volume': 0, 'pitch': 0, 'fine_tune': 128, 'shape': 0, 'timbre': 128, 'color': 128, 'degrade': 0, 'redux': 0, 'filter_type': 1, 'filter_cutoff': 48, 'filter_resonance': 160, 'amp_level': 0, 'amp_limit': 0, 'mixer_pan': 128, 'mixer_dry': 192, 'mixer_chorus': 192, 'mixer_delay': 128, 'mixer_reverb': 128}, 'modulators': [{'type': 0, 'destination': 1, 'amount': 255, 'attack': 0, 'hold': 0, 'decay': 96}, {'type': 0, 'destination': 7, 'amount': 159, 'attack': 0, 'hold': 0, 'decay': 64}]}
```

### whither enums? 21/02/25

- include enums or not?
- tried a couple of ways and neither seem ideal
- maybe enums are just syntactic sugar for the m8 interface
- as no- one can remember the underlying ints
- but the sugar format is dictated by the constraints of the interface
- if you didn't have that, maybe the api would look different?
