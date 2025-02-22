# short

- refactor block_byte [object] and default [array] as default_byte

# pymacro

- remove fx
- LP filter envelope
- amp and limit
- chorus

# medium

- instrument id field to reflect position in list
- transpose/eq/pitch/fine_tune
- enums

# thoughts

- song/chain/phrase/instrument api which hides idx?
- abstract modulators as per instruments?
  - probably not worth it

# done

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

