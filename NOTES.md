### pico waveforms 08/03/25

```
(env) jhw@Justins-Air pym8 % ls /Volumes/M8/Samples/woldo/waveforms/erica\ pico 
ERICA PICO 01.wav	ERICA PICO 09.wav	ERICA PICO 17.wav	ERICA PICO 25.wav
ERICA PICO 02.wav	ERICA PICO 10.wav	ERICA PICO 18.wav	ERICA PICO 26.wav
ERICA PICO 03.wav	ERICA PICO 11.wav	ERICA PICO 19.wav	ERICA PICO 27.wav
ERICA PICO 04.wav	ERICA PICO 12.wav	ERICA PICO 20.wav	ERICA PICO 28.wav
ERICA PICO 05.wav	ERICA PICO 13.wav	ERICA PICO 21.wav	ERICA PICO 29.wav
ERICA PICO 06.wav	ERICA PICO 14.wav	ERICA PICO 22.wav	ERICA PICO 30.wav
ERICA PICO 07.wav	ERICA PICO 15.wav	ERICA PICO 23.wav	ERICA PICO 31.wav
ERICA PICO 08.wav	ERICA PICO 16.wav	ERICA PICO 24.wav	ERICA PICO 32.wav
```

### wavsynth 04/03/25

- synth params
- synth
- shapes enum
- destinations enum
- instrument FX enum
- convert hello macro to pydemo, creating both macro and wav 

### working macrosynth 03/03/25

git checkout 76008cc97879424a028a6dd78cfef28326300cdc

### class names 27/02/25

If def set_caller_module_decorator is not enabled we get the following -

```
  "phrases": {
    "__class__": "m8.api.phrases.M8Phrases",
    "items": [
      {
        "__class__": "m8.api.phrases.M8Phrase",
        "steps": [
          {
            "__class__": "m8.api.phrases.M8PhraseStep",
            "note": 36,
            "velocity": 111,
            "instrument": 0,
            "fx": [
              {
                "__class__": "m8.core.object.M8FXTuple",
                "key": 144,
                "value": 64
              }
            ]
          },
```

Paths for objects nested at leaf level are incorrect

If it is enabled, we get the following -

```
  "phrases": {
    "__class__": "m8.api.phrases.M8Phrases",
    "items": [
      {
        "__class__": "m8.api.phrases.M8Phrase",
        "steps": [
          {
            "__class__": "m8.api.phrases.M8PhraseStep",
            "note": 36,
            "velocity": 111,
            "instrument": 0,
            "fx": [
              {
                "__class__": "m8.api.phrases.cls",
                "key": 144,
                "value": 192
              }
            ]
          },
```

So now the leaf paths are correct but the class name is listed as cls!

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
