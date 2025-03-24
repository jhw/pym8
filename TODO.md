# short

- check uppercase forcing wrt instrumnet/modulator names

- add constructor enum support to fx
- add fx enums
- check fx is_empty()
- add constructor enum support to phrases
- add phrase note enum
- check phrase is_empty()

# medium

- fx example
- TODO.md >> github project
- 5.0.2 test

- sampler slices
- fmsynth
- hypersynth
- tables

# beats

- revoke chains model in favour of phrases only
- replace concat_phrases with m8/tools version
- check reverb_send, chorus_send refs

# roadmap

- eq
- midi
- grooves
- scales

# thoughts

- get rid of enums?
  - tempting but they are likely useful
- screenshot >>> textract?
  - not precise enough and not worth automating

# done

✓ add default: 0 as third default for YAML fields
✓ default size/type defaults for YAML fields (size: 1, type: "UINT8")
✓ abstract bit utils, json utils
✓ implement proper modulator is_empty() definition using configuration
✓ implement proper is_empty() definition and re-enable is_empty tests
✓ add tools for future Claude string substitution tasks
- api bug
- standardize instrument/modulator enum strings to use uppercase consistently
  - update format_config.yaml to use uppercase keys for instrument and modulator types
  - added case-insensitive lookup for backward compatibility
  - all config accessors now handle both uppercase and lowercase
  - updated all tests to use uppercase enum strings consistently
  - temporarily commented out inconsistent is_empty tests
- do enum helpers support a list but also a dict with list values?
- references to "manual" in modulator testing?
- abstraction of helper support to utils to simplify modulator testing
- add constructor enum supoort to modulator
- add mod destination enums
- M8Params >> M8InstrumentParams
- wavsynth shapes
- macrosynth shapes
- sampler play modes
- filter types
- limit types
- constructor support for enum field string values
- int values not found in enums to raise exceptions
- clean up project initialise file paths
- does project.toml include templates
- version checking
- add back version and log
- instrument type classes should have M8 prefix 
- song counts should be in config 
- remove custom IndexError (not needed/used)
- instrument common synthesiser params should be part of config
- instrument read_from_file and write_to_file
- config refactoring
  - modulators section (fields, constants)
  - metadata section (fields)
  - phrases section (fields)
  - chains section (fields)
  - fx section (fields, constants)
- harmonise modulators offset
- remove redundant sample_path_offset in config
- create dump_sampler_m8i script
- avoid sample path duplication
- load m8i and print from project modulator offset
- adapt to print modulators from modulator offset
- remove version
- don't write to var
- bake_chains handling of blanks
- bake_chains script
- remove typing
- concat_phrases script
- validation of flat structures [notes]
- check if project read/write is tested
- refactor modulators as per instruments
- move instruments
- song/chain/phrase example
- sampler example
- macrosynth example
- string handling code smell
- add instrument name
- m8s >> dict test suite
- instrument inspector
- json bitmap
- add back wavsynth param hardcoding
- propose a solution for removing synth param hardcoding
- abstract offsets, counts, sizes to YAML configuration
- remove hardcoded constants in favor of configuration
- instrument, modulator tests
- project tests
- remove defaults and backwards compatibility
- clean up commenting
- CLAUDE.md

