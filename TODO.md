# short [01-remove-enums]

- include fx in hello macrosynth
- re- test

# medium

- simple json serialisation
- simple json deserialisation
- json hex rendering
- json enum rendering (how?)

- m8i files
- add back as_dict(), as_list() tests
- custom modulator is_empty() method
- toml file
- api tests

# thoughts

- are modulator fx instrument specific or generic?
- inheritance pattern for instruments?
- refactor macrosynth as macro_synth?
- NULL vs BLANK?
- transpose/eq/pitch/fine_tune synth parameters

# rejected

- instrument idx field
- song/chain/phrase/instrument api which hides idx

# done

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

