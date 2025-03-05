# short

- last commit introduced dual serialisation of filter/amp/mixer params

- filter/amp/mixer/amplifier offsets must be on a per instrument basis

# medium

- m8i files
- test suite

- wavsynth
- sampler
- fmsynth
- hypersynth

- sampler slice points

- toml file

# thoughts

- transpose/eq/pitch/fine_tune synth parameters?

# done

- auto instrument naming 
- check offset = None
- TEENSY
- enums
- macrosynth contains hardcoded offset
- not sure macrosynth params needs its current constructor
- refactor project offsets
- modulators, song, fx
- explicit offsets/ranges/indexes/counts/sizes
- check exceptions thrown
- fix duplication of synth params offsets ("19") (or "18" now)
- common params
- decrement instrument offsets
- cleanup
- capture and test working version
- create diffs of old (working) and new (broken) versions
- fix diffs as best you can 
- re- test
- test macro on teensy
- compare offsets with pre oxp-myb version 
- test macro on M8
- remaining modulators
- replace M8 index error with simple index error 
- change metadata defaults 
- add hex formatting via json decoder/encoder
- json helpers in m8/api/__init__.py
- modulators could be rationalised with structure similar to _param_defs in params
- remove FX_ prefix from fx global variables
- rationalise modulator enums
- why does second modulator have destination 3?
- hardcoded offsets
- move params into params.py
- abstract filter/amp/mixer params into instrument base
- why isn't fx "tuples" key showing in serialisation?
- fx (tuples) as list
- refactor song row as index
- modulators as list
- song row as list
- instruments as list
- chains as list
- phrases as list
- render version as string
- modulators to be independent of synth
- add back modulator index
- add back modulator empty (off)
- only render non- empty modulators
- see if macrosynth default parameter handling could be moved to instrument base helper function
- move instrument _write_parameters
- macrosynth to delegate handling of base params to base class via super()
- xxx_params base class
- move type/name/transpose/table_tick/volume/pitch to instrument base
- move shape/timbre/color/degrade/redux to (macro) synth params
- add mixer, amp, filter params
- collapse instrument/instrument params distinction
- type parameter being duplicated in instrument base and synth params
- remove modulator is_empty() code
- modulators not showing index
- off modulators not being filtered out
- type 3 lfo not being shown
- move utils/bits into api
- replace IndexError with M8IndexError
- move M8Block into m8/api/__init__.py
- rationalise imports
- chains multi- list indexation
- filled_indices refs
- fx indexation
- modulators indexation
- consider adding back filter/amp/mixer classes
- modulator abstraction into base classes
- remove __class__ checks in instruments and modulators
- remove checks for "__class__"
- liberate M8Modulators
- instruments not being serialised to json
- remove __class__
- remove api/serialisation
- examples and demo to use json.loads/dumps directly
- remove all json code in classes
- separate version from project
- separate metadata from project
- separate fx from phrases
- remove NULL and BLANK
- remove core package
- remove all tests
- move serialisation to api
- simplify serialisation
- complete project/version/metadata refactoring
- complete instruments, modulator refactoring
- remove set_caller_module
- remove local from/to_json imports
- add back last version of from_json and test
- run_profile.py doesn't need to save profile, or save it to tmp

```
(env) jhw@Justins-MacBook-Air pym8 % python dev/test_deserialisation.py tmp/PYMACRO.json
Found non-dict phrases in m8.api.project.M8Project: <class 'm8.api.project.M8Project'>
*** CIRCULAR REFERENCE DETECTED: phrases is an M8Project ***
Converted phrases back to a dictionary
```

- change hello_macrosynth to dump json
- delete tools/inspect_m8s.py
- auto_name_decorator
- include fx in hello macrosynth
- re- test
- include macrosynth enums in enums
- remove enums from core
- remove enums from core tests
- re- test
- manually remove enums from api field maps
- remove utils/enums and test
- remove tests/api
- support for list of enums
- remove custom as_dict
- remove enum and hex support in as_dict
- remove attribute checks in object getter/setter methods
- complete fx enums
- remove unnecessary attribute error checks
- import into laptop
- script to iterate fx
- create a template with all fx from one group in a single phrase
- instruments, modulators tests
- add_xxx to return slot position
- hello_macrosynth to use slot position returned by add_instrument
- to_dict to render hex codes
- does M8Object get_xxx really need format checking code?
- phrase note enum 
- extend MacroSynthModDestinations enum
- instrument types enum
- M8ModTypes enum
- macrosynth mod dest enums
- include mod dest enum ref in hello_macrosynth
- default modulators doesn't need to include instrument type
- modulators root to dynamically instantiate modulators
- modulator directory
- remove params
- investigate why synth_params_class check is required at macrosynth.py constructor level
- factory functions taking self.synth_params.type to instantiate modulators
- as_dict lenient enum handling
- add low pass filter to instrument 
- add second AHD modulator for filter cutoff 
- add instrument shape
- add instrument (amp) level and limit 
- add instrument chorus
- run hello macrosynth
- check inspect_m8s shows enum keys where applicable 
- include enum refs in instrument, modulator field map definitions
- /M8/enums/instruments/macrosynth/M8MacroSynthShapes
- /M8/enums/instruments/M8FilterTypes
- /M8/enums/instruments/M8AmpLimitTypes
- missing checks in object get/set int, compared to other types 
- add timestamp to prompt outputs
- refactor dump snapshot to iterate through a series of root directories
- m8/api/__init__.py
- move tools/dump_snapshot to tools/prompts/init_chat
- add core subdir to tests
- M8/API
- as_dict() to return enum keys if they exist
- field map abstractions
- refactor block_byte [object] and default [array] as default_byte
- remove passing of instrument type fields
- modulators beyond modulator 1 are messed up
- instrument pool is full of wavsynths (0x00)
- convert M8List to take default set of items
  - refactor modulator initialisation code
- refactor M8List to write to fixed blocks
- initialise instruments with set of modulators
- modulator default values (screenshot)

```
(env) jhw@Justins-MacBook-Air pym8 % python tools/inspect_m8s.py templates/M8MACRO.m8s
Error reading M8 project file: name 'M8ADSRLFO' is not defined
```

- note is E-6 (transpose?)
- clean out volumes / M8
- create default 401 and m8macro and export to laptop
- inspect m8macro with focus on modulators and FX 
- create pymacro and compare with m8macro, with same focus 
- move pymacro to M8 and see if it will load / render 
- enhanced song api
- refactor project test to use simplified api
- phrase/chain step apis
- project add/set instrument
- project add/set phrase
- project add/set chain
- refactor examples to use simplified api
- instrument add/set modulator
- phrase add/set fx
- M8IndexError
- notes on enums
- LFO >> 7 bytes including type_dest?
- create project test from demos
- fx enum
- include fx enum in write script
- validation to include empty check?
- abstraction of macrosynth from instruments >> eliminate TYPE?
- failing list test
- array to validate read() size
- check size validation works in object read()
- remove list DEFAULT_DATA
- remove superflous m8 is_empty() methods
- object.is_empty()
- snapshot generator to ask about core/m8/tests/demos
- list test
- utils/bits tests
- NULL (0x00) and BLANK (0xFF)
- github repo
- update dump_snapshot for new files
- move validation error to project
- move M8 block to root
- move bitwise stuff to utils
- setup.py
- single test script

